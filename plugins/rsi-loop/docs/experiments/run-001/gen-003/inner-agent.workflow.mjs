export const meta = {
  name: 'aide2-exploit-explorer-inner-agent',
  description: 'AIDE2 tree-search inner agent: family-tagged parallel drafts, a seeded stress tie-breaker, and a search loop whose explore/improve switch is fully lexicographic — code-blind EXPLORE roots fire only while the top of the leaderboard is indistinguishable on BOTH public and stress scores (or after a failed improve), so a new family that wins the stress tie-break becomes uniquely best and immediately receives greedy IMPROVE children instead of being abandoned as a one-shot root.',
  phases: [
    { title: 'Draft', detail: 'parallel initial solutions, each committed to a distinct algorithm family' },
    { title: 'Stress', detail: 'build a seeded synthetic stress suite and evaluate existing drafts on it' },
    { title: 'Search', detail: 'debug buggy leaves; explore a NEW family only while the top is lexicographically tied or an improve stalled; otherwise exploit the unique lexicographic best with improve' },
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
  "family 'naive-baseline': simplest correct baseline — prioritize validity over quality",
  "family 'sorted-greedy': order the input once, then place each element by a fixed greedy rule",
  "family 'complement-matching': build the solution by explicitly pairing/grouping complementary elements that combine tightly — NOT a one-pass greedy placement",
  "family 'local-search-repack': start from a trivial valid solution, then apply deterministic improvement moves (relocate, swap, merge, re-split) until a fixpoint — the move engine is the point",
  "family 'exact-hybrid': solve small subproblems exactly (bounded DP / branch-and-bound / exhaustive over small subsets, with strict cutoffs) and fall back safely on large inputs",
]

// Deterministic Lehmer RNG — Workflow scripts have no Math.random by design.
let rngState = ((A.seed ?? 42) >>> 0) % 2147483647 || 1
function rand() {
  rngState = (rngState * 48271) % 2147483647
  return rngState / 2147483647
}

const FAMILY_FIELD = {
  type: 'string',
  description: "short kebab-case algorithm-family label for this solution's core mechanism (e.g. sorted-greedy, complement-matching, local-search-repack, exact-hybrid); keep the parent's label unless you fundamentally replaced the algorithm",
}

const NODE_SCHEMA = {
  type: 'object',
  properties: {
    code: { type: 'string', description: 'full contents of the solution.py you wrote' },
    public_score: { type: 'number', description: 'the "score" field printed by score.py --public (0 if it failed)' },
    buggy: { type: 'boolean', description: 'true if scoring errored, any per-instance error was non-null, or score is 0' },
    family: FAMILY_FIELD,
    summary: { type: 'string', description: 'one line: approach and result' },
  },
  required: ['code', 'public_score', 'buggy', 'family', 'summary'],
  additionalProperties: false,
}

const SEARCH_NODE_SCHEMA = {
  type: 'object',
  properties: {
    code: { type: 'string', description: 'full contents of the solution.py you wrote' },
    public_score: { type: 'number', description: 'the "score" field printed by score.py --public (0 if it failed)' },
    stress_score: { type: 'number', description: 'the "stress_score" printed by nodes/stress/stress_eval.py (0 if the harness is unavailable or the eval failed)' },
    buggy: { type: 'boolean', description: 'true if public scoring errored, any per-instance error was non-null, or public score is 0' },
    family: FAMILY_FIELD,
    summary: { type: 'string', description: 'one line: approach and result' },
  },
  required: ['code', 'public_score', 'stress_score', 'buggy', 'family', 'summary'],
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

// Full-history context for improve/debug (they refine existing code).
function historyText(nodes) {
  return nodes
    .map(
      (n) =>
        `### node-${n.id} [op=${n.op}${n.parent === null ? '' : ` parent=node-${n.parent}`} family=${n.family} score=${n.public_score} stress=${n.stress_score ?? 0} buggy=${n.buggy}]\n` +
        `summary: ${n.summary}\n\`\`\`python\n${n.code}\n\`\`\``
    )
    .join('\n\n')
}

// Code-blind context for explore: families, scores, summaries — no code, so the
// explorer cannot anchor on the incumbent implementation.
function familyText(nodes) {
  return nodes
    .map(
      (n) =>
        `- node-${n.id}: family=${n.family} public=${n.public_score} stress=${n.stress_score ?? 0} buggy=${n.buggy} — ${n.summary}`
    )
    .join('\n')
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
3. Direction for THIS draft (sibling drafts hold the other families — your value to the search is ONLY as high as your fidelity to this family): ${direction}
4. Write a complete solution to ${nodePath(id)}.
5. Score it: cd ${sandbox} && python3 score.py --public --solution nodes/node-${id}/solution.py --json
6. Return the structured output (exact solution code, real score, buggy flag, your family label, one-line summary).

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

function explorePrompt(id, nodes, best, stressReady) {
  const families = [...new Set(nodes.filter((n) => !n.buggy).map((n) => n.family))]
  const stressStep = stressReady
    ? `6. Also run the stress suite: ${stressCmd(id)} — report the real "stress_score" it prints (0 if it fails). It is a deterministic synthetic tie-breaker: when public scores tie, the higher stress score wins.`
    : `6. The stress harness is unavailable this run — report stress_score as 0.`
  return `You are the EXPLORE operator of a tree-search research agent working on "${taskName}" (creating node-${id}, a fresh root — no parent).

The search has stalled: every working solution so far comes from the algorithm families listed
below, and they tie on the public score. More variants of those families are worthless. Your
job is DIVERSITY: design and implement a solution whose CORE MECHANISM belongs to a family NOT
on the banned list, and make it strong enough to beat the incumbent.

1. Read ${sandbox}/task.md — it defines the solution contract and scoring.
2. Read ${genDir}/prompts/explore.md and follow its method.
3. Incumbent to beat: public ${best ? best.public_score : 0}, stress ${best ? best.stress_score ?? 0 : 0}. Success = strictly higher public score, or equal public score with strictly higher stress score.
4. Existing nodes (family, scores, one-line summary — code deliberately withheld so you design fresh, not imitate):
${familyText(nodes)}

   BANNED families: ${families.join(', ') || '(none reported)'}.
   Judge by mechanism, not by label: if your plan amounts to "order the elements once, then
   place each one into an open slot by a fixed rule", it is the same sorted-greedy family no
   matter what you call it, and it is banned.
5. Write a complete solution to ${nodePath(id)}, then score it:
   cd ${sandbox} && python3 score.py --public --solution nodes/node-${id}/solution.py --json
${stressStep}
7. Return the structured output (exact solution code, real public score, real stress score, buggy flag, a NEW family label not on the banned list, one-line summary).

Rules:
- ${RULES}`
}

function fixPrompt(op, id, target, nodes, promptFile, stressReady) {
  const goal =
    op === 'debug'
      ? `node-${target.id} is buggy (score ${target.public_score}). Diagnose the failure and produce a FIXED solution that preserves its algorithm family (${target.family}).`
      : `node-${target.id} is the current best (public score ${target.public_score}, stress score ${target.stress_score ?? 0}, family ${target.family}). Produce an IMPROVED solution: strictly better public score, or an equal public score with a strictly better stress score.`
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
8. Return the structured output (exact solution code, real public score, real stress score, buggy flag, family label, one-line summary).

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
    family: result && typeof result.family === 'string' && result.family ? result.family : 'unknown',
    summary: result ? result.summary : 'agent failed or was skipped',
    path: nodePath(id),
  })
}

// ── Phase 1: parallel drafts, one algorithm family each ─────────────
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
log(`drafts done: scores [${nodes.map((n) => n.public_score).join(', ')}] families [${nodes.map((n) => n.family).join(', ')}]`)

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
      log('stress harness unavailable — continuing without the tie-breaker')
    }
  } else {
    log('no working drafts to calibrate the stress harness on — skipping')
  }
} else {
  log('stress harness disabled by policy')
}

// ── Phase 3: search — debug buggy leaves; explore a new family only while
// the top is lexicographically tied (public AND stress) or an improve
// stalled; otherwise exploit the unique lexicographic best with improve ──
phase('Search')
let stalled = false
while (nodes.length < MAX_NODES) {
  if (budget.total && budget.remaining() < 20000) {
    log(`stopping early: token budget nearly exhausted (${budget.remaining()} left)`)
    break
  }
  const id = nodes.length
  const children = new Set(nodes.filter((n) => n.parent !== null).map((n) => n.parent))
  const buggyLeaves = nodes.filter((n) => n.buggy && !children.has(n.id))
  const valid = nodes.filter((n) => !n.buggy)
  const best = valid.length ? valid.reduce((a, b) => (betterNode(b, a) ? b : a)) : null
  let op, target, result
  if (buggyLeaves.length > 0) {
    op = 'debug'
    target = buggyLeaves[Math.floor(rand() * buggyLeaves.length)]
  } else if (!best) {
    op = 'explore'
    target = null
  } else {
    // Lexicographic top-tie detection: explore only while some OTHER working
    // node is indistinguishable from the best on BOTH public and stress
    // scores — i.e. the full measurement instrument has lost its gradient.
    // A node that wins the stress tie-break is uniquely best, so the search
    // EXPLOITS it with improve children (the gen-002 public-only tie check
    // stayed permanently true and starved winning explore roots of improves).
    const coTied = valid.filter((n) => n.id !== best.id && !betterNode(best, n))
    op = stalled || coTied.length >= 1 ? 'explore' : 'improve'
    target = best
  }
  if (op === 'explore') {
    result = await agent(explorePrompt(id, nodes, best, stressReady), {
      label: `explore:node-${id}`,
      phase: 'Search',
      schema: SEARCH_NODE_SCHEMA,
      model: MODEL,
      effort: EFFORT,
    })
    record(nodes, id, 'explore', null, result)
  } else {
    result = await agent(fixPrompt(op, id, target, nodes, `${op}.md`, stressReady), {
      label: `${op}:node-${id}<-node-${target.id}`,
      phase: 'Search',
      schema: SEARCH_NODE_SCHEMA,
      model: MODEL,
      effort: EFFORT,
    })
    record(nodes, id, op, target.id, result)
  }
  // Stall bookkeeping: a non-debug node that fails to strictly beat the prior
  // best (lexicographic) marks the current line as stalled → next op explores.
  if (op !== 'debug') {
    stalled = best ? !(!nodes[id].buggy && betterNode(nodes[id], best)) : nodes[id].buggy
  }
  log(`node-${id} (${op}${target ? ` of node-${target.id}` : ''}): public ${nodes[id].public_score}, stress ${nodes[id].stress_score}, family ${nodes[id].family}${stalled && op !== 'debug' ? ' [stalled]' : ''}`)
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
    family: best.family,
    solution_path: best.path,
    summary: best.summary,
  },
  stress_harness: stressReady,
  n_nodes: nodes.length,
  n_buggy: nodes.filter((n) => n.buggy).length,
  n_families: new Set(nodes.filter((n) => !n.buggy).map((n) => n.family)).size,
  nodes: nodes.map(({ code, ...meta }) => meta),
}
