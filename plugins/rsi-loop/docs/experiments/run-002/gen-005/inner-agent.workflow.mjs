export const meta = {
  name: 'adversarial-probe-tree-search',
  description: 'Tree-search inner agent: 5 parallel drafts, then a debug/improve loop selected on PUBLIC score (clean, non-degrading). A final ADVERSARIAL PROBE phase decouples the robustness instrument from the solver: one shared, hard, generalization-probing perturbation battery is generated ONCE from the public inputs and applied identically to every candidate, so a brittle node and a generalizing node get different scores instead of both self-reporting 1.0. gen-005 refinement: the probe candidate pool no longer just re-orders the earliest public-tied DRAFT nodes — within the public-tie band it ALWAYS includes the improve/explore-lineage LEAVES (the synonym-tolerant solvers that generalize best) and scales its bounded cap with the tie count, then fills remaining slots with the strongest DRAFT candidates as brittle contrast. An anti-saturation guard escalates battery difficulty until the candidate scores spread; the returned best is the pooled candidate with the highest measured adversarial robustness (ties break toward the generalizing improve-lineage leaf).',
  phases: [
    { title: 'Draft', detail: 'parallel initial solutions, different directions' },
    { title: 'Search', detail: 'debug random buggy leaf, else improve greedy public best; reserves budget for the probe' },
    { title: 'Probe', detail: 'build one shared adversarial battery, measure each top-public candidate against it, pick the most robust' },
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
// ── Adversarial-probe selection knobs (tunable via policy, no logic change) ──
// Candidates eligible for the probe: valid nodes whose public score is within
// PUBLIC_TIE_BAND of the max public score. The probe only ever re-orders
// NEAR-TIED-public candidates, so it can never trade public score away (the
// gen-003 failure mode where combined-score steering dropped public).
//
// gen-005 POOL REFINEMENT (why this exists): gen-004 sorted the tied candidates
// by ASCENDING id and truncated to PROBE_TOPK=4. With 5 drafts + up to 4 search
// nodes, that pool was always the four earliest DRAFT nodes, so the later
// synonym-heavy IMPROVE leaves (which parse/normalize input tolerantly and
// generalize far better on held-out data) were NEVER probed and therefore could
// never be selected. Fix: within the public-tie band, ALWAYS include the
// improve/explore-lineage LEAVES, and grow the (still bounded) cap with the tie
// count so those leaves are never truncated; fill the remaining slots with the
// strongest DRAFT-lineage candidates so the battery still has a brittle baseline
// to spread against. PROBE_TOPK is now the BASE cap; PROBE_TOPK_MAX bounds it.
const PROBE_TOPK = policy.probe_topk ?? 4
const PROBE_TOPK_MAX = policy.probe_topk_max ?? 8
const PUBLIC_TIE_BAND = policy.public_tie_band ?? 0.05
// Anti-saturation guard: if the battery cannot separate the candidates by at
// least MIN_SPREAD, it is too easy — escalate difficulty and re-measure, up to
// MAX_ESCALATIONS extra rounds. A battery that still cannot spread the scores is
// a FAILED check: we fall back to the deterministic top-public pick, we do NOT
// treat a saturated 1.0 as "everyone is robust".
const MIN_SPREAD = policy.min_spread ?? 0.1
const MAX_ESCALATIONS = policy.max_escalations ?? 1
// Tokens to leave unspent by the search loop so the probe phase can actually run
// (the probe is the whole point of this generation — never let search starve it).
const PROBE_RESERVE = policy.probe_reserve_tokens ?? 350000
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

function clamp01(x) {
  const n = typeof x === 'number' && isFinite(x) ? x : 0
  return n < 0 ? 0 : n > 1 ? 1 : n
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

// The battery agent WRITES a shared perturbation set to disk and reports metadata
// only. Decoupling generation (this agent, blind to any solution) from evaluation
// is what forces a spread: the same hard variants hit every candidate.
const BATTERY_SCHEMA = {
  type: 'object',
  properties: {
    battery_path: { type: 'string', description: 'absolute path of the JSON battery file you wrote' },
    n_source: { type: 'number', description: 'how many distinct public inputs you drew variants from' },
    n_variants: { type: 'number', description: 'total number of equivalent variants written across all sources' },
    variant_classes: { type: 'string', description: 'comma-separated list of the perturbation classes you used (e.g. synonym-substitution, re-templated-phrasing, clause-reorder, filler-injection, alt-encoding, edge-scale)' },
    note: { type: 'string', description: 'one line: how you made these ADVERSARIAL (hard, generalization-probing) and confirmation they are answer-preserving' },
  },
  required: ['battery_path', 'n_source', 'n_variants', 'variant_classes', 'note'],
  additionalProperties: false,
}

// The eval agent reads the SAME battery file and runs each candidate solution on
// originals + variants, reporting a MEASURED consistency fraction per candidate.
const PROBE_EVAL_SCHEMA = {
  type: 'object',
  properties: {
    results: {
      type: 'array',
      description: 'one entry per candidate node id you were given',
      items: {
        type: 'object',
        properties: {
          node: { type: 'number', description: 'the candidate node id' },
          variants_total: { type: 'number', description: 'number of battery variants you actually ran this solution on' },
          variants_consistent: { type: 'number', description: 'of those, how many produced a valid output equivalent to the solution\'s output on the ORIGINAL source input (answer-preserving perturbation ⇒ answer should not change)' },
          adversarial_robustness: { type: 'number', description: 'MEASURED variants_consistent / variants_total in [0,1]. Must be actually run, never estimated.' },
          note: { type: 'string', description: 'one line: which variant classes broke this candidate' },
        },
        required: ['node', 'variants_total', 'variants_consistent', 'adversarial_robustness', 'note'],
        additionalProperties: false,
      },
    },
    battery_note: { type: 'string', description: 'one line: did the battery separate the candidates, or did they all pass (saturated)?' },
  },
  required: ['results', 'battery_note'],
  additionalProperties: false,
}

const RULES = [
  `Work ONLY inside ${sandbox} — never read or write anything outside it.`,
  'Use ONLY the public data (task.md, public/, score.py --public). Never reference or attempt to access any private or held-out split; your solution must generalize beyond the public instances, and hard-coding public-instance answers counts as failure.',
  'The solution must be deterministic, standard-library-only, and fast.',
  'Always actually run the public scorer and report its real output — never estimate or fabricate a score.',
].join('\n- ')

const PROBE_RULES = [
  `Work ONLY inside ${sandbox} — never read or write anything outside it.`,
  'Build every perturbation from the PUBLIC inputs only, by transforming them yourself. NEVER reference, guess at, or try to access the private / held-out split or its phrasings or answers — the whole point is to synthesize held-out-STYLE variation from public data.',
  'Perturbations must be ANSWER-PRESERVING: only apply transformations a human would agree do not change the correct answer. Do not alter anything that would legitimately change the answer.',
  'Measure, never estimate. Every reported number must come from actually running the code on the actual files. A fabricated battery or a fabricated robustness fraction is a protocol violation and will be caught by re-running.',
].join('\n- ')

function nodePath(id) {
  return `${sandbox}/nodes/node-${id}/solution.py`
}
const BATTERY_PATH = `${sandbox}/nodes/_probe/battery.json`

// Search context: public score only (clean AIDE0-style steering). Robustness is
// measured once, at the end, by the shared adversarial probe — NOT self-reported
// per node (that self-report saturated at 1.0 in the prior generation).
function historyText(nodes) {
  return nodes
    .map(
      (n) =>
        `### node-${n.id} [op=${n.op}${n.parent === null ? '' : ` parent=node-${n.parent}`} public=${n.public_score} buggy=${n.buggy}]\n` +
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
      : `node-${target.id} is the current best (public ${target.public_score}). Produce an IMPROVED solution with a strictly better public score. Note: after the search, the final winner among near-tied candidates is chosen by an ADVERSARIAL robustness probe (hard rephrasings, synonyms, re-templated inputs, edge-scale variants). So when public score is saturated, the durable win is a solution that parses/normalizes input tolerantly and generalizes — that is what the probe rewards.`
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

function batteryPrompt(round) {
  const escalation =
    round === 0
      ? `This is the FIRST battery. Make it genuinely adversarial from the start: reach for the HARD, generalization-probing variation a held-out set would use, not trivial whitespace/case/reorder that any parser survives.`
      : `ESCALATION ROUND ${round}. The previous battery was TOO EASY — the candidate solutions all passed it (their scores did not spread). That means it failed as a discriminating instrument. Regenerate a STRICTLY HARDER battery: push further on synonym/paraphrase distance, re-template the whole phrasing, change sentence structure and clause order, inject more filler, use alternative equivalent encodings, and (for numeric/structural tasks) larger, edge-shaped but still-equivalent instances. Keep every variant answer-preserving. Overwrite ${BATTERY_PATH}.`
  return `You are the ADVERSARIAL PROBE BUILDER for a research agent working on "${taskName}". You do NOT see or care about any candidate solution. Your only job is to synthesize a SHARED battery of HARD, answer-preserving variants of the public inputs, so a downstream evaluator can tell a brittle solution apart from one that truly generalizes.

1. Read ${sandbox}/task.md and inspect the public inputs under ${sandbox}/public/.
2. Read ${genDir}/prompts/probe-battery.md and follow its method.
3. ${escalation}
4. Pick a handful of representative public inputs. For each, generate MULTIPLE equivalent variants spanning several perturbation CLASSES that probe GENERALIZATION, e.g.:
   - language tasks: synonym substitution (e.g. "add" -> "sum"/"total"/"combine"/"plus"), re-templated / reworded phrasing, different sentence structure, reordered clauses, harmless filler words, relabeled entities.
   - numeric / structural tasks: alternative equivalent encodings, larger or edge-case-shaped instances, harder value distributions.
   Deliberately AVOID variants a trivial parser already survives (pure whitespace / letter-case / independent-item reorder) UNLESS combined with a harder class — those saturate the check.
5. Write the battery as JSON to ${BATTERY_PATH} (create ${sandbox}/nodes/_probe/ if needed). Use a self-describing structure: a list of sources, each with the original input and its list of variants, and enough info for an evaluator to feed a variant to a solution and compare its output to the solution's output on the original. Keep it standard-library JSON.
6. Return the structured metadata (path, counts, the variant classes you used, and one line confirming they are hard and answer-preserving).

Rules:
- ${PROBE_RULES}`
}

function probeEvalPrompt(pool, battery) {
  const list = pool
    .map((n) => `  - node-${n.id}: solution at ${nodePath(n.id)} (public ${n.public_score})`)
    .join('\n')
  return `You are the ADVERSARIAL PROBE EVALUATOR for a research agent working on "${taskName}". A shared, deliberately HARD perturbation battery has already been written to ${battery.battery_path} (${battery.n_variants} variants across ${battery.n_source} sources; classes: ${battery.variant_classes}). Every candidate below is scored against the SAME battery so the results are comparable.

Candidates (all have near-identical public score; your measurement breaks the tie):
${list}

1. Read ${sandbox}/task.md so you know what "equivalent output" means for this task (same label / same routing / same objective value / valid packing of equal quality, etc.).
2. Read ${genDir}/prompts/probe-eval.md and follow its method.
3. Load the battery at ${battery.battery_path}.
4. For EACH candidate node above, and for EACH variant: run that candidate's solution on the variant's input AND on its original source input, then decide whether the variant output is a VALID output EQUIVALENT to the output on the original (the perturbation is answer-preserving, so a generalizing solution should not change its answer; a brittle one will crash, return empty/degenerate, or flip).
5. adversarial_robustness for a candidate = variants_consistent / variants_total, ACTUALLY MEASURED by running the code. Report per-candidate results plus one line on whether the battery separated the candidates.

Do NOT edit any candidate solution — only run them. Report the real measured fractions even if they are all high; a saturated result is itself a finding (it tells the outer loop the battery was too easy).

Rules:
- ${PROBE_RULES}`
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
    adversarial_robustness: null, // filled in by the probe phase for pooled candidates
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
log(`drafts done: public [${nodes.map((n) => n.public_score).join(', ')}]`)

// ── Phase 2: greedy public debug/improve loop (reserves budget for probe) ──
phase('Search')
while (nodes.length < MAX_NODES) {
  if (budget.total && budget.remaining() < PROBE_RESERVE) {
    log(`stopping search to reserve budget for the adversarial probe (${budget.remaining()} left)`)
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
  log(`node-${id} (${op} of node-${target.id}): public ${nodes[id].public_score}`)
}

// ── Phase 3: shared adversarial probe over top-public candidates ──────
// This is the hardened selection instrument. Instead of every node grading
// itself on perturbations it already handles (which saturated at 1.0), ONE
// shared adversarial battery is applied to all near-tied-public candidates, so
// their scores actually spread and the generalizing node is the one returned.
phase('Probe')
const valid = nodes.filter((n) => !n.buggy)
const basePool = valid.length ? valid : nodes
const maxPublic = basePool.reduce((m, n) => (n.public_score > m ? n.public_score : m), -Infinity)

// ── Lineage-aware candidate pool (gen-005) ───────────────────────────
// A node is a LEAF if no other node was forked from it (the current frontier);
// it is IMPROVE-LINEAGE if it was produced by the improve operator or descends
// from one (so a debug-child of an improve still counts — it carries the
// tolerant-parsing idea). The improve-lineage leaves are the synonym-heavy
// generalizers we must be able to select.
const byId = new Map(nodes.map((n) => [n.id, n]))
const parents = new Set(nodes.filter((n) => n.parent !== null).map((n) => n.parent))
const isLeaf = (n) => !parents.has(n.id)
function isImproveLineage(n) {
  let cur = n
  let guard = 0
  while (cur && guard++ < nodes.length + 1) {
    if (cur.op === 'improve') return true
    cur = cur.parent === null ? null : byId.get(cur.parent)
  }
  return false
}
const generalizes = (n) => isLeaf(n) && isImproveLineage(n)

const byPublic = (a, b) => b.public_score - a.public_score || a.id - b.id
// Near-tied-public candidates only — the probe re-orders within this band and
// therefore can never sacrifice public score.
const tied = basePool.filter((n) => n.public_score >= maxPublic - PUBLIC_TIE_BAND)

// MUST-PROBE: every tied improve/explore-lineage leaf. These generalize best on
// held-out data and were the exact candidates gen-004 excluded — they are now
// guaranteed into the pool (bounded by the ceiling so probe budget stays fixed).
const mustProbe = tied.filter((n) => generalizes(n)).sort(byPublic).slice(0, PROBE_TOPK_MAX)
// CONTRAST: strongest remaining tied candidates (typically the early DRAFT
// nodes) so the battery has a brittle baseline to spread the improves against —
// a pool of only-tolerant nodes could saturate and hide the win.
const contrast = tied.filter((n) => !mustProbe.includes(n)).sort(byPublic)
// Bounded, tie-count-scaled cap: fit all must-probe leaves plus a couple of
// contrast drafts, never exceeding PROBE_TOPK_MAX.
const target = Math.min(PROBE_TOPK_MAX, Math.max(PROBE_TOPK, mustProbe.length + 2))
const need = Math.max(0, target - mustProbe.length)
const pool = [...mustProbe, ...contrast.slice(0, need)].sort(byPublic)
log(
  `probe pool: [${pool.map((n) => `node-${n.id}(${n.op}${generalizes(n) ? ',leaf*' : ''})`).join(', ')}] ` +
    `(${mustProbe.length} improve-lineage leaf/leaves guaranteed, cap ${target})`
)

let probe = { ran: false, spread: 0, escalations: 0, saturated: false, battery: null, results: [] }

async function runAdversarialProbe(candidates) {
  let spread = 0
  let results = []
  let battery = null
  let round = 0
  for (;;) {
    if (budget.total && budget.remaining() < PROBE_RESERVE / 3) {
      log(`probe: low budget, stopping escalation (${budget.remaining()} left)`)
      break
    }
    battery = await agent(batteryPrompt(round), {
      label: `probe-battery:round-${round}`,
      phase: 'Probe',
      schema: BATTERY_SCHEMA,
      model: MODEL,
      effort: EFFORT,
    })
    if (!battery || !battery.battery_path) {
      log('probe: battery generation failed; aborting probe')
      break
    }
    const ev = await agent(probeEvalPrompt(candidates, battery), {
      label: `probe-eval:round-${round}`,
      phase: 'Probe',
      schema: PROBE_EVAL_SCHEMA,
      model: MODEL,
      effort: EFFORT,
    })
    results = ev && Array.isArray(ev.results) ? ev.results : []
    const vals = results.map((r) => clamp01(r.adversarial_robustness))
    spread = vals.length ? Math.max(...vals) - Math.min(...vals) : 0
    log(
      `probe round ${round}: robustness [${results
        .map((r) => `n${r.node}=${clamp01(r.adversarial_robustness).toFixed(2)}`)
        .join(', ')}] spread ${spread.toFixed(3)}`
    )
    // Anti-saturation guard: a battery that cannot spread the candidates is too
    // easy and has FAILED as an instrument — escalate difficulty and re-measure.
    if (spread >= MIN_SPREAD || round >= MAX_ESCALATIONS) break
    round++
  }
  return { spread, results, battery, escalations: round, saturated: spread < MIN_SPREAD }
}

let best
if (pool.length <= 1) {
  // Nothing to discriminate — one clear public leader. Return it directly.
  best = pool.length ? pool[0] : basePool.reduce((a, b) => (b.public_score > a.public_score ? b : a))
  log(`probe skipped: single top-public candidate node-${best.id} (public ${best.public_score})`)
} else {
  const r = await runAdversarialProbe(pool)
  probe = { ran: true, spread: r.spread, escalations: r.escalations, saturated: r.saturated, battery: r.battery, results: r.results }
  const robMap = new Map()
  for (const res of r.results) {
    if (res && typeof res.node === 'number') robMap.set(res.node, clamp01(res.adversarial_robustness))
  }
  for (const n of pool) if (robMap.has(n.id)) n.adversarial_robustness = robMap.get(n.id)

  if (!r.saturated && robMap.size > 0) {
    // The instrument DISCRIMINATED: return the top-public candidate with the
    // highest measured adversarial robustness (tiebreak: higher public, lower id).
    best = pool.reduce((a, b) => {
      const ra = robMap.has(a.id) ? robMap.get(a.id) : -1
      const rb = robMap.has(b.id) ? robMap.get(b.id) : -1
      if (rb !== ra) return rb > ra ? b : a
      // Robustness tie → prefer the improve/explore-lineage leaf (broader
      // paraphrase handling) over a brittle early draft; then higher public,
      // then lower id.
      const ga = generalizes(a) ? 1 : 0
      const gb = generalizes(b) ? 1 : 0
      if (gb !== ga) return gb > ga ? b : a
      if (b.public_score !== a.public_score) return b.public_score > a.public_score ? b : a
      return b.id < a.id ? b : a
    })
    log(`probe DISCRIMINATED (spread ${r.spread.toFixed(3)}): selecting node-${best.id} (public ${best.public_score}, adversarial_robustness ${clamp01(best.adversarial_robustness).toFixed(2)})`)
  } else {
    // Saturated even after escalation → the instrument could not separate the
    // candidates. That is a FAILED check, not a pass: fall back to the
    // deterministic top-public pick rather than trusting a flat 1.0.
    best = pool[0]
    log(`probe SATURATED (spread ${r.spread.toFixed(3)} < ${MIN_SPREAD}) after ${r.escalations} escalation(s): falling back to top-public node-${best.id}`)
  }
}

// ── Result ───────────────────────────────────────────────────────────
return {
  task: taskName,
  generation: genDir,
  best: {
    node: best.id,
    public_score: best.public_score,
    adversarial_robustness: best.adversarial_robustness,
    solution_path: best.path,
    summary: best.summary,
  },
  probe: {
    ran: probe.ran,
    pool: pool.map((n) => n.id),
    spread: probe.spread,
    escalations: probe.escalations,
    saturated: probe.saturated,
    battery_variants: probe.battery ? probe.battery.n_variants : 0,
    robustness: probe.results.map((r) => ({ node: r.node, adversarial_robustness: clamp01(r.adversarial_robustness) })),
  },
  n_nodes: nodes.length,
  n_buggy: nodes.filter((n) => n.buggy).length,
  nodes: nodes.map(({ code, ...meta }) => meta),
}
