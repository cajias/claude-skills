# rsi-loop — Implementation Plan

Faithful re-implementation of Weco's **AIDE²** recursive self-improvement (RSI) method as a
Claude Code plugin, built from skills, commands, subagents, and the built-in Workflow
orchestrator.

Primary sources:

- explainx summary: <https://explainx.ai/blog/weco-aide2-recursive-self-improvement-rsi-ladder-july-2026>
- Weco first-party report: <https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement>
- RSI ladder definition: <https://www.weco.ai/blog/4-levels-of-recursive-self-improvement>

Status: **M1–M2 implemented** (standalone inner agent, outer step, one completed run); M3–M5
still to build. This document is the build spec; where the shipped code has diverged from it,
the deviation is noted inline and in [CONTINUATION.md](CONTINUATION.md). A full as-built
reconciliation is scheduled for M5.

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
   eval set (can reuse this repo's `.claude/evals` + `scripts/test-skills.sh` conventions);
   private = unseen eval cases. (The self-referential family from the paper.)

`holdout-tasks/`: one unseen task per family plus one far-OOD task (WeatherBench-2 analog —
e.g. a time-series forecasting mini-task from a different domain). Scored only by
`/rsi:report`, never during the loop.

## 5. Third-party skills / components we can leverage

Nothing existing implements bi-level RSI as a skill — searched the claude.ai plugin catalog
(no hits for self-improvement/prompt-optimization/eval-harness) and known marketplaces. But we
can compose substantial existing pieces rather than build from scratch:

| Component                                              | Source                                                                                             | What we reuse                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **autoresearch**                                       | [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) (MIT, 5.3k★, active)         | Candidate **outer-loop chassis** — see §5.1. Its core loop (modify → mechanical verify → keep/discard, auto-revert, git-as-memory, TSV ledger, guard commands, plateau detection via `/autoresearch:evals`) is exactly the outer step's shape. Not usable as the inner agent. |
| **Workflow tool**                                      | Claude Code built-in                                                                               | The entire orchestration substrate: deterministic loops, `parallel()` fan-out, per-agent `model`/`effort` overrides (model asymmetry), `budget` (fixed-budget constraint), structured-output schemas (scores), journals (transcripts). Both loops are Workflow scripts.       |
| **skill-creator**                                      | Anthropic (official)                                                                               | Skill authoring + its eval/benchmark harness — used to build the harness-engineering task family and to validate rewritten generations structurally.                                                                                                                          |
| **deep-research**                                      | Claude Code built-in                                                                               | Pattern reference for the verifier stage (adversarial claim-checking before accepting results). Not reusable as the inner agent: it does web research (search → verify → cited report), not experiment-driven autoresearch (code → run → score → iterate).                    |
| **ralph-loop**                                         | Geoff Huntley's ralph technique (already referenced in this repo's `skills/ralph-loop-invocation`) | Prior art for long-running loop-until-done outer iteration with max-iterations + completion promise; `/rsi:run` follows the same invocation ergonomics.                                                                                                                       |
| **/loop** (built-in) + `send_later`/Routines           | Claude Code built-in                                                                               | Multi-day unattended outer-loop pacing — the paper's 8-day unattended run maps to scheduled wakeups re-invoking `/rsi:step`.                                                                                                                                                  |
| **claudeception, session-mining**                      | this repo                                                                                          | Complementary, not core: mine accepted-proposal rationales from transcripts into reusable skills (a human-digestible byproduct the paper doesn't have).                                                                                                                       |
| **scripts/validate.sh, test-skills.sh, .claude/evals** | this repo                                                                                          | Structural gate every proposed generation must pass before spending eval budget.                                                                                                                                                                                              |
| **DSPy / GEPA, OpenEvolve (AlphaEvolve OSS)**          | Python libraries, not skills                                                                       | Pattern reference only (evolutionary prompt/code optimization, keep-if-better + lineages). We replicate natively; no dependency.                                                                                                                                              |

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
  Workflow script — 2×2 paired runs, pre-registered metrics and decision rule); results land in
  `docs/experiments/` and the winner becomes `/rsi:step`. Exit: 3
  manual outer steps produce ≥1 accepted generation on private score.
- **M3 — full protocol**: all 3 task families, verifier + <50% hack rule + outlier filter,
  `/rsi:run` with budget accounting. Exit: 10-step unattended run with sane ledger.
- **M4 — measurement**: `gen-human` hand-tuned baseline, `holdout-tasks/`, `/rsi:report` with
  ladder-level evidence (improvement slope vs. baseline, generalization deltas, hack-rate trend).
- **M5 — ignition test**: `/rsi:ignite` swaps the best generation's strategy into the proposer
  role and compares campaigns at equal budget (the paper's Level-2 test — expect, like Weco, to
  measure it honestly rather than to pass it).

## 7. Risks / open questions

- **Cost**: even miniaturized, each outer step = full battery evaluation. Mitigations: haiku
  inner model, tiny tasks, hard token caps, structural pre-gate before spending eval budget.
- **Eval noise vs. tiny tasks**: small privates make accept/reject noisy; use multiple seeds per
  task and require the paper's "sustained, multi-step" trend, not single jumps.
- **Reward hacking of _our_ harness**: inner agents run with tool access; the deny hook +
  immutable-harness boundary is critical and needs its own tests (try to read `private/` from an
  inner agent; must fail).
- **Wall-clock**: multi-day unattended runs in ephemeral sessions need Routines/`send_later`
  re-entry and a resumable ledger (Workflow resume covers the intra-step case).
- **Honest claims**: like the paper, Level 1 is the target claim, Level 2 is a test we run, not
  a result we assume.
