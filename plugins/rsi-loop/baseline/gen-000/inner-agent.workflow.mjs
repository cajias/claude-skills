export const meta = {
  name: 'aide0-inner-agent',
  description: 'AIDE0 baseline tree-search inner agent: 5 parallel drafts, then a greedy debug/improve loop selected on public score, with naive full-history context.',
  phases: [
    { title: 'Draft', detail: 'parallel initial solutions, different directions' },
    { title: 'Search', detail: 'debug random buggy leaf, else improve greedy best' },
  ],
}

// ── Inputs (provided by the /rsi:autoresearch or outer-step harness) ──
// args = {
//   sandbox:  absolute path of the inner sandbox (task.md, score.py, public/, nodes/)
//   genDir:   absolute path of the generation directory (prompts/, policy.json)
//   policy:   parsed contents of genDir/policy.json (scripts cannot read files)
//   seed:     integer RNG seed for reproducibility (default 42)
//   taskName: display name for logs
// }
// Harness may deliver args as a JSON string — accept both encodings.
const A = typeof args === 'string' ? JSON.parse(args) : args || {}
const sandbox = A.sandbox
const genDir = A.genDir
const policy = A.policy || {}
const taskName = A.taskName || 'task'
if (!sandbox || !genDir) throw new Error('args.sandbox and args.genDir are required')

const NUM_DRAFTS = policy.num_drafts ?? 5
const MAX_NODES = policy.max_nodes ?? 9
const MODEL = policy.model ?? 'haiku'
const EFFORT = policy.effort ?? 'low'
const DIRECTIONS = policy.draft_directions ?? [
  'simplest correct baseline — prioritize validity over quality',
  'sorting/preprocessing-based heuristic',
  'incremental best-choice heuristic (locally optimal placements/decisions)',
  'deterministic local search: start greedy, then iteratively improve',
  'hybrid: combine two heuristics, keep the better result (deterministic, fast)',
]

// Deterministic Lehmer RNG — Workflow scripts have no Math.random by design.
let rngState = ((A.seed ?? 42) >>> 0) % 2147483647 || 1
function rand() {
  rngState = (rngState * 48271) % 2147483647
  return rngState / 2147483647
}

const NODE_SCHEMA = {
  type: 'object',
  properties: {
    code: { type: 'string', description: 'full contents of the solution.py you wrote' },
    public_score: { type: 'number', description: 'the "score" field printed by score.py --public (0 if it failed)' },
    buggy: { type: 'boolean', description: 'true if scoring errored, any per-instance error was non-null, or score is 0' },
    summary: { type: 'string', description: 'one line: approach and result' },
  },
  required: ['code', 'public_score', 'buggy', 'summary'],
  additionalProperties: false,
}

const RULES = [
  `Work ONLY inside ${sandbox} — never read or write anything outside it.`,
  'Use ONLY the public data (task.md, public/, score.py --public). Never reference or attempt to access any private or held-out split; your solution must generalize beyond the public instances, and hard-coding public-instance answers counts as failure.',
  'The solution must be deterministic, standard-library-only, and fast.',
  'Always actually run the public scorer and report its real output — never estimate or fabricate a score.',
].join('\n- ')

function nodePath(id) {
  return `${sandbox}/nodes/node-${id}/solution.py`
}

// Naive full-history context — deliberately weak (AIDE0), headroom for the
// outer loop to discover context engineering.
function historyText(nodes) {
  return nodes
    .map(
      (n) =>
        `### node-${n.id} [op=${n.op}${n.parent === null ? '' : ` parent=node-${n.parent}`} score=${n.public_score} buggy=${n.buggy}]\n` +
        `summary: ${n.summary}\n\`\`\`python\n${n.code}\n\`\`\``
    )
    .join('\n\n')
}

function draftPrompt(id, direction) {
  return `You are the DRAFT operator of a tree-search research agent working on "${taskName}" (creating node-${id}).

1. Read ${sandbox}/task.md — it defines the solution contract and scoring.
2. Read ${genDir}/prompts/draft.md and follow its method.
3. Direction for THIS draft (differentiate from sibling drafts): ${direction}
4. Write a complete solution to ${nodePath(id)}.
5. Score it: cd ${sandbox} && python3 score.py --public --solution nodes/node-${id}/solution.py --json
6. Return the structured output (exact solution code, real score, buggy flag, one-line summary).

Rules:
- ${RULES}`
}

function fixPrompt(op, id, target, nodes, promptFile) {
  const goal =
    op === 'debug'
      ? `node-${target.id} is buggy (score ${target.public_score}). Diagnose the failure and produce a FIXED solution.`
      : `node-${target.id} is the current best (score ${target.public_score}). Produce an IMPROVED solution with a strictly better public score.`
  return `You are the ${op.toUpperCase()} operator of a tree-search research agent working on "${taskName}" (creating node-${id}, child of node-${target.id}).

1. Read ${sandbox}/task.md.
2. Read ${genDir}/prompts/${promptFile} and follow its method.
3. ${goal}
4. Full search history so far (all nodes):

${historyText(nodes)}

5. Write your new complete solution to ${nodePath(id)}.
6. Score it: cd ${sandbox} && python3 score.py --public --solution nodes/node-${id}/solution.py --json
7. Return the structured output (exact solution code, real score, buggy flag, one-line summary).

Rules:
- ${RULES}`
}

function record(nodes, id, op, parent, result) {
  nodes.push({
    id,
    op,
    parent,
    code: result ? result.code : '',
    public_score: result && typeof result.public_score === 'number' ? result.public_score : 0,
    buggy: result ? Boolean(result.buggy) || result.public_score <= 0 : true,
    summary: result ? result.summary : 'agent failed or was skipped',
    path: nodePath(id),
  })
}

// ── Phase 1: parallel drafts ─────────────────────────────────────────
phase('Draft')
const nodes = []
const draftResults = await parallel(
  Array.from({ length: NUM_DRAFTS }, (_, i) => () =>
    agent(draftPrompt(i, DIRECTIONS[i % DIRECTIONS.length]), {
      label: `draft:node-${i}`,
      phase: 'Draft',
      schema: NODE_SCHEMA,
      model: MODEL,
      effort: EFFORT,
    })
  )
)
draftResults.forEach((r, i) => record(nodes, i, 'draft', null, r))
log(`drafts done: scores [${nodes.map((n) => n.public_score).join(', ')}]`)

// ── Phase 2: greedy debug/improve loop ───────────────────────────────
phase('Search')
while (nodes.length < MAX_NODES) {
  if (budget.total && budget.remaining() < 20000) {
    log(`stopping early: token budget nearly exhausted (${budget.remaining()} left)`)
    break
  }
  const id = nodes.length
  const children = new Set(nodes.filter((n) => n.parent !== null).map((n) => n.parent))
  const buggyLeaves = nodes.filter((n) => n.buggy && !children.has(n.id))
  let op, target
  if (buggyLeaves.length > 0) {
    op = 'debug'
    target = buggyLeaves[Math.floor(rand() * buggyLeaves.length)]
  } else {
    op = 'improve'
    target = nodes.reduce((a, b) => (b.public_score > a.public_score ? b : a))
  }
  const result = await agent(fixPrompt(op, id, target, nodes, `${op}.md`), {
    label: `${op}:node-${id}<-node-${target.id}`,
    phase: 'Search',
    schema: NODE_SCHEMA,
    model: MODEL,
    effort: EFFORT,
  })
  record(nodes, id, op, target.id, result)
  log(`node-${id} (${op} of node-${target.id}): score ${nodes[id].public_score}`)
}

// ── Result ───────────────────────────────────────────────────────────
const valid = nodes.filter((n) => !n.buggy)
const best = (valid.length ? valid : nodes).reduce((a, b) =>
  b.public_score > a.public_score ? b : a
)
return {
  task: taskName,
  generation: genDir,
  best: {
    node: best.id,
    public_score: best.public_score,
    solution_path: best.path,
    summary: best.summary,
  },
  n_nodes: nodes.length,
  n_buggy: nodes.filter((n) => n.buggy).length,
  nodes: nodes.map(({ code, ...meta }) => meta),
}
