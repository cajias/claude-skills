export const meta = {
  name: 'aide1-stress-tiebreak-inner-agent',
  description: 'AIDE1 tree-search inner agent: 5 parallel drafts, then a self-generated seeded stress suite whose score breaks ties when the public metric saturates, then a debug/improve loop selected on (public, stress).',
  phases: [
    { title: 'Draft', detail: 'parallel initial solutions, different directions' },
    { title: 'Stress', detail: 'build a seeded synthetic stress suite and evaluate existing drafts on it' },
    { title: 'Search', detail: 'debug random buggy leaf, else improve best by (public score, stress tie-break)' },
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
const USE_STRESS = policy.stress_harness !== false
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

const SEARCH_NODE_SCHEMA = {
  type: 'object',
  properties: {
    code: { type: 'string', description: 'full contents of the solution.py you wrote' },
    public_score: { type: 'number', description: 'the "score" field printed by score.py --public (0 if it failed)' },
    stress_score: { type: 'number', description: 'the "stress_score" printed by nodes/stress/stress_eval.py (0 if the harness is unavailable or the eval failed)' },
    buggy: { type: 'boolean', description: 'true if public scoring errored, any per-instance error was non-null, or public score is 0' },
    summary: { type: 'string', description: 'one line: approach and result' },
  },
  required: ['code', 'public_score', 'stress_score', 'buggy', 'summary'],
  additionalProperties: false,
}

const STRESS_SCHEMA = {
  type: 'object',
  properties: {
    harness_ok: { type: 'boolean', description: 'true only if make_stress.py generated the suite and stress_eval.py ran successfully on at least one node' },
    evals: {
      type: 'array',
      description: 'real stress_eval.py output for each existing node you were asked to evaluate',
      items: {
        type: 'object',
        properties: {
          node: { type: 'integer', description: 'node id' },
          stress_score: { type: 'number', description: 'the real "stress_score" printed by stress_eval.py for this node (0 if it failed)' },
        },
        required: ['node', 'stress_score'],
        additionalProperties: false,
      },
    },
    summary: { type: 'string', description: 'one line: suite composition and headline results' },
  },
  required: ['harness_ok', 'evals', 'summary'],
  additionalProperties: false,
}

const RULES = [
  `Work ONLY inside ${sandbox} — never read or write anything outside it.`,
  'Use ONLY the public data (task.md, public/, score.py --public). Never reference or attempt to access any private or held-out split; your solution must generalize beyond the public instances, and hard-coding public-instance answers counts as failure.',
  'The solution must be deterministic, standard-library-only, and fast.',
  'Always actually run the public scorer and report its real output — never estimate or fabricate a score. The same applies to the stress score: report only what stress_eval.py actually printed.',
].join('\n- ')

function nodePath(id) {
  return `${sandbox}/nodes/node-${id}/solution.py`
}

function stressCmd(id) {
  return `cd ${sandbox} && python3 nodes/stress/stress_eval.py --solution nodes/node-${id}/solution.py --json`
}

// Naive full-history context — deliberately weak (AIDE0), headroom for the
// outer loop to discover context engineering.
function historyText(nodes) {
  return nodes
    .map(
      (n) =>
        `### node-${n.id} [op=${n.op}${n.parent === null ? '' : ` parent=node-${n.parent}`} score=${n.public_score} stress=${n.stress_score ?? 0} buggy=${n.buggy}]\n` +
        `summary: ${n.summary}\n\`\`\`python\n${n.code}\n\`\`\``
    )
    .join('\n\n')
}

// Lexicographic comparison: public score first, stress score breaks ties.
function betterNode(a, b) {
  if (a.public_score !== b.public_score) return a.public_score > b.public_score
  return (a.stress_score ?? 0) > (b.stress_score ?? 0)
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

function stressPrompt(drafts) {
  const list = drafts
    .map((n) => `- node-${n.id}: nodes/node-${n.id}/solution.py (public score ${n.public_score})`)
    .join('\n')
  return `You are the STRESS-HARNESS operator of a tree-search research agent working on "${taskName}".

The public split is small, so working solutions often tie on the public score and the search
loses its gradient. Your job is to build a finer-grained, generalization-oriented measurement
instrument: a deterministic synthetic stress suite plus an evaluator, so the search can tell
tied solutions apart.

1. Read ${sandbox}/task.md and ${sandbox}/score.py to learn the exact instance format, solution
   contract, and scoring formula.
2. Read ${genDir}/prompts/stress.md and follow its method.
3. Write ${sandbox}/nodes/stress/make_stress.py and ${sandbox}/nodes/stress/stress_eval.py.
4. Generate the suite: cd ${sandbox} && python3 nodes/stress/make_stress.py
5. Evaluate each existing working node on the suite with
   cd ${sandbox} && python3 nodes/stress/stress_eval.py --solution nodes/node-<id>/solution.py --json
   Nodes to evaluate:
${list}
6. Return the structured output with the REAL stress_score printed for each node.

Rules:
- ${RULES}
- The stress suite must be your own synthetic creation from the task definition: never copy
  public instances into it, and never attempt to guess, imitate, or access any private or
  held-out data.`
}

function fixPrompt(op, id, target, nodes, promptFile, stressReady) {
  const goal =
    op === 'debug'
      ? `node-${target.id} is buggy (score ${target.public_score}). Diagnose the failure and produce a FIXED solution.`
      : `node-${target.id} is the current best (public score ${target.public_score}, stress score ${target.stress_score ?? 0}). Produce an IMPROVED solution: strictly better public score, or an equal public score with a strictly better stress score.`
  const stressStep = stressReady
    ? `7. Also run the stress suite: ${stressCmd(id)} — report the real "stress_score" it prints (0 if it fails). The stress suite is a deterministic synthetic tie-breaker: it rewards genuine generalization when the small public split cannot distinguish solutions.`
    : `7. The stress harness is unavailable this run — report stress_score as 0.`
  return `You are the ${op.toUpperCase()} operator of a tree-search research agent working on "${taskName}" (creating node-${id}, child of node-${target.id}).

1. Read ${sandbox}/task.md.
2. Read ${genDir}/prompts/${promptFile} and follow its method.
3. ${goal}
4. Full search history so far (all nodes):

${historyText(nodes)}

5. Write your new complete solution to ${nodePath(id)}.
6. Score it: cd ${sandbox} && python3 score.py --public --solution nodes/node-${id}/solution.py --json
${stressStep}
8. Return the structured output (exact solution code, real public score, real stress score, buggy flag, one-line summary).

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
    stress_score: result && typeof result.stress_score === 'number' ? result.stress_score : 0,
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

// ── Phase 2: build the stress harness and score existing drafts ──────
phase('Stress')
let stressReady = false
if (USE_STRESS) {
  const workingDrafts = nodes.filter((n) => !n.buggy)
  if (workingDrafts.length > 0) {
    let h = null
    try {
      h = await agent(stressPrompt(workingDrafts), {
        label: 'stress:harness',
        phase: 'Stress',
        schema: STRESS_SCHEMA,
        model: MODEL,
        effort: EFFORT,
      })
    } catch (e) {
      log(`stress harness agent failed: ${e && e.message ? e.message : e}`)
    }
    if (h && h.harness_ok === true && Array.isArray(h.evals)) {
      for (const e of h.evals) {
        const n = nodes.find((x) => x.id === e.node)
        if (n && typeof e.stress_score === 'number') n.stress_score = e.stress_score
      }
      stressReady = true
      log(`stress harness ready: ${h.summary} | stress scores [${nodes.map((n) => n.stress_score ?? 0).join(', ')}]`)
    } else {
      log('stress harness unavailable — falling back to greedy public selection')
    }
  } else {
    log('no working drafts to calibrate the stress harness on — skipping')
  }
} else {
  log('stress harness disabled by policy')
}

// ── Phase 3: debug/improve loop, selected on (public, stress) ────────
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
    target = nodes.reduce((a, b) => (betterNode(b, a) ? b : a))
  }
  const result = await agent(fixPrompt(op, id, target, nodes, `${op}.md`, stressReady), {
    label: `${op}:node-${id}<-node-${target.id}`,
    phase: 'Search',
    schema: SEARCH_NODE_SCHEMA,
    model: MODEL,
    effort: EFFORT,
  })
  record(nodes, id, op, target.id, result)
  log(`node-${id} (${op} of node-${target.id}): public ${nodes[id].public_score}, stress ${nodes[id].stress_score}`)
}

// ── Result ───────────────────────────────────────────────────────────
const valid = nodes.filter((n) => !n.buggy)
const best = (valid.length ? valid : nodes).reduce((a, b) => (betterNode(b, a) ? b : a))
return {
  task: taskName,
  generation: genDir,
  best: {
    node: best.id,
    public_score: best.public_score,
    stress_score: best.stress_score ?? 0,
    solution_path: best.path,
    summary: best.summary,
  },
  stress_harness: stressReady,
  n_nodes: nodes.length,
  n_buggy: nodes.filter((n) => n.buggy).length,
  nodes: nodes.map(({ code, ...meta }) => meta),
}
