export const meta = {
  name: 'robustness-aware-tree-search',
  description: 'Tree-search inner agent: 5 parallel drafts, then a debug/improve loop selected on a ROBUSTNESS-AWARE combined score. Each node self-runs an invariance check (perturbs the public inputs into equivalent variants and measures output stability), and selection prefers solutions that generalize over ones that merely max the public score.',
  phases: [
    { title: 'Draft', detail: 'parallel initial solutions, different directions, each self-checked for input-variation robustness' },
    { title: 'Search', detail: 'debug random buggy leaf, else improve the best node by combined public*robustness score' },
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
// How much a node's self-measured robustness discounts its public score during
// selection. combined = public * ((1 - W) + W * robustness), robustness in [0,1].
// At W=0.5 a brittle node (robustness 0) is halved; a fully robust node is
// unchanged. Tunable via policy without touching the search logic.
const ROBUSTNESS_WEIGHT = policy.robustness_weight ?? 0.5
// The real per-generation directions live in policy.json (`draft_directions`),
// which the harness always passes. This inline list is only a last-resort
// default for a hand-run with no policy — keep it generic, not a shadow copy of
// any specific generation's tuned directions.
const DIRECTIONS =
  policy.draft_directions ??
  Array.from({ length: NUM_DRAFTS }, (_, i) => `distinct solution direction #${i + 1}`)

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
    robustness: { type: 'number', description: 'MEASURED fraction in [0,1] from your own invariance check: run your solution on equivalent, perturbed copies of the public inputs and report the fraction that stayed valid and stable (non-degenerate). Must be actually run, never estimated. If you could not run the check, report 0.' },
    robustness_note: { type: 'string', description: 'one line: what perturbations you applied and what you observed (e.g. which variants broke the solution)' },
    buggy: { type: 'boolean', description: 'true if scoring errored, any per-instance error was non-null, or score is 0' },
    summary: { type: 'string', description: 'one line: approach and result' },
  },
  required: ['code', 'public_score', 'robustness', 'robustness_note', 'buggy', 'summary'],
  additionalProperties: false,
}

const RULES = [
  `Work ONLY inside ${sandbox} — never read or write anything outside it.`,
  'Use ONLY the public data (task.md, public/, score.py --public). Never reference or attempt to access any private or held-out split; your solution must generalize beyond the public instances, and hard-coding public-instance answers counts as failure.',
  'The solution must be deterministic, standard-library-only, and fast.',
  'Always actually run the public scorer and report its real output — never estimate or fabricate a score.',
  'The robustness number must come from ACTUALLY running your invariance check (see the operator method). Report the measured value only; a fabricated robustness is a protocol violation just like a fabricated score.',
].join('\n- ')

function nodePath(id) {
  return `${sandbox}/nodes/node-${id}/solution.py`
}

// Combined selection score: public score discounted by self-measured
// robustness, so a solution that overfits the public split (high public,
// low robustness) loses to one that generalizes. Buggy nodes score 0.
function robustnessOf(n) {
  const r = typeof n.robustness === 'number' ? n.robustness : 0.5
  return r < 0 ? 0 : r > 1 ? 1 : r
}
function combinedScore(n) {
  if (n.buggy) return 0
  return n.public_score * ((1 - ROBUSTNESS_WEIGHT) + ROBUSTNESS_WEIGHT * robustnessOf(n))
}

// Context: show each node's public score AND its measured robustness, so the
// improve operator can see when a lineage is brittle (high public, low
// robustness) and knows to fix generalization rather than chase public points.
function historyText(nodes) {
  return nodes
    .map(
      (n) =>
        `### node-${n.id} [op=${n.op}${n.parent === null ? '' : ` parent=node-${n.parent}`} public=${n.public_score} robustness=${robustnessOf(n).toFixed(2)} combined=${combinedScore(n).toFixed(3)} buggy=${n.buggy}]\n` +
        `summary: ${n.summary}\n` +
        `robustness_note: ${n.robustness_note || '(none reported)'}\n\`\`\`python\n${n.code}\n\`\`\``
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
6. Run the INVARIANCE CHECK described in draft.md: generate equivalent, perturbed copies of the public inputs and measure how stably your solution handles them. Report the measured fraction as robustness.
7. Return the structured output (exact solution code, real public score, measured robustness, buggy flag, one-line summary).

Rules:
- ${RULES}`
}

function fixPrompt(op, id, target, nodes, promptFile) {
  const goal =
    op === 'debug'
      ? `node-${target.id} is buggy (public ${target.public_score}). Diagnose the failure and produce a FIXED solution.`
      : `node-${target.id} is the current best by combined score (public ${target.public_score}, robustness ${robustnessOf(target).toFixed(2)}, combined ${combinedScore(target).toFixed(3)}). Produce an IMPROVED solution with a strictly better COMBINED score — raise the public score, the robustness, or both. If public is already saturated but robustness is low, the win is to make the solution handle input variation (rephrasings, reordering, formatting, synonyms) without degrading.`
  return `You are the ${op.toUpperCase()} operator of a tree-search research agent working on "${taskName}" (creating node-${id}, child of node-${target.id}).

1. Read ${sandbox}/task.md.
2. Read ${genDir}/prompts/${promptFile} and follow its method.
3. ${goal}
4. Full search history so far (all nodes, with public score AND measured robustness):

${historyText(nodes)}

5. Write your new complete solution to ${nodePath(id)}.
6. Score it: cd ${sandbox} && python3 score.py --public --solution nodes/node-${id}/solution.py --json
7. Run the INVARIANCE CHECK described in ${promptFile}: perturb the public inputs into equivalent variants, run your solution on them, and report the measured robustness fraction.
8. Return the structured output (exact solution code, real public score, measured robustness, buggy flag, one-line summary).

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
    robustness: result && typeof result.robustness === 'number' ? result.robustness : 0.5,
    robustness_note: result ? result.robustness_note : '',
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
log(`drafts done: public [${nodes.map((n) => n.public_score).join(', ')}] robustness [${nodes.map((n) => robustnessOf(n).toFixed(2)).join(', ')}]`)

// ── Phase 2: robustness-aware debug/improve loop ─────────────────────
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
    // Improve the best node by COMBINED score, not raw public — this is the
    // core anti-overfitting change: a brittle public-max node no longer
    // dominates the search over a slightly-lower but generalizing node.
    target = nodes.reduce((a, b) => (combinedScore(b) > combinedScore(a) ? b : a))
  }
  const result = await agent(fixPrompt(op, id, target, nodes, `${op}.md`), {
    label: `${op}:node-${id}<-node-${target.id}`,
    phase: 'Search',
    schema: NODE_SCHEMA,
    model: MODEL,
    effort: EFFORT,
  })
  record(nodes, id, op, target.id, result)
  log(`node-${id} (${op} of node-${target.id}): public ${nodes[id].public_score} robustness ${robustnessOf(nodes[id]).toFixed(2)} combined ${combinedScore(nodes[id]).toFixed(3)}`)
}

// ── Result ───────────────────────────────────────────────────────────
// Final pick is the best by COMBINED score (public discounted by measured
// robustness). This is what the harness will score on the held-out split, so
// preferring the generalizing node here is the whole point of the mutation.
const valid = nodes.filter((n) => !n.buggy)
const pool = valid.length ? valid : nodes
const best = pool.reduce((a, b) => (combinedScore(b) > combinedScore(a) ? b : a))
return {
  task: taskName,
  generation: genDir,
  best: {
    node: best.id,
    public_score: best.public_score,
    robustness: robustnessOf(best),
    combined_score: combinedScore(best),
    solution_path: best.path,
    summary: best.summary,
  },
  n_nodes: nodes.length,
  n_buggy: nodes.filter((n) => n.buggy).length,
  nodes: nodes.map(({ code, ...meta }) => meta),
}
