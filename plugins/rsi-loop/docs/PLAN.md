# rsi-loop — Implementation Plan

Faithful re-implementation of Weco's **AIDE²** recursive self-improvement (RSI) method as a
Claude Code plugin, built from skills, commands, subagents, and the built-in Workflow
orchestrator.

Primary sources:

- explainx summary: <https://explainx.ai/blog/weco-aide2-recursive-self-improvement-rsi-ladder-july-2026>
- Weco first-party report: <https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement>
- RSI ladder definition: <https://www.weco.ai/blog/4-levels-of-recursive-self-improvement>

Status: **M1–M2 shipped; M3 complete (run-002 ran to a plateau stop at 10 ledger steps,
~37.9M inner tokens, incumbent gen-006); M4 measured (Level 0 and Level 1 met — see
`docs/experiments/m4-report.md`); M5 ignition run complete — returned Level-2 NOT supported (ignited
0.5876 < control 0.6126 at equal 1-step budget; see `docs/experiments/ignite/README.md`).** That verdict
is now diagnosed as a measurement artifact — a category-error ignition test — and **Level 2 was reopened
as M6** (Approach-1 isomorphic re-architecture, design COMPLETE — full resolved spec in §6.1; see §6).
**M6 is now RESOLVED (2026-07-28): verdict NO_RESULT (paper parity), declared up front on a
power/battery-resolution basis** — see `docs/experiments/ignite-m6/verdict.json`. A real cost probe first
exposed that the inner shim's `await import()` is forbidden by the Workflow runtime (fixed by inlining the
engine, PR #60; caught at \$0). The fresh gen-000 discovery campaign then found a **real, verifier-clean
lift** (gen-001, a prompt-only k-fold-CV mutation: 0.8265 → 0.844, gain entirely on tabular), so the scaffold
_can_ self-improve within the frozen 8-field vocabulary. But the battery cannot resolve a scaffold-vs-scaffold
asymptote difference: bin-packing is 100% saturated (0.8705, zero signal) and tabular headroom is small, so the
**maximum achievable ΔA ≈ 0.040 < MDE(3) = 0.071** at measured `σ_d` = 0.049 (`K_req(0.040)` = 10 seeds). Spending
the ~\$400 paired A/B would confirm a predetermined NO_RESULT — the exact M5 mistake — so it was declared up
front. Total spend ~\$13 of a \$420 ceiling. Paper-parity: control and ignited reach the same battery-imposed
ceiling ("converged faster, no asymptotic advantage"). The plugin is
promoted in `.claude-plugin/marketplace.json`. Real-compute results so far: gen-000 floor
0.575 → gen-005 0.856 private aggregate (+0.281, two accepted improvements across steps 2–3);
gen-005 beats the hand-tuned `gen-human` baseline 0.588 (Level 1, +0.269); holdout near-transfer
mean Δ +0.279 (carried by instruction-ops 0.0 → 0.85), far-OOD Δ −0.016 (timeseries-forecast,
reported separately). The §5.2 chassis A/B is **resolved (2026-07-20): ship Arm B (native
`/rsi:step` / `/rsi:run`); autoresearch stays as pattern reference** (evidence in
`docs/experiments/chassis-ab/`). M1–M5 execution is banked history: the M5 `/rsi:ignite` Level-2 campaign
ran (step-1 paired A/B → Level-2 NOT supported, `docs/experiments/ignite/README.md`). A design review since
diagnosed that "not supported" as a **measurement artifact / category error** — the old `/rsi:ignite`
injected the incumbent's task-solving strategy into a stock proposer and compared campaign endpoints, which
tests "does a strategy-briefed proposer beat a stock one," not the paper's actual ignition question — is the
discovered inner agent a better `outer` agent than its predecessor, judged on the whole campaign trajectory
(convergence rate + asymptote), a first-order comparison a 1-step endpoint A/B structurally cannot make; the loop also
banked only ~3 genuine forward meta-steps and never carried the outer optimizer forward, so ignition was
untestable regardless. **Level 2 is therefore reopened as M6** (Approach-1 isomorphic re-architecture, design
COMPLETE — see §6/§6.1). The −0.025 run itself stands; only its interpretation changed. This document is the build
spec; where the shipped code has diverged from it, the deviation is noted inline and in
[CONTINUATION.md](CONTINUATION.md).

As-built notes (M3 additions):

- The paper's three reward-hack defense layers (§1) split by ownership: the anti-overfitting
  stage prompts (layer 1) live in each generation's mutable prompts; the "statistical removal
  of too-good results" (layer 3) is realized as an **immutable outer-side detector**,
  `scripts/rsi-aggregate.py --flag-outliers`, consumed by the verifier — a harness DETECTION
  mechanism, consistent with the integrity model, not a generation-side trick the loop must
  discover. Robust cross-seed aggregation (median of seeds) in the same script addresses the
  tiny-battery noise risk (§7).
- `/rsi:run` is the native-Workflow chassis (Arm B). The §5.2 chassis A/B is resolved
  (2026-07-20) in favor of Arm B — the native driver stands, and autoresearch (Arm A) stays as
  pattern reference (evidence in `docs/experiments/chassis-ab/`).
- **M3 extension — evaluation protocol switch (run-002).** Mid-run the protocol moved from
  single-seed to robust `--seeds 3` (seeds 42/43/44), selecting on mean-of-per-task-medians via
  `scripts/rsi-aggregate.py --aggregate`, after single-seed scores on the tiny private splits
  proved unreliable: gen-005's banked headline `private_aggregate` 0.856 turned out to be a lucky
  single-seed draw (robust re-baseline = **0.644**). This validates the §7 "tiny splits are noisy,
  prefer multi-seed" caveat rather than contradicting it.
- **Modality-aware adversarial probe (accepted gen-006, now incumbent).** The probe evolved to
  pick its perturbation battery by task modality — a **data-perturbation** battery
  (train bootstrap / subsample / jitter / noise-permute / feature-holdout, scored by prediction
  stability) for numeric-tabular tasks, the paraphrase battery for language — because the
  paraphrase battery could not discriminate ML-model candidates. Re-evaluated at seeds-3, gen-006
  scored robust **0.725 > 0.644** → accepted, verifier-clean.
- **Plateau stop.** Two subsequent seeds-3 steps both rejected — gen-008 "multi-draw de-noising"
  (0.696) and gen-009 "correctness-coverage probe" (0.546) — so 2 consecutive rejections triggered
  a plateau stop at 10 ledger steps (~37.9M cumulative inner tokens). Key RSI finding: the
  instruction-routing private split (n=32) is **probe-limited** — no public-data-only probe
  (self-consistency, multi-draw, correctness-coverage) reliably predicts its private
  generalization; gen-006 is the ceiling of gen-005's neighborhood under the 3-family battery.
- As-built PLAN.md reconciliation complete (this pass).

---

## 1. The method we are replicating

AIDE² frames RSI as **bi-level optimization**: an outer-loop agent optimizes the inner-loop
agent's _ability to optimize_.

### Outer loop (supervisor)

Per step (100 steps in the paper, ~8 days, ~90% proposal rejection):

1. **Propose** — outer agent (Claude Opus 4.7 in the paper) rewrites the inner agent's code.
2. **Evaluate** — candidate inner agent runs on a heterogeneous task battery under a **fixed
   dollar budget** per evaluation.
3. **Select** — keep the rewrite only if it beats the incumbent best on **private (held-out)
   scores** the inner agent never sees.
4. Repeat: AIDE0 → AIDE99. Best performers: AIDE47 (step 50), AIDE85 (step 100).

### Inner agent (worker) — AIDE0 baseline

- Tree-search research agent (cheap model — Gemini 3 Flash in the paper) with three operators:
  - **Draft** — 5 initial solutions, each prompted toward a different direction
  - **Debug** — targets a random buggy leaf node
  - **Improve** — enhances the current best node
- Baseline policy: greedy parent selection; drafting phase first, then alternate debug/improve.
- Baseline context handling: naive full-history concatenation (deliberately weak — headroom for
  the outer loop to discover better).

### Evaluation protocol

- **Public/private split** per task: the inner agent optimizes the visible public score; survival
  is decided by the hidden private score (anti-overfitting).
- **Fixed budget** per evaluation, metered in dollars: gains must come from better algorithms,
  not brute-force scaling (best-of-N, parallelism explosion all rejected by the constraint).
- **Heterogeneous task families** to force generalizable improvements:
  1. ML engineering (train models against measurable metrics)
  2. Heuristic/combinatorial optimization (routing, packing, scheduling)
  3. Harness engineering (improving LLM agent scaffolds themselves)
- **Second-order generalization**: winners re-tested on benchmark families never optimized
  against (MLE-Bench Lite, ALE-Bench Lite, WeatherBench 2 far-OOD).

### Reward-hacking defenses (three layers, discovered by the loop itself)

1. Anti-overfitting instructions embedded in stage prompts
2. Hard-coded guards that regenerate suspicious outputs
3. Statistical outlier removal of "too good" results

Detection rule: a solution counts as hacked if <50% of its claimed gain survives end-to-end
re-testing. Hack rate fell 63% (AIDE0) → 34% (AIDE85).

### What the evolved agent (AIDE85) discovered — target behaviors to leave room for

- **Multi-armed bandit lineages**: each draft subtree is a bandit arm; explore across lineages,
  greedy within one; fork the global best into a new lineage on stagnation.
- **~16× context compression**: per-operator minimal context instead of transcript dumps
  (newest-12 one-liners + one full solution).
- **Matrix context gating**: debug/improve/eval-review get different prompt slices; some
  components gated on signals (e.g. include only when recent bug rate > 15%; improve receives a
  plateau signal from the last four scores).
- **Evaluation repair**: fixed a crashing eval harness rather than exploiting it.

### RSI ladder (falsifiable claims)

| Level | Name         | Criterion                                                                                   | AIDE² result                                                            |
| ----- | ------------ | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| 0     | Delegation   | System improves itself, but slower than human R&D                                           | floor                                                                   |
| 1     | Net positive | Improves itself **faster** than human R&D (fair baseline, sustained, general, fixed budget) | claimed ✓                                                               |
| 2     | Ignition     | vN's improvement campaign beats what vN−1 would produce at equal budget                     | rejected (AIDE47-as-outer converged faster but no asymptotic advantage) |
| 3     | Inflection   | Gains per generation grow under constant investment                                         | not claimed                                                             |

---

## 2. Mapping AIDE² onto Claude Code primitives

The key translation: in AIDE² the inner agent is Python code; here the inner agent is a
**directory of prompt + policy + orchestration files** — which is exactly what a Claude Code
skill is. "Rewriting the inner agent's code" becomes rewriting those files, which Claude is
natively good at.

| AIDE² concept               | Claude Code realization                                                                                                                                            |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Inner agent "code"          | `generations/gen-NNN/` — Workflow script (tree search) + operator prompts + `policy.json`                                                                          |
| Inner agent model (Flash)   | cheap model via `agent(..., {model: 'haiku'})`                                                                                                                     |
| Outer agent (Opus 4.7)      | session model (Opus/Fable) running the `/rsi:step` skill                                                                                                           |
| Solution tree + operators   | Workflow script: `parallel()` drafts, loop of debug/improve `agent()` calls                                                                                        |
| Fixed dollar budget         | Workflow `budget` (token target as dollar proxy) + hard agent-count caps                                                                                           |
| Public/private split        | `tasks/<task>/public/` vs `tasks/<task>/private/`; private scoring runs only in the outer loop; a PreToolUse deny hook blocks inner agents from reading `private/` |
| Keep-if-better selection    | outer skill compares aggregate private scores, updates `ledger.jsonl` + `best` pointer                                                                             |
| Heterogeneous task families | 3 mini-families checked into `tasks/` (see §4)                                                                                                                     |
| Reward-hack detection       | verifier subagent re-runs winners end-to-end; <50%-of-claim rule; outlier filter                                                                                   |
| Second-order generalization | `holdout-tasks/` never used during the run; scored only by `/rsi:report`                                                                                           |
| RSI ladder measurement      | `/rsi:report` computes slopes vs. the hand-tuned baseline; `/rsi:ignite` runs the Level-2 swap test                                                                |

Two fidelity compromises, called out explicitly:

1. **Budget metering** — we meter tokens/agent-calls rather than dollars. Same intent
   (efficiency-forcing), different unit. The Workflow tool's `budget.spent()`/`remaining()` is
   the enforcement point.
2. **Scale** — the paper ran 100 outer steps over 8 days on real benchmarks. We target
   10–30 outer steps on miniature tasks that score in seconds. The _protocol_ is the match, not
   the compute.

## 3. Plugin architecture

```text
plugins/rsi-loop/
├── .claude-plugin/plugin.json
├── README.md
├── docs/
│   └── PLAN.md                     ← this file
├── commands/
│   ├── rsi-init.md                 # /rsi:init — scaffold a run dir, gen-000, ledger
│   ├── rsi-step.md                 # /rsi:step [n] — run n outer-loop steps
│   ├── rsi-run.md                  # /rsi:run — loop /rsi:step until budget/steps exhausted
│   ├── rsi-report.md               # /rsi:report — scores, lineage, ladder-level evidence
│   └── rsi-ignite.md               # /rsi:ignite — Level-2 test: best gen becomes outer agent
├── skills/
│   ├── rsi-loop/SKILL.md           # orchestration knowledge: the outer-loop protocol
│   └── autoresearch/SKILL.md       # standalone inner agent: run tree-search autoresearch on
│                                   # any task with a score script (/rsi:autoresearch <task>)
├── agents/
│   ├── proposer.md                 # outer-loop rewriter (strong model)
│   ├── verifier.md                 # reward-hack auditor (re-runs winners, <50% rule)
│   └── inner-runner.md             # thin wrapper that executes a generation on one task
├── hooks/
│   └── hooks.json                  # PreToolUse deny: inner agents reading */private/*
├── baseline/
│   ├── gen-000/                    # faithful AIDE0: greedy, naive context
│   │   ├── inner-agent.workflow.mjs
│   │   ├── prompts/{draft,debug,improve}.md
│   │   └── policy.json
│   └── gen-human/                  # "AIDEhuman" analog: best hand-tuned config (Level-1 baseline)
├── tasks/                          # training battery (public+private per task)
└── holdout-tasks/                  # second-order generalization set — never touched by the loop
```

### Run-time state (created by `/rsi:init` in the user's workspace, not the plugin)

```text
rsi-runs/<run-id>/
├── generations/gen-000 … gen-NNN/  # every proposed rewrite, accepted or not
├── ledger.jsonl                    # one line per outer step: proposal summary, public/private
│                                   # scores per task, budget spent, accept/reject, hack flags
├── best                            # symlink/pointer to incumbent generation
└── transcripts/                    # inner-run journals for post-hoc analysis
```

### The outer step (`/rsi:step`), precisely

1. Read `ledger.jsonl` (full lineage history — the outer agent _does_ get history; only the
   inner agent gets minimal context).
2. **Proposer** subagent (strong model) writes `gen-N+1/` as a mutation of `best`, with a
   one-paragraph rationale and a _predicted_ effect. Prompted with the paper's proposal
   diversity: search policy, context engineering, operator prompts, verification — anything in
   the generation dir.
3. **Evaluate**: for each task in the battery, run `gen-N+1`'s Workflow script via a cheap-model
   inner runner under a fixed token cap. Inner agent sees only `public/`. Collect public scores.
4. **Private scoring**: outer loop (never the inner agent) runs `score.py --private` on each
   task's private split.
5. **Verifier** subagent audits the top results: re-runs claimed winners end-to-end; flags
   hacked if <50% of the claimed gain survives; strips statistical outliers.
6. **Select**: accept iff aggregate private score (post-verification) beats incumbent. Either
   way, append the ledger line. Expect and log a high rejection rate — ~90% in the paper is a
   feature, not a bug.

### The inner agent (`baseline/gen-000`), precisely — faithful AIDE0

A Workflow script interpreting `policy.json`:

- Phase 1: `parallel()` of **5 draft** agents, each with a different-direction hint.
- Phase 2: loop until node/budget cap — if buggy leaves exist, **debug** a random one;
  else **improve** the greedy-best node.
- Context: naive concatenation of all prior nodes (deliberately weak, as in the paper).
- Each node = candidate solution + `score.py --public` result. Output: best node by public score.

Everything the proposer may rewrite lives in the generation dir; the runner harness, scorers,
budget enforcement, and ledger live _outside_ it and are immutable to the loop (that boundary is
the paper's harness/agent split, and our main anti-hack wall).

### `autoresearch` as a standalone skill

The inner agent is also exposed as its own skill, decoupled from the RSI loop — mirroring the
paper's lineage, where AIDE was a useful standalone agent (first place on MLE-Bench) before
AIDE² wrapped it:

- `/rsi:autoresearch <task-dir>` runs whichever generation `best` points to (falling back to
  `baseline/gen-000`) against any user-supplied task that provides a `task.md` and a scoring
  command — no outer loop, no private split required.
- This gives the plugin immediate standalone value (an AIDE-style solve-by-tree-search agent for
  ML/heuristic/harness tasks) and doubles as the manual test surface for M1.
- Because the skill always resolves through the `best` pointer, users of `/rsi:autoresearch`
  automatically benefit from improvements the outer loop discovers — the paper's "inner
  improvements generalize upward" alternative to stacking meta-loops.
- Note: this is _experiment-driven_ research (write code → run → score → iterate on a solution
  tree), distinct from the built-in `deep-research` skill's web-research loop (search → verify
  sources → cited report). The two are complementary, not substitutes.

## 4. Task battery (miniature but heterogeneous, per the paper's three families)

Each task ships `public/` (data + `score.py --public`), `private/` (held-out data +
`--private`), and a `task.md`. Scoring must be deterministic and run in seconds.

1. **ML engineering** — small tabular prediction (sklearn-style, bundled CSV); public = CV score
   on public split, private = held-out rows. (MLE-Bench analog.)
2. **Heuristic optimization** — bin-packing / TSP-style instances; public = visible instance
   set, private = hidden instances of different sizes. (ALE-Bench analog.)
3. **Harness engineering** — improve a small agent scaffold's prompt+context against a fixed
   eval set (can reuse this repo's `scripts/test-skills.sh` conventions);
   private = unseen eval cases. (The self-referential family from the paper.)

`holdout-tasks/`: one unseen task per family plus one far-OOD task (WeatherBench-2 analog —
e.g. a time-series forecasting mini-task from a different domain). Scored only by
`/rsi:report`, never during the loop.

## 5. Third-party skills / components we can leverage

Nothing existing implements bi-level RSI as a skill — searched the claude.ai plugin catalog
(no hits for self-improvement/prompt-optimization/eval-harness) and known marketplaces. But we
can compose substantial existing pieces rather than build from scratch:

| Component                                       | Source                                                                                             | What we reuse                                                                                                                                                                                                                                                                 |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **autoresearch**                                | [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) (MIT, 5.3k★, active)         | Candidate **outer-loop chassis** — see §5.1. Its core loop (modify → mechanical verify → keep/discard, auto-revert, git-as-memory, TSV ledger, guard commands, plateau detection via `/autoresearch:evals`) is exactly the outer step's shape. Not usable as the inner agent. |
| **Workflow tool**                               | Claude Code built-in                                                                               | The entire orchestration substrate: deterministic loops, `parallel()` fan-out, per-agent `model`/`effort` overrides (model asymmetry), `budget` (fixed-budget constraint), structured-output schemas (scores), journals (transcripts). Both loops are Workflow scripts.       |
| **skill-creator**                               | Anthropic (official)                                                                               | Skill authoring + its eval/benchmark harness — used to build the harness-engineering task family and to validate rewritten generations structurally.                                                                                                                          |
| **deep-research**                               | Claude Code built-in                                                                               | Pattern reference for the verifier stage (adversarial claim-checking before accepting results). Not reusable as the inner agent: it does web research (search → verify → cited report), not experiment-driven autoresearch (code → run → score → iterate).                    |
| **ralph-loop**                                  | Geoff Huntley's ralph technique (already referenced in this repo's `skills/ralph-loop-invocation`) | Prior art for long-running loop-until-done outer iteration with max-iterations + completion promise; `/rsi:run` follows the same invocation ergonomics.                                                                                                                       |
| **/loop** (built-in) + `send_later`/Routines    | Claude Code built-in                                                                               | Multi-day unattended outer-loop pacing — the paper's 8-day unattended run maps to scheduled wakeups re-invoking `/rsi:step`.                                                                                                                                                  |
| **claudeception, session-mining**               | this repo                                                                                          | Complementary, not core: mine accepted-proposal rationales from transcripts into reusable skills (a human-digestible byproduct the paper doesn't have).                                                                                                                       |
| **scripts/validate.sh, scripts/test-skills.sh** | this repo                                                                                          | Structural gate every proposed generation must pass before spending eval budget.                                                                                                                                                                                              |
| **DSPy / GEPA, OpenEvolve (AlphaEvolve OSS)**   | Python libraries, not skills                                                                       | Pattern reference only (evolutionary prompt/code optimization, keep-if-better + lineages). We replicate natively; no dependency.                                                                                                                                              |

### 5.1 `uditgoenka/autoresearch` evaluation

A mature Claude Code skill implementing goal-directed optimization loops: modify → verify
against a single mechanical metric → commit or auto-revert → repeat, with git history as
memory, TSV iteration ledgers, must-pass guard commands, safety hooks, and an autonomous
orchestrator mode (v2.2). Generalizes Karpathy's autoresearch framing beyond ML.

**What it is not** (why it can't be our inner agent): it is a _single-level_ hill-climb —
one atomic change per iteration on a linear history. AIDE0 requires solution-**tree** search
with parallel drafts and draft/debug/improve operators, a public/private score split (its
metric is fully visible to the loop; the guard command is the only overfitting defense), a
fixed cost budget as a first-class constraint, and a bi-level structure where the loop's own
code is the thing being optimized. None of these exist there.

**What it maps to precisely**: the AIDE² _outer_ loop is itself "modify the inner agent's
files → evaluate mechanically → keep iff better → repeat" — autoresearch's exact contract.
Adoption sketch:

- scope = the incumbent generation dir; one outer step = one autoresearch iteration
- metric = aggregate private battery score, emitted by our **immutable** harness script (the
  outer loop is allowed to see private scores — only inner agents are firewalled)
- guard = structural validation (`validate.sh`-style) + the verifier's hack check, so hacked
  wins fail the guard and auto-revert
- its TSV ledger and plateau detection subsume parts of our `ledger.jsonl` + `/rsi:report`

**Decision point (M2)**: prototype the outer step both ways — (a) depend on autoresearch as an
installed plugin driving our harness scripts, vs. (b) native Workflow-script outer loop.
Adopt (a) if its iteration contract accommodates multi-task private scoring + verifier gating
without forking it; otherwise keep it as pattern/code reference (MIT permits lifting the
revert/ledger/guard mechanics). Risks of (a): coupling our step semantics to its release
cadence, and single-metric plumbing flattening the per-task score vector too early.

### 5.2 Chassis experiment: outer loop with vs. without the autoresearch skill

The §5.1 decision is settled empirically, not by taste — a paired A/B run in M2:

**Arms** (everything else held identical: `baseline/gen-000` starting point, task battery,
proposer + verifier prompts and models, per-eval token cap, seeds):

- **Arm A (with skill)**: outer loop driven by `uditgoenka/autoresearch` — metric script =
  aggregate private battery score from our immutable harness; guard = structural validation +
  verifier hack check; its git-commit/auto-revert = our accept/reject.
- **Arm B (without skill)**: outer loop as our native Workflow script (`/rsi:step` loop) with
  `ledger.jsonl` accept/reject.

**Protocol**: 10 outer steps per arm, 2 repetitions each (variance on tiny batteries is real);
both arms write the same ledger schema so runs are directly comparable. Total: 4 short runs.

**Metrics** (pre-registered, in priority order):

1. _Primary_: best private aggregate score reached at equal total token budget.
2. Score-per-token slope across steps (efficiency of the loop itself).
3. Harness overhead: tokens spent on orchestration vs. on inner-agent evaluation.
4. Protocol fidelity: did accept/reject always follow private score + guard? any hacked win
   slipping past the guard? ledger completeness; crash/resume behavior mid-run.
5. Friction notes: forks/patches needed, multi-task score plumbing, verifier integration.

**Decision rule** (recorded here with the results when M2 lands): adopt Arm A only if it is
within noise of or better than Arm B on the primary metric **and** clean on fidelity (4) with
no fork required (5). Any fidelity violation is disqualifying regardless of score — the outer
loop is the experiment's control surface and must be exactly the paper's protocol. Otherwise
ship Arm B and keep autoresearch as pattern reference. Either way the losing arm's run stays
in the repo under `docs/experiments/` as evidence.

**Result (2026-07-20): ship Arm B (native `/rsi:step` / `/rsi:run`); keep autoresearch as
pattern reference.** Applying the decision rule to the banked evidence: the primary metric (1)
is a **tie by construction** — the chassis is downstream of scoring, so both chassis make the
identical accept/reject decision on the same eval. The call therefore turns on the
pre-registered structural metrics. Fidelity (4) favors native's single atomic `ledger.jsonl`
append over autoresearch's git commit/revert (sharper failure edges). Friction (5) is decisive
against Arm A: it requires the `metric.txt` shim (the inner eval is Workflow-tool-only, so
autoresearch's shell `Verify:` cannot spawn it — a Workflow-capable agent must stay in the
loop), a git-repo scope, and `AR_DISABLE_*` hook overrides, while native needs none. This
matches the pre-registered a priori expectation and the paper's §5.1/§5.2 finding. Confirmed on
real compute: a paired fresh run drove one eval (`0.570979 < 0.587646` incumbent) to the
identical REJECT in both chassis, plus a keep-path demo (iter-1 `+0.029166`). The full 2×2×10
was **not** needed for the chassis decision — the structural metrics settle it — and remains
optional RSI-dynamics evidence. Full evidence: `docs/experiments/chassis-ab/`
(PRE-REGISTRATION.md, PILOT-RESULTS.md, ARM-A-CHASSIS-DEMO.md, PAIRED-RUN-FINDINGS.md).

**Naming collision**: our standalone inner-agent skill is also named `autoresearch`
(namespaced `rsi-loop:autoresearch` vs. their top-level `autoresearch`). Claude Code
disambiguates by plugin prefix, but if adoption lands in M2 we should rename ours (e.g.
`aide-inner` or `tree-research`) to avoid trigger-description competition in the same session.

## 6. Milestones

- **M0 — placeholder** (this commit): scaffold + this plan.
- **M1 — inner agent + one task**: `baseline/gen-000` Workflow script, heuristic-optimization
  task with public/private scoring, private-dir deny hook, and the standalone `autoresearch`
  skill + `/rsi:autoresearch` command wrapping it. Exit: gen-000 solves the task end-to-end via
  `/rsi:autoresearch` under a token cap; private score computed outside the inner context.
- **M2 — outer step**: proposer + selection + `ledger.jsonl`; `/rsi:init`, `/rsi:step`.
  Includes the §5.2 chassis A/B experiment (outer loop on `uditgoenka/autoresearch` vs. native
  Workflow script — pre-registered metrics and decision rule) — **DONE (2026-07-20)**: results
  landed in `docs/experiments/chassis-ab/`, winner = **Arm B (native)**, shipped as `/rsi:step`;
  the chassis decision turned on the structural metrics (4 fidelity, 5 friction), so the full
  2×2×10 was not required and remains optional. Exit: 3
  manual outer steps produce ≥1 accepted generation on private score.
- **M3 — full protocol** _(DONE — run-002 ran to a plateau stop at 10 ledger steps)_: all
  3 task families (bin-packing, tabular-classification, instruction-routing), verifier + <50% hack
  rule + outlier filter (`scripts/rsi-aggregate.py`), `/rsi:run` with budget accounting. Exit
  criterion (10-step unattended run) **met**: ~37.9M cumulative inner tokens, stopped on 2
  consecutive rejections. As-built outcome — net = **1 accepted improvement** (gen-006, robust
  0.644 → 0.725 under `--seeds 3`) plus **2 negative results** (gen-008 0.696, gen-009 0.546);
  **incumbent = gen-006**. Full evidence in `docs/experiments/run-002/` (10-line `ledger.jsonl`,
  `gen-000/003/004/005/006/007/008/009` dirs, `seeds3-evals/`, `README.md`, `M3-FINDINGS.md`).
- **M4 — measurement** _(measured — Level 0 and Level 1 met; see `docs/experiments/m4-report.md`)_:
  `baseline/gen-human` hand-tuned baseline, `holdout-tasks/` (one per family + a far-OOD
  time-series task), `/rsi:report` (`scripts/rsi-report.py`) with ladder-level evidence
  (improvement slope vs. baseline, generalization deltas, hack-rate trend).
- **M5 — ignition test** _(RUN — Level-2 NOT supported; see `docs/experiments/ignite/README.md`)_:
  `/rsi:ignite` swaps the best generation's strategy into the proposer role and compares campaigns at
  equal budget (the paper's Level-2 test). Step-1 paired A/B (both arms from gen-000, `--seeds 3`):
  mean-of-per-task-medians **control 0.6126 vs ignited 0.5876** — ignited is −0.025 _worse_, a
  measurable regression, not merely the paper's "same-ceiling" wash. Root cause: gen-006's
  adversarial-robustness tie-break probe rides on a public-data battery that carries no discriminating
  signal on the coarse tabular private buckets, so a noisy tie-break is strictly worse than
  greedy-public. Measured honestly, as expected — not passed. **Superseded as a Level-2 test by M6:**
  a post-run design review diagnosed this ignition as a category error (it tests strategy-briefing, not
  compounding) — see M6.
- **M6 — Level-2 re-architecture (isomorphic ignition)** _(LIVE — design COMPLETE; full resolved spec in §6.1; reopens
  Level 2 as a design, not a result)_:
  the M5 ignition is diagnosed as a measurement artifact — the old `/rsi:ignite` injected the incumbent's
  task-solving strategy into a stock proposer and compared campaign _endpoints_, testing "does a
  strategy-briefed proposer beat a stock one," NOT the thing the paper's ignition test actually asks: is the
  discovered inner agent a **better outer agent than its predecessor**, judged on the whole campaign
  **trajectory (convergence rate + asymptote)** rather than a single endpoint — a first-order comparison of
  two outer agents that a 1-step-per-generation endpoint A/B structurally cannot make; the loop also banked
  only ~3 genuine forward meta-steps and never carried the outer optimizer forward, so ignition was
  untestable regardless. M6 adopts the approved **Approach 1 ("isomorphic loops")**: collapse both loops
  onto ONE generic tree-search engine (`search-engine.mjs`) that searches over a POLYMORPHIC artifact — the
  inner instantiation's artifact is a _solution_, the outer's is an _inner-agent scaffold (a generation
  dir)_. Both seats consume the IDENTICAL `policy.json` vocabulary and run the IDENTICAL engine, so
  **promotion becomes a literal lift**: the discovered inner scaffold's policy+prompts drop into the outer
  engine's scaffold slot — impossible in the current split architecture (Workflow `.mjs` inner vs. markdown
  proposer-agent outer), and the whole reason for Approach 1. **Consequence made explicit (arch reconciliation):
  M6 is a FRESH campaign from `baseline/gen-000`; the run-002 lineage (gen-006 etc.) is NOT promoted.** Its
  gains live where Approach 1 deliberately freezes them — inside the mutable `.mjs` engine (gen-006 is +260
  engine lines of Probe machinery) and in 7 policy fields _outside_ the shared vocabulary. Freezing the
  engine and fixing the vocabulary is the price of a literal-`cp` promotion; forfeiting run-002's
  engine-resident incumbent is the acknowledged cost, logged as a deviation (§6.1.5). The corrected ignition
  test then races TWO FULL campaigns from that identical gen-000 start (control: stock greedy outer scaffold;
  ignited: promoted-scaffold outer) measured on **improvement-rate + asymptote trajectory across many
  meta-generations**, NOT endpoint deltas. Documented divergence from strict AIDE² isomorphism (logged with
  reason): AIDE² makes both agents LLM-tree-search over Python code; we keep LLM-driven scaffold edits but
  route them through the same engine/vocabulary substrate — our artifacts are `.mjs`+prompt dirs, not `.py`;
  same policy vocabulary, same promotion semantics. **The make-or-break crux (compute-nesting) and open items
  3–6 are now RESOLVED — concrete spec (miniaturized inner search + enlarged private measurement +
  token-metered binding budget + paired A/B + mandatory Phase-0 power gate, ~$233 ceiling / ~$163 typical) is
  in §6.1 below.** M6 remains a reopening and a design, not a Level-2 result — no new Level-2 claim is made,
  and the expected verdict is NOT-supported (paper parity).

### 6.1 M6 design — isomorphic ignition (resolved)

This is the full resolved M6 spec. It fixes the M5 **measurement** failure (coarse private buckets quantized any real
effect below noise) rather than gating around it, keeps every change on the mutable side of the immutability wall, and
reuses the exact `policy.json` vocabulary so promotion stays a verbatim lift. All five open items (2 compute-nesting, 3
battery, 4 rate rule, 5 promotion, 6 testing/known-positive control) are answered concretely below. Honesty stance is
unchanged: **M6 is a design + a reopening, not a Level-2 result; the prior on the eventual verdict is NOT-supported,
exactly as the paper found ("converged faster, no asymptotic advantage").**

#### The isomorphic engine + polymorphic artifact

Three layers; the loop mutates exactly one:

| Layer                               | Contents                                                                                                                                                                                                                                                                                                                                                  | Loop-mutable?                      | Promoted?                  |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | -------------------------- |
| **Substrate**                       | `search-engine.mjs` — the generic tree-search (drafts → greedy debug/improve → best), factored as a **pure `search(deps, policy, adapter)` core** whose agent-runner, scorer, and budget/RNG arrive through `deps` (see §6.1.6 refactor note); a thin Workflow shim binds the runtime globals (`agent`/`parallel`/`phase`/`budget`) into `deps` at launch | No (immutable harness)             | No                         |
| **Adapter** (seat-fixed launch arg) | artifact kind, artifact-path template, operator write-target, `SCORE_CMD`, public/private/holdout split, deny-hook scope                                                                                                                                                                                                                                  | No                                 | No                         |
| **Scaffold** (portable)             | `policy.json` (the fields the frozen engine reads) + `prompts/{draft,debug,improve}.md`                                                                                                                                                                                                                                                                   | Yes — the search operates on these | **Yes — this IS the lift** |

**Invariant that makes promotion work:** anything that must _differ_ between the inner seat and the outer seat lives in
the **adapter**, never in `policy.json` or the prompts. That is why the scaffold lifts verbatim — it carries nothing
seat-specific. Concrete build requirement: the operator prompts are placeholder-templated (`${ARTIFACT}`,
`${SCORE_CMD}`, `${ARTIFACT_KIND}`), filled by the seat's adapter at launch, so a prompt reads correctly whether
`${ARTIFACT}` is a `solution.py` or a scaffold dir.

**Fixed vocabulary (arch constraint, load-bearing):** the promotable vocabulary is the gen-000 8-field set — but note
today's baseline engine only _reads_ five of them (`num_drafts`, `max_nodes`, `model`, `effort`, `draft_directions`)
and hardcodes `algorithm`, `context_mode`, `selection` (the greedy loop and full-history concatenation are baked in).
Extending the M6 pure `search()` core (§6.1.6) to interpret those three as policy fields is therefore committed
refactor work — a precondition for a literal-`cp` promotion to carry real behavior across all 8 fields, not just 5.
The scaffold search may tune those fields and rewrite the prompts; it may
NOT add engine-actioned fields, because a frozen generic engine cannot act on a field it does not read. This is
precisely why the run-002 lineage is not promoted: gen-006's gains are 7 extra policy fields (`probe_modality`,
`public_tie_band`, `min_spread`, `probe_topk`, `probe_reserve_tokens`, `max_escalations`, `probe_topk_max`) plus ~260
lines of Probe machinery _inside the engine_ — both on the frozen side of this wall.

**Structural polymorphism check (unit test):** the engine source contains zero artifact-type-specific tokens — `grep
-Eiw 'solution|scaffold|task|\.py|generation' search-engine.mjs` returns 0 matches in the search loop. The engine
literally cannot name either artifact type.

**Logged deviation from strict AIDE² isomorphism (with reason):** artifacts are `.mjs`+prompt bundles, not `.py`; AIDE²
tree-searches Python at both seats. We keep LLM-driven scaffold edits routed through the identical engine/vocabulary
substrate — same policy vocabulary, same promotion semantics. The deviation buys a promotion that is a literal `cp`, at
the cost of not editing raw Python at the outer seat **and** of forfeiting any inner improvement that would require
changing the frozen engine or extending the vocabulary (the run-002 incumbent is exactly such an improvement).

---

#### §6.1.2 Compute-nesting resolution (open item 2) — miniaturize search, enlarge measurement, bind token budget

The decisive reframe: **M5 died from a measurement problem, not a compute problem.** LLM node generation is the
expensive thing; private-set size is ~free (deterministic Python scoring). So we decouple them — miniaturize the
_search_ (few nodes, haiku) and simultaneously _enlarge the measurement_ (big graded private sets, item 3) — which cures
the M5 root cause and cuts compute at the same time.

Base unit (measured, run-002): ~55K tokens/inner-node (haiku, low effort, full-history); haiku blended ≈$2/M tokens;
scoring ≈0 LLM tokens.

**Budget mechanism (arch-corrected — the harness meters TOKENS):** the inner stop condition is a **binding per-sub-run
token cap `B_inner`**, not a node counter, reusing the existing `budget.remaining()` token meter (`--budget TOKENS`,
ledger `inner_tokens`). Dollars are a **reporting** conversion only, never a new meter. Two pinned reporting constants
in `rsi-report.py`: inner nodes run on haiku, `PRICE_PER_MTOK ≈ $2/M`; the per-outer-node proposer edit (~0.15M tok)
runs on the **strong outer model** (Opus/Fable session model, §3 — not haiku), priced at `PROPOSER_PRICE_PER_MTOK ≈
$6/M` (blended strong-model input+output). `B_inner ≈ 335K tokens (~$0.67)` per sub-run; a full inner campaign (2 tasks
× 3 seeds = 6 sub-runs) ≈ 2.0M tokens (~$4). Outer score = `best-private-achieved-under-B_inner`. The engine's one loop
primitive at both seats becomes `while (budget.remaining() > estCost) expandNextNode()`, all in tokens, with `estCost` =
trailing-max node **token** cost (never mean, so a runaway proposal can't overshoot). This gives efficiency a gradient:
best-of-N and parallelization-spam exhaust `B_inner` without improving per-token yield, so **they cannot be the winning
move at equal budget** (the paper's "must not pass") — a real gain must _beat_ the best-of-N baseline under the same
cap, not merely be permitted. **Tune `B_inner` so the incumbent spends 80–90% of it (the budget must bind).**

| Nest depth         | Knob               | Full-real             | **Committed miniature**                             | Why                                                                           |
| ------------------ | ------------------ | --------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------- |
| 0 — inner node     | model/effort       | haiku/low             | **haiku/low**                                       | already the floor                                                             |
| 1 — inner campaign | stop condition     | 9 nodes               | **`B_inner`≈335K tok/sub-run (~2.0M tok/campaign)** | token cap binds; brute force can't win                                        |
| 1                  | selection families | 3                     | **2 pre-screened discriminating**                   | M5: 2 of 3 carried zero differentiating signal                                |
| 1                  | private set        | coarse 8ths / 32 inst | **≥50 graded instances/task** (item 3: 120–400)     | resolution ~0.02 vs ~0.125 → the anti-M5 fix, ~free                           |
| 1                  | seeds              | 3 (42/43/44)          | **3**                                               | now powered because per-seed SE dropped with the enlarged set                 |
| 2 — outer campaign | meta-gens `G`      | 8–10                  | **8** (num_drafts 3 + 5 search)                     | 8 points fit early slope + late plateau; `G≥4` hard floor (need a 3-gen tail) |
| 3 — ignition A/B   | design             | —                     | **paired, R reps** (from staged-fidelity graft)     | pairs cancel seed noise → power at far fewer reps                             |

_(Nest-depth labels are architectural nesting only; they deliberately do NOT reuse the paper's RSI-ladder rungs L0–L3 —
the ignition A/B at nest depth 3 tests the paper's **Level 2**, not Level 3.)_

**Budget arithmetic (committed; tokens primary, dollars = reporting conversion):**

| Unit                                      | Composition                                                            | Tokens    | Cost      |
| ----------------------------------------- | ---------------------------------------------------------------------- | --------- | --------- |
| Inner node                                | 1 draft/debug/improve + score (haiku)                                  | ~55K      | ~$0.11    |
| Inner campaign = **1 outer node's score** | 2 tasks × 3 seeds, token-capped (haiku)                                | ~2.0M     | **~$4**   |
| Outer node (loaded)                       | inner campaign ($4 haiku) + proposer edit (0.15M strong @ $6/M ≈ $0.9) | ~2.15M    | ~$4.9     |
| Outer campaign (1 arm, 1 rep)             | 8 meta-gens × outer node                                               | ~17.2M    | **~$39**  |
| **Paired A/B, R=3**                       | 2 arms × 3 paired reps = 6 × outer campaign                            | **~103M** | **~$233** |

_Dollar rows use haiku $2/M for inner nodes + strong-proposer ~$6/M for the per-node edit; tokens are the real meter._

Spend is **phased, power-gated before verdict** (the M5 covenant): **Phase-0** instrument power gate ~$8 (§6.1.6);
**Phase-1** paired pilot R=2 = 4 campaigns × ~$39 ≈ ~$155 (total with Phase-0 ~$163, where most runs stop); **Phase-2**
add R=3 only if within noise → ~$233 ceiling. The **paired** design (control and ignited share start artifact + seed
sequence per replicate) is what keeps R low: a 2-pair pilot confirming paired-SD ≤ 0.04 buys ~80% power without chasing
independent-arm variance.

**Reconciliation note (deviation-with-reason, committed shape governs):** open item 3's resolver kept all 3 families in
the battery; the funded compute-nesting shape selects on **2 pre-screened discriminating families**. Reconciled into a
clean three-tier that mirrors the inner loop: **2 selection families drive outer search**; the **third family
(instruction-routing) is the outer-private survival signal** (off-search, read each outer generation to decide scaffold
acceptance — the outer analogue of the inner public/private split); and **`holdout-tasks/`** (one per family + the
far-OOD time-series) stays **untouched, scored once at `/rsi:report`** for the generalization verdict. This preserves
heterogeneity anti-hack pressure (2 selection families, not 1), gives survival a real held-out signal, and keeps a
genuinely untouched probe for generalization — honoring the M5 lesson that a signal-free family only dilutes power.

#### §6.1.3 Non-saturating battery + real generalization gap + budget pressure (open item 3)

Reshape splits, do not invent families. Scorers stay immutable (they mean over instances/buckets and absorb larger N);
the only new code is one generator plus a `--power-check` mode on `rsi-aggregate.py`.

| Family (role)                                                               | pub N          | priv N           | honest floor | honest ceiling | priv SE | non-saturating mechanism                                                                              |
| --------------------------------------------------------------------------- | -------------- | ---------------- | ------------ | -------------- | ------- | ----------------------------------------------------------------------------------------------------- |
| tabular-classification (ML-eng) — **selection**                             | 200            | **400** (was 80) | 0.44         | 0.92           | ~0.015  | 4% irreducible label noise caps < 1.0                                                                 |
| bin-packing (heuristic-opt) — **selection**                                 | **40** (was 5) | **120** (was 7)  | 0.55         | 0.96           | ~0.02   | ~30% pathological size mixes strand capacity                                                          |
| instruction-routing (harness-eng) — **outer-private survival (off-search)** | 60             | 160              | 0.60         | 0.90           | ~0.024  | adversarial arg-distribution shift (ties, indexing, whitespace, unicode) breaks a public-tuned parser |

- **Generalization-gap contract (the anti-noise fix):** each family draws public/private from the same generator,
  different draws, shifted on the one axis separating memorization from generalization (fresh rows / harder args /
  different size regimes). **Honest gap** `honest_public − honest_private < 0.05`; **hack gap** for a public-overfit
  hard-coder `> 0.30`. Both measured at SE ≤ 0.025/task, so the gap no longer collapses into noise as it did on M5's
  coarse tabular buckets and 7-instance bin-packing.
- **Power gate (`rsi-aggregate.py --power-check`, precondition for ANY verdict):** asserts (1) each
  **selection-family** task's private aggregate SE ≤ **0.02** (bootstrap over private instances; the two
  verdict-driving families — the off-search survival family is held to the ≤ 0.025 gap contract above) and (2) a
  planted true Δ = **0.03** between two synthetic
  scaffolds is rejected at α = 0.05 by a paired bootstrap over pooled private instances. If either fails, the verdict is
  "underpowered — inconclusive," never "not supported." This is the exact check M5 skipped. (`--power-check` is the
  battery-resolution precondition — a property of the private splits, so it lives on the aggregator that already
  bootstraps them; moving it would duplicate that bootstrap. The ignition-**instrument** power calc — MDE/K given σ_d —
  lives in `rsi-ignition.py power`, §6.1.6.)
- **Budget-as-selection knob:** reuse existing `--budget TOKENS` (cumulative inner tokens from ledger `inner_tokens`);
  per-eval brute force is capped by `B_inner` (§6.1.2). `rsi-report.py` gains `tokens_to_best`. Efficiency
  (private-per-token) is deliberately NOT computed yet (YAGNI — it gates no verdict; add when a report consumes
  it); the honesty point it encodes is already enforced by §6.1.4's verdict table: equal-asymptote-at-fewer-tokens
  is the `|ΔA|<MDE` NO_RESULT row, never a win. Only a strictly higher sustained asymptote (§6.1.4) can produce
  SUPPORTED.
- **Files:** regenerate `tasks/tabular-classification/make_data.py` (`gen(400)` private) and
  `tasks/instruction-routing/make_data.py` (hard-arg private); **new** `tasks/bin-packing/make_data.py` (seeded
  generator, 40/120 graded); add `--power-check` to `rsi-aggregate.py`; add `tokens_to_best` to
  `rsi-report.py`. `score.py` (all 3) and the `policy.json` schema are untouched. Regenerated `instances.json`
  re-anchored to git HEAD (content-checked by `rsi-check-integrity.sh`).

#### §6.1.4 Rate decision rule (open item 4)

Two full campaigns from the identical `gen-000` baseline differing only in the outer scaffold slot: **control** (stock
gen-000 policy+prompts) vs **ignited** (promoted policy+prompts), paired across seeds 42/43/44, `G = 8`
meta-generations. New dir `docs/experiments/ignite-m6/{PREREG.md, progress.jsonl, trajectories.json, verdict.json,
README.md}`; new `scripts/rsi-ignition.py` (subcommands `decide` + `power`; reuses `rsi-aggregate.py`; does not
re-implement median logic).
`PREREG.md` is git-committed **before** any eval spend.

- **Best-so-far curve** `B(g) = max(pa(1..g) of accepted generations)`, `B(0) = gen-000 baseline` (monotone; a rejected
  candidate never lowers it — the campaign trajectory the paper compares).
- **Asymptote** `A = mean(B(G-1), B(G))` (mean-of-last-2 damps a lucky final accept — the gen-005 0.856→0.644 failure
  mode). **Rate** `R = (1/G)·Σ (B(g) − B(0))` — corroborative only, can never alone produce SUPPORTED.
- Paired per-seed deltas `ΔA_s`, `ΔR_s`; point estimates `ΔA = median_s ΔA_s`, `ΔR = median_s ΔR_s`. **Sustained** check
  over the tail `{G-2, G-1, G} = {6,7,8}`: `B_ignited(g,s) − B_control(g,s) ≥ MDE` for all tail g, all seeds.
- **Significance (n=3 is too small for a t-test — don't pretend):** two honest gates. (a) **Effect size vs measured
  noise:** the governing threshold is the canonical power-form MDE from §6.1.6, `MDE(K) = 2.487·σ_d/√K`, evaluated at
  the run's actual K (default K=3 → **0.072**); `σ_d` = the control-vs-control paired SD of `ΔA` (measured via
  `--calibrate`, planning value ≈0.05, N_null ≥ 5). SUPPORTED requires `ΔA ≥ MDE(K)`. (b) **Sign consistency:**
  one-sided sign test on paired `ΔA_s` — n=3 all-same-sign p = 0.125 (gate at n=3); escalate to seeds 42–46 → 5/5 p =
  0.031.
- **Power precondition (hard-gated, the M5 lesson):** the planted known-positive effect (§6.1.6) must exceed `MDE(K)` on
  this instrument — the §6.1.6 control clears it at 0.15 ≫ MDE(3)=0.072. If the instrument can't resolve its own planted
  positive at the run's K, the run is `NO_RESULT` regardless of the arms. (Resolving a 0.025-scale effect instead needs
  K≈25 — see the §6.1.6 seed table; that is a budget decision made up front, not a gate imposed at planning.)

| Verdict       | Condition                                                                                                                                                                                                                                                                                                                                                                            | Meaning                                                                              |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| **SUPPORTED** | `ΔA ≥ MDE` AND all seeds `ΔA_s > 0` (sign test ≤ α) AND sustained for all seeds AND `ΔR ≥ 0`                                                                                                                                                                                                                                                                                         | Ignited reaches a strictly higher, sustained plateau — Level 2 clears                |
| **REFUTED**   | `ΔA ≤ −MDE` (or within ±MDE while `ΔR ≤ −MDE` — faster-losing)                                                                                                                                                                                                                                                                                                                       | Ignited plateau measurably worse                                                     |
| **NO_RESULT** | power precondition fails; **or** `\|ΔA\| < MDE` (within noise — _the paper's actual outcome:_ `ΔR>0` with `\|ΔA\|<MDE` ⇒ Level 2 not claimed = "converged faster, no asymptotic advantage"); **or** `ΔA ≥ MDE` while `ΔR < 0` (higher plateau reached only via a late jump while converging slower — not a clean ignition, report as inconclusive); **or** sign/sustained gate fails | Instrument couldn't resolve a clean asymptote win — Level 2 not supported, ≠ refuted |

**Stated honestly up front:** NO*RESULT (paper parity) is the prior; `ΔR > 0` with `|ΔA| < MDE` is a scientifically
clean not-supported and must be reported as such — it is the SAME outcome as "converged faster at equal asymptote," so
an efficiency edge (§6.1.3) can accompany it without ever upgrading the verdict. Note M5's −0.025 sits \_inside* the
±MDE(3)=0.072 band (|−0.025| < 0.072) → at this instrument's resolution M5 was NO_RESULT-on-asymptote, the honest
restatement of why its endpoint delta was a category error. `rsi-ignition.py decide` ships with a runnable self-check
planting four synthetic trajectory sets (flat +0.10 → SUPPORTED; faster-same-plateau → NO_RESULT; −0.10 plateau →
REFUTED; σ_d=0.08 with real ΔA=0.10 → NO_RESULT power-fail).

**Reconciliation note:** item 4's draft froze `G=6`; the committed shape (§6.1.2) and the power controls (§6.1.6) use
`G=8`, so the tail is `{6,7,8}` and `G≥4` is the hard floor. No curve-fit — best-so-far + mean-of-last-2 is robust at
n≤5 seeds; upgrade to a saturating-curve asymptote fit only if `G` is later raised past ~10.

#### §6.1.5 Promotion mechanics (open item 5) — literal policy+prompt lift, fixed vocabulary, zero new fields

The `policy.json` vocabulary is unchanged and shared verbatim by both seats; `baseline/gen-000/policy.json` is already a
valid outer policy. The promotable fields are exactly the 8 the frozen engine reads (arch constraint, §6.1). Field map
(outer-seat interpretation):

| Field              | Outer-seat meaning                                                                                                                                                                                     | Class                  |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------- |
| `algorithm`        | engine search mode, identical both seats (`aide0-greedy-tree-search`)                                                                                                                                  | direct                 |
| `num_drafts`       | # parallel draft **scaffold-mutations** at root                                                                                                                                                        | direct (cost-capped)   |
| `max_nodes`        | outer search budget in nodes — **the expensive knob** (each outer node = one full inner campaign); lifts verbatim, harness ceiling may clamp                                                           | direct                 |
| `model`            | model of the operator that _edits the artifact at this seat_ (outer: writes scaffold edits); distinct from a scaffold's own `policy.model` one level down                                              | direct (level-shifted) |
| `effort`           | that operator's reasoning effort                                                                                                                                                                       | direct                 |
| `context_mode`     | same semantics; referent = scaffold-nodes (prior mutations, their outer-public scores, rationales)                                                                                                     | reinterpreted referent |
| `selection`        | same rule on the **outer-public** signal; `greedy-public` = greedy on the scaffold's inner-campaign private-aggregate over the **selection** battery                                                   | reinterpreted referent |
| `draft_directions` | same field/type; content names scaffold-mutation axes (context engineering, selection rule, node-budget split, verification steps); outer gen-000 ships a scaffold-flavored default of the same length | reinterpreted content  |

**New fields: none — and none permitted** (the frozen engine cannot act on fields it does not read; §6.1).
Public/private/holdout split and artifact kind are adapter concerns (launch args), deliberately kept OUT of
`policy.json` — a `"seat"` field would poison promotion. **This is also why the run-002 incumbent is not the promoted
scaffold:** gen-006 carries 7 out-of-vocabulary fields plus an engine-resident Probe phase, neither of which a frozen
generic engine can interpret. M6 re-derives from gen-000 within this vocabulary; whether the 8-field vocabulary can
recapture a gen-006-class gain is an open empirical question the M6 inner campaign answers — and if it cannot, that is a
legitimate (paper-consistent) not-supported outcome, not a spec failure.

**Outer-seat split (reuses the existing battery, three-tier per §6.1.2):** outer-public (drives outer search +
`selection`) = the scaffold's inner-campaign private-aggregate on the 2 **selection** families, `--seeds 3`,
mean-of-per-task-medians via `rsi-aggregate.py --aggregate` (inner-private is _public to the `RSI_OUTER_LOOP=1` outer_;
the deny hook still gates inner agents, which never see `--private`). Outer-private / true survival objective (decides
scaffold acceptance each outer generation) = the scaffold's score on the **third family (instruction-routing)**.
Generalization verdict = the untouched **`holdout-tasks/`** (one per family + far-OOD time-series), scored once at
`/rsi:report` — catching the outer analogue of the M5 overfit.

**The lift (fresh from gen-000; no `outer-seat/` subdir — the gen dir is flat):** `baseline/gen-000` serves as BOTH the
inner seed artifact AND the outer **control** operating scaffold (no separate outer gen-000). The best discovered inner
scaffold is the M6 inner campaign's last accepted generation's `{policy.json + prompts/}` bundle — discovered under the
frozen engine, NOT the run-002 lineage.

```bash
SRC=<source-run>/best-scaffold                 # last accepted M6 inner generation (frozen-engine)
/rsi:init <run>/ignite/arm-control             # outer scaffold = baseline/gen-000 (stock), flat dir
/rsi:init <run>/ignite/arm-ignited             # outer scaffold = baseline/gen-000 (stock), flat dir
cp    "$SRC/policy.json"  <run>/ignite/arm-ignited/policy.json      # THE LIFT
cp -r "$SRC/prompts/."    <run>/ignite/arm-ignited/prompts/
/rsi:run <run>/ignite/arm-control  --max-steps 8 --budget B --seeds 3 --plateau 0
/rsi:run <run>/ignite/arm-ignited  --max-steps 8 --budget B --seeds 3 --plateau 0
```

The **only** difference between arms is the bytes of `arm-ignited/{policy.json, prompts/*}`; engine, adapter, battery,
seeds, budget, verifier, deny hook are byte-identical. This _replaces_ the M5 `ignite/strategy-brief.md` prose-injection
seam (which tested strategy-briefing, not compounding) with a real policy+prompt lift — the reason M6 exists.
`commands/rsi-ignite.md` step 2's seam becomes the `cp` lift above; `/rsi:init` already produces the flat generation dir
the lift targets (no new directory contract needed).

#### §6.1.6 Testing + known-positive control + demonstrated power (open item 6)

**Required refactor (arch, load-bearing — stated, not assumed):** today the engine calls Workflow globals
(`agent`/`parallel`/`phase`/`budget`) directly, so it cannot be unit-tested cheaply. M6 factors it into a **pure
`search(deps, policy, adapter)` core** (agent-runner, scorer, budget/RNG passed via `deps`) plus a thin Workflow shim
that binds the runtime globals into `deps` at launch. Only the pure core is tested and promoted-over; the shim is a few
lines and stays in the immutable substrate. The pure core must also _read_ `algorithm`, `context_mode`, and
`selection` from `policy` (today hardcoded), so all 8 vocabulary fields are engine-interpreted and promotion is
behavior-complete. This refactor is the precondition for the <1s deterministic tests and for
the Phase-0 power gate running without nested LLM cost — it is committed work, not a free property.

With that core, the polymorphism test, known-positive control, and negative control all run in <1s with zero
LLM/nested-compute cost by injecting deterministic closures via `deps`. Four new files, all in `make test-skills` + CI's
`rsi-loop` job (no new deps):

| File                                     | Role                                                                                                                                                                                                                                                                |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tests/test-engine-polymorphism.sh`      | run `search()` twice, one policy+seed, two stub adapters (`solutionStub`, `scaffoldStub`) via `deps`; assert identical draft count, `max_nodes` cap, node-ledger key set, greedy pick, debug routing on a `buggy:true` stub, and the grep-zero structural invariant |
| `tests/fixtures/synthetic-landscape.mjs` | deterministic unimodal seed-noised scorer using the engine's Lehmer RNG (no `Math.random`): `s(θ,seed,node)=1−(θ−0.8)²+ε`, mock `propose` steps halfway toward θ\*=0.8                                                                                              |
| `tests/test-ignition-instrument.sh`      | three controls at K=3 (below)                                                                                                                                                                                                                                       |
| `scripts/rsi-ignition.py`                | ignition stats: `decide` (verdict) + `power` (MDE/K_req/`--calibrate`) subcommands                                                                                                                                                                                  |

**Known-positive control (proves the instrument has power):** two outer policies over the synthetic landscape, differing
only in FIXED-schema knob values (proving promotion is a literal policy lift): **stock** `num_drafts=2, max_nodes=4` vs
**rigged-better** `num_drafts=8, max_nodes=12`. Same operator, so rigged-better is provably the stronger outer
optimizer; realized asymptote gap tuned to ≈0.15. Three assertions:

1. **POSITIVE** — effect 0.15, σ_d≈0.05 ⇒ MDE(3)=0.072; 0.15 ≫ 0.072 → **must return IGNITION**.
2. **NEGATIVE** — promoted == stock (effect 0), noise on → **must return NO IGNITION** (guards the M5
   signal-free-verdict failure).
3. **UNDERPOWERED/HONESTY** — effect 0.03 (M5-scale), MDE(3)=0.072 > 0.03 → **must return INCONCLUSIVE**, not a false
   IGNITION (the exact scenario M5 mishandled).

**Power quantified** (`rsi-ignition.py power`, paired one-sided, α=0.05, power 0.80 ⇒ constant 2.487): `MDE(K) =
2.487·σ_d/√K`, `K_req(effect) = ceil((2.487·σ_d/effect)²)`; `σ_d` **measured** via `--calibrate` (control-vs-control),
planning value ≈0.05.

| K (seeds)   | MDE (min detectable asymptote gap) |
| ----------- | ---------------------------------- |
| 3 (default) | **0.072**                          |
| 5           | 0.056                              |
| 10          | 0.039                              |
| **25**      | **0.025**                          |

The M5 lesson, quantified: M5's point estimate −0.025 (itself inside the noise band) ran at K=3 (MDE 0.072) —
underpowered ~3× for any sub-0.072 effect. Resolving a 0.025-scale effect needs **K ≈ 25**. `--calibrate` prints
`K_req(target_effect)` on the real battery
so the real ignition run is declared INCONCLUSIVE _before_ spending if the budget can't fund the required seeds — the
honest non-claim is made up front, not after a wasted campaign.

**`ponytail:` fixed G=8/nest-depth-3/tail={6,7,8}, two literal adapters, no adapter registry/factory, no
successive-halving proxy machinery — best-so-far + mean-of-last-2 + paired sign test is the whole instrument; upgrade
only if G later exceeds ~10.**

## 7. Risks / open questions

- **Compute-nesting tension (M6, resolved — §6.1.2)**: Approach-1 isomorphism makes each outer node's score a full inner
  campaign (3-level nesting). This is settled by **miniaturizing the search while enlarging the measurement**: haiku
  inner model, a binding per-sub-run **token** cap `B_inner` (~335K tok/sub-run, ~2.0M tok/campaign ≈ $4, tuned so the
  incumbent spends 80–90%; dollars are a reporting conversion, the harness meters tokens), 2 pre-screened discriminating
  selection families with ≥50 graded private instances each, `--seeds 3`, `G=8` outer meta-gens, a **paired**
  control-vs-ignited A/B — full envelope ~$233, most runs ~$163 (phased, Phase-0 power-gated). Residual risks now
  bounded and named: a 2-family selection battery re-opens some overfitting pressure (fenced by the third family as
  outer-private survival signal + untouched far-OOD holdout at `/rsi:report`); the engine must first be factored into a
  pure `search(deps,…)` core (arch-required, §6.1.6); and if `--calibrate` shows the smallest interesting effect needs
  K≫3 seeds, the run is declared INCONCLUSIVE **before** spend rather than over-claimed.
- **Lineage forfeit (M6, named — §6.1.5)**: Approach 1 freezes the engine and fixes the 8-field vocabulary, so run-002's
  incumbent (gen-006: ~260 engine lines of Probe machinery + 7 out-of-vocabulary policy fields) is **not** promotable
  and M6 re-derives from `gen-000`. Whether the fixed vocabulary can recapture a gen-006-class gain is an open empirical
  question; a "no" is a paper-consistent not-supported outcome, not a spec failure. The alternative (widening the
  promoted scaffold to include the engine) is rejected because it kills the immutable-substrate / grep-zero invariant
  that makes promotion a literal `cp`.
- **Cost (M6, bounded — §6.1.2)**: even miniaturized, each outer node = a full inner campaign, so the paired A/B is the
  dominant spend. Mitigations are committed and quantified: haiku inner model, binding **token** budget (not a node
  counter — brute force can't win at equal budget), enlarged-but-free deterministic private sets, and a Phase-0
  known-good-delta gate (~$8) that must detect a planted gen-002 > gen-000 before any A/B budget is released. Honest
  residual: R=3 paired reps × 8 meta-gens detects only **large** ignition effects (the paper's own "no asymptotic
  advantage" null is the expected outcome); a subtle sub-MDE asymptote edge is correctly unclaimable, and escalation
  past ~$233 is authorized only if the pilot shows a calibrated, gate-clearing signal.
- **Eval noise vs. tiny tasks**: small privates make accept/reject noisy; use multiple seeds per
  task and require the paper's "sustained, multi-step" trend, not single jumps. _As-built (run-002):_
  confirmed — a single-seed headline (gen-005 0.856) collapsed to 0.644 under `--seeds 3`
  (42/43/44) on mean-of-per-task-medians; the robust protocol is now the selection default.
- **Harness phantom-node gap** _(known, unfixed — future work)_: `inner-agent.workflow.mjs` records
  a node from the agent's self-reported public score without verifying `solution.py` exists on disk,
  so the top-public fallback can name a phantom (missing-file) node (hit once, bin-packing, gen-007).
  Fix belongs in a future generation — never edit the immutable harness mid-run.
- **Reward hacking of _our_ harness**: inner agents run with tool access; the deny hook +
  immutable-harness boundary is critical and needs its own tests (try to read `private/` from an
  inner agent; must fail).
- **Wall-clock**: multi-day unattended runs in ephemeral sessions need Routines/`send_later`
  re-entry and a resumable ledger (Workflow resume covers the intra-step case).
- **Honest claims**: like the paper, Level 1 is the target claim, Level 2 is a test we run, not
  a result we assume.
