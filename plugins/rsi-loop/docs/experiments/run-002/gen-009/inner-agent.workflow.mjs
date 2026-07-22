export const meta = {
  name: 'adversarial-probe-tree-search',
  description: 'Tree-search inner agent: 5 parallel drafts, then a debug/improve loop selected on PUBLIC score (clean, non-degrading). A final ADVERSARIAL PROBE phase decouples the robustness instrument from the solver: one shared, hard, generalization-probing perturbation battery is generated ONCE from the public inputs and applied identically to every candidate, so a brittle node and a generalizing node get different scores instead of both self-reporting 1.0. gen-005 refinement: the probe candidate pool no longer just re-orders the earliest public-tied DRAFT nodes — within the public-tie band it ALWAYS includes the improve/explore-lineage LEAVES (the tolerant/generalizing solvers) and scales its bounded cap with the tie count, then fills remaining slots with the strongest DRAFT candidates as brittle contrast. An anti-saturation guard escalates battery difficulty until the candidate scores spread; the returned best is the pooled candidate with the highest measured adversarial robustness (ties break toward the generalizing improve-lineage leaf). gen-006 mutation — MODALITY-AWARE PROBE: the battery builder first DETECTS task modality from task.md and the shape of the public inputs, then chooses perturbation classes accordingly. For a NUMERIC-TABULAR task (a predict(train,test)-style contract over rows of numeric features, scored by cross-validation) paraphrase/synonym variants cannot discriminate ML candidates, so it instead builds a DATA-PERTURBATION battery from the PUBLIC rows only — bootstrap resamples and subsamples of the TRAINING rows, small within-feature-scale jitter, permutation of low-signal (noise) feature columns, and single-feature holdout — written as concrete perturbed train/test row arrays; the evaluator then measures each candidate\'s prediction STABILITY on the public test rows relative to its own unperturbed-train baseline (a brittle/overfit model flips many labels under resampling, a well-regularized one holds), so tabular candidates finally SPREAD instead of saturating flat. For LANGUAGE tasks the builder keeps the existing paraphrase/synonym/re-template battery unchanged, so instruction-routing and bin-packing selection behavior is not regressed. gen-009 mutation — CORRECTNESS-COVERAGE PROBE (language tasks with a computable exact-match answer): the gen-006 LANGUAGE battery scored candidates on SELF-CONSISTENCY across answer-preserving rephrasings while holding each instance\'s ARGUMENTS fixed, so it never exercised the argument edge-cases task.md publicly enumerates for the held-out set (negatives, ties, single-item lists, larger indices/values) and its robustness ranking correlated poorly with generalization — the instruction-routing winner measured paraphrase-robustness 0.39 yet produced empty output on most held-out cases. That is a probe-BIAS problem, not sampling noise, so — unlike the REJECTED gen-008 which only averaged more paraphrase draws and dropped the instruction-routing median — gen-009 changes WHAT is measured, still a SINGLE draw: when the task is scored by exact string-equality of the solver output AND the answer is uniquely determined by a closed set of operation rules fully stated in task.md, the battery builder synthesizes a fresh COVERAGE set spanning EVERY operation with edge-case ARGUMENTS and varied PHRASING and records the builder-computed correct answer for each instance (derived only from the public rules in task.md — never any held-out data), and the evaluator scores each candidate on CORRECTNESS against those answers instead of self-consistency. Correctness-over-coverage is a near-direct proxy for the held-out objective (same operations, varied args and phrasings), so the probe ranks the genuinely general parser above a brittle one that only handles the public phrasings. Non-computable / non-exact-match language tasks and the ratio-scored bin-packing contract keep the existing paraphrase/self-consistency battery (so their selection and the 0.9379 bin-packing result are unchanged); the numeric-tabular data-perturbation path and the search / pool / escalation / single-draw selection logic are all untouched.',
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
    modality: { type: 'string', description: 'the task modality you detected and built for: "numeric-tabular" (predict/train/test rows of numbers, CV-scored); "language-coverage" (natural-language exact-match task whose answer is uniquely computable from the closed operation rules stated in task.md — you synthesize fresh instances covering every operation with edge-case arguments and varied phrasing, and record the builder-computed CORRECT answer per instance); or "language" (any other natural-language task — answer not builder-computable, so you fall back to answer-preserving paraphrases scored by self-consistency)' },
    n_source: { type: 'number', description: 'how many distinct public inputs / operations (language) or perturbed dataset variants (numeric-tabular) you drew from' },
    n_variants: { type: 'number', description: 'total number of variants/instances written across all sources' },
    variant_classes: { type: 'string', description: 'comma-separated perturbation/coverage classes you used. LANGUAGE-COVERAGE: e.g. op-add,op-subtract,...,edge-negative,edge-tie,edge-single-item,edge-large-index,synonym-phrasing,re-templated. LANGUAGE: e.g. synonym-substitution, re-templated-phrasing, clause-reorder, filler-injection, alt-encoding. NUMERIC-TABULAR: e.g. train-bootstrap, train-subsample, feature-jitter, noise-feature-permute, feature-holdout' },
    note: { type: 'string', description: 'one line: how you made these ADVERSARIAL (hard, generalization-probing) and confirmation they are answer-preserving (language) / distribution-preserving (tabular) / correctly-computed-from-public-rules (language-coverage)' },
  },
  required: ['battery_path', 'modality', 'n_source', 'n_variants', 'variant_classes', 'note'],
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
          variants_total: { type: 'number', description: 'number of battery variants/instances you actually ran this solution on' },
          variants_consistent: { type: 'number', description: 'of those, how many the candidate PASSED. LANGUAGE-COVERAGE: passed = the candidate output exactly equals the battery-provided CORRECT answer for that instance. LANGUAGE (paraphrase): passed = output equivalent to the solution\'s output on the ORIGINAL source input. NUMERIC-TABULAR: passed = prediction stayed stable vs the unperturbed-train baseline.' },
          adversarial_robustness: { type: 'number', description: 'MEASURED variants_consistent / variants_total in [0,1]. Must be actually run, never estimated.' },
          note: { type: 'string', description: 'one line: which variant/coverage classes broke this candidate' },
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
  'Build the battery from the PUBLIC inputs and the PUBLIC rules stated in task.md only, by transforming or instantiating them yourself. NEVER reference, guess at, or try to access the private / held-out split or its phrasings, rows, or answers — the whole point is to synthesize held-out-STYLE variation from public information.',
  'The battery must be valid for the modality. LANGUAGE-COVERAGE: synthesize FRESH instances covering every operation with edge-case arguments and varied phrasing, and compute each instance\'s CORRECT answer yourself strictly from the operation rules stated in task.md — never invent an answer you cannot derive from those public rules, and drop any instance whose correct answer you are unsure of. LANGUAGE (paraphrase): only apply transformations a human would agree do not change the correct answer (synonyms, rephrasings). NUMERIC-TABULAR: perturb only the TRAINING data (resample/subsample rows, jitter within feature scale, permute a low-signal column, drop one feature) — never alter the fixed public TEST rows or their true labels; a solution that genuinely generalizes should give STABLE predictions on the fixed test rows under these training perturbations, while an overfit one flips many.',
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
      ? `This is the FIRST battery. Make it genuinely adversarial from the start: reach for the HARD, generalization-probing variation a held-out set would use, not trivial variation that any candidate survives.`
      : `ESCALATION ROUND ${round}. The previous battery was TOO EASY — the candidate solutions all passed it (their scores did not spread). That means it failed as a discriminating instrument. Regenerate a STRICTLY HARDER battery within the SAME modality. LANGUAGE-COVERAGE: push the ARGUMENTS to harder edge cases (more negatives, ties, single-item and empty-ish lists, larger indices/values, mixed formatting) and combine harder phrasings, while still computing each correct answer yourself from the public rules. LANGUAGE (paraphrase): push further on synonym/paraphrase distance, re-template the whole phrasing, change sentence structure and clause order, inject more filler, use alternative equivalent encodings. NUMERIC-TABULAR: use more aggressive training-data perturbations — smaller/more-varied bootstrap subsamples, larger (but still within-scale) feature jitter, permute more of the low-signal columns, hold out more single features — and add more perturbed dataset variants so an overfit model's predictions swing more. Keep every instance valid for the modality (answer-preserving / correctly-computed / distribution-preserving). Overwrite ${BATTERY_PATH}.`
  return `You are the ADVERSARIAL PROBE BUILDER for a research agent working on "${taskName}". You do NOT see or care about any candidate solution. Your only job is to synthesize a SHARED battery of HARD, equivalence-preserving perturbations of the public data, so a downstream evaluator can tell a brittle solution apart from one that truly generalizes.

1. Read ${sandbox}/task.md and inspect the public inputs under ${sandbox}/public/.
2. Read ${genDir}/prompts/probe-battery.md and follow its method.
3. DETECT THE TASK MODALITY first, from task.md and the SHAPE of the public inputs:
   - NUMERIC-TABULAR — the contract trains on rows of numbers and predicts labels (e.g. a predict(train, test) function over rows of numeric features, scored by cross-validation). Paraphrase/synonym variants are meaningless here; a robust model is one whose predictions are STABLE under resampling and mild perturbation of the TRAINING data. Build Method A.
   - LANGUAGE-COVERAGE — the inputs are natural-language instructions, scoring is EXACT string-equality of the solver output, AND the correct answer of each instance is uniquely determined by a closed, small set of operation rules FULLY stated in task.md (so you can COMPUTE the right answer yourself). Build Method C — a correctness-coverage battery. This is the strongest instrument when it applies because it measures the SAME thing the held-out scorer does (correctness across the full operation set and argument range), not mere self-consistency.
   - LANGUAGE — any other natural-language task: scoring is not exact-match, or the answer is not something you can reliably compute from the public rules. Build Method B (answer-preserving paraphrases scored by self-consistency).
   Set the "modality" field of your output to "numeric-tabular", "language-coverage", or "language" accordingly, and build the matching battery below.
4. ${escalation}
5a. IF NUMERIC-TABULAR: build a DATA-PERTURBATION battery from the PUBLIC rows only. FIRST carve the public rows once into (i) a FIXED held-aside TEST set — a deterministic slice of the rows with their labels STRIPPED (features only, e.g. 20-30% of rows), identical across every source and the baseline — and (ii) a BASE TRAIN set (the remaining rows, WITH labels). Then emit MULTIPLE perturbed *training-set variants*, each a full (or subsampled) list of training rows produced by one or more of these classes, always paired with that same fixed test set — never perturb or relabel the test rows:
   - train-bootstrap: resample the training rows WITH replacement to the same size (seeded, deterministic).
   - train-subsample: keep a random deterministic subset (e.g. 70–85%) of the training rows.
   - feature-jitter: add small noise to feature values, scaled to each feature's own spread (small relative to its range) so the class structure is preserved.
   - noise-feature-permute: shuffle the values of ONE low-signal / noise feature column across rows (a feature that truly carries signal must NOT be permuted; identify low-signal columns from the data's own variance/label-correlation, never from the private split).
   - feature-holdout: drop ONE feature column from both the perturbed train and the test rows.
   For each variant, record the perturbed TRAINING rows and the SAME fixed TEST rows (features only) to predict, so the evaluator can retrain each candidate on the perturbed training set and compare its test-row predictions to that candidate's own predictions from the UNPERTURBED base training set. A generalizing model keeps almost all test-row predictions; an overfit model flips many.
5b. IF LANGUAGE-COVERAGE: enumerate EVERY operation the task defines (read task.md for the full list). For EACH operation, synthesize SEVERAL fresh instances (not copies of the public ones) that jointly stress two independent axes: (i) ARGUMENT edge cases the held-out set is stated to use — negatives, zero, ties/duplicates, single-item and near-empty lists, larger indices/values, and boundary values; and (ii) PHRASING variation — synonyms for the operative verb (e.g. "add" -> "sum"/"total"/"combine"/"plus"), re-templated sentences, reordered clauses, harmless filler. Combine both axes so an instance can be both a hard argument and a hard phrasing. For each instance, COMPUTE the correct answer yourself by applying the operation's rule from task.md, and match the task's exact-output convention (e.g. a bare integer with no trailing ".0", a bare word with no quotes). If you cannot be certain of an instance's correct answer from the public rules, drop that instance. Aim for broad, even coverage across all operations (do not over-weight one).
5c. IF LANGUAGE (paraphrase fallback): pick a handful of representative public inputs. For each, generate MULTIPLE equivalent variants spanning several classes that probe GENERALIZATION: synonym substitution (e.g. "add" -> "sum"/"total"/"combine"/"plus"), re-templated / reworded phrasing, different sentence structure, reordered clauses, harmless filler words, relabeled entities. Deliberately AVOID variants a trivial parser already survives (pure whitespace / letter-case / independent-item reorder) UNLESS combined with a harder class — those saturate the check.
6. Write the battery as JSON to ${BATTERY_PATH} (create ${sandbox}/nodes/_probe/ if needed). Use a self-describing structure with a top-level "modality" and a list of sources, each carrying enough for an evaluator to reproduce the comparison. NUMERIC-TABULAR example: {"modality":"numeric-tabular","sources":[{"id":<k>,"class":"train-bootstrap","base_train":[[...,label],...],"train":[[...,label],...],"test":[[...],...]}, ...]} where "test" is the same fixed features-only held-aside set on every source, "base_train" is the unperturbed base training rows (the candidate's baseline), and "train" is the perturbed training rows. LANGUAGE-COVERAGE example: {"modality":"language-coverage","sources":[{"id":<k>,"op":"add","class":"edge-negative","input":<instruction string>,"expected":<the correct answer string you computed from task.md's rules>}, ...]} — every source carries the builder-computed correct "expected" answer. LANGUAGE example: {"modality":"language","sources":[{"id":<k>,"original":<input>,"variants":[{"class":"synonym","input":<variant>}, ...]}, ...]}. Keep it standard-library JSON.
7. Return the structured metadata (path, detected modality, counts, the variant classes you used, and one line confirming they are hard and equivalence-preserving).

Rules:
- ${PROBE_RULES}`
}

function probeEvalPrompt(pool, battery) {
  const list = pool
    .map((n) => `  - node-${n.id}: solution at ${nodePath(n.id)} (public ${n.public_score})`)
    .join('\n')
  const modality = battery.modality || 'language'
  const measure =
    modality === 'numeric-tabular'
      ? `4. This is a NUMERIC-TABULAR battery: each source is a PERTURBED TRAINING set plus the fixed public TEST rows. For EACH candidate solution (do not modify any of them — only run them):
   a. Establish the candidate's BASELINE test-row predictions by running it trained on the source's UNPERTURBED base training rows against the fixed (features-only) test rows.
   b. For each perturbed source, run the SAME candidate trained on that source's perturbed training rows against the SAME fixed test rows.
   c. A source counts as CONSISTENT if the candidate's predictions on the fixed test rows match its baseline predictions on (almost) all rows (use a high agreement threshold, e.g. ≥ 95% of test-row labels unchanged); count it as a FAILURE if the solution crashes, times out, returns the wrong-length/degenerate output, or flips a large fraction of its test-row labels.
   Prediction STABILITY under training perturbation is the signal: an overfit model swings, a well-regularized one holds.`
      : modality === 'language-coverage'
      ? `4. This is a LANGUAGE-COVERAGE battery: each source is a fresh instance carrying an "input" instruction and the builder-computed CORRECT "expected" answer (covering every operation across edge-case arguments and varied phrasing). This measures CORRECTNESS, the same thing the held-out scorer measures — NOT self-consistency. For EACH candidate solution (do not modify any of them — only run them), and for EACH source: run the candidate on the source's "input", then compare its output to "expected" using the task's exact-match convention (compare str(output).strip() to expected, exactly as task.md's scorer does). Count the source as CONSISTENT (passed) if they match exactly; count it as a FAILURE if the solution crashes, hangs, returns empty/degenerate output, or returns the wrong answer. A brittle parser that only handles the public phrasings/arguments will FAIL many of these; a genuinely general parser passes most.`
      : `4. This is a LANGUAGE (paraphrase) battery: each variant is an answer-preserving rephrasing of an original source input. For EACH candidate solution (do not modify any of them — only run them), and for EACH variant: run the candidate on the variant's input AND on its original source input, then decide whether the variant output is a VALID output EQUIVALENT to the output on the original (the perturbation is answer-preserving, so a generalizing solution should not change its answer; a brittle one will crash, return empty/degenerate, or flip).`
  return `You are the ADVERSARIAL PROBE EVALUATOR for a research agent working on "${taskName}". A shared, deliberately HARD ${modality} perturbation battery has already been written to ${battery.battery_path} (${battery.n_variants} variants across ${battery.n_source} sources; classes: ${battery.variant_classes}). Every candidate below is scored against the SAME battery so the results are comparable.

Candidates (all have near-identical public score; your measurement breaks the tie):
${list}

1. Read ${sandbox}/task.md so you know what "equivalent output" means for this task (same predicted labels / same routing / same objective value / valid packing of equal quality, etc.).
2. Read ${genDir}/prompts/probe-eval.md and follow its method.
3. Load the battery at ${battery.battery_path}.
${measure}
5. adversarial_robustness for a candidate = variants_consistent / variants_total (for numeric-tabular, "variants" are the perturbed sources and "consistent" means its predictions stayed stable), ACTUALLY MEASURED by running the code. Report per-candidate results plus one line on whether the battery separated the candidates.

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
