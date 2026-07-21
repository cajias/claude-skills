# Continuation state — rsi-loop implementation

Snapshot for resuming the KICKOFF.md build in a fresh session. Everything needed lives in
this repo; the scratchpad run directory is ephemeral and fully reconstructable from
`docs/experiments/run-002/` (the current run; `run-001/` mirrors the earlier M2 campaign).

## Where the build stands (2026-07-20 — banked)

- **M1 — done** (`docs/experiments/m1-smoke-bin-packing.md`): gen-000 verified end-to-end;
  `/rsi:autoresearch` live.
- **M2 — exit criteria met** (`docs/experiments/run-001/README.md`): 3 manual outer steps,
  gen-002 accepted (private 0.9405 > 0.9379), steps 1 and 3 rejected with recorded diagnoses.
- **M3 — code complete; exit run demonstrated** (`docs/experiments/run-002/`): three-family
  battery, `scripts/rsi-aggregate.py`, `/rsi:run` driver. run-002 ran 4 steps with a complete
  diagnose→repair→improve arc (gen-003 rejected → gen-004 accepted → gen-005 accepted, private
  aggregate 0.575 → **0.856**). Banked at step 3; the ≥10-step target (steps 4–10) is optional
  extra evidence, not a blocker.
- **M4 — MEASURED** (`docs/experiments/m4-report.md`): Level 0 and Level 1 both met; gen-005
  beats the hand-tuned `gen-human` baseline 0.588 by +0.269; holdout near-transfer mean Δ +0.279,
  far-OOD Δ −0.016 (reported separately). Real `/rsi:report` output committed.
- **M5 — MACHINERY BUILT** (`commands/rsi-ignite.md`): `/rsi:ignite` Level-2 swap test. The
  real ignition campaign is **not yet run** (see "How to continue").
- **§5.2 chassis A/B — RESOLVED (2026-07-20)** (`docs/experiments/chassis-ab/`): ship **Arm B**
  (native `/rsi:step` / `/rsi:run`); keep autoresearch as pattern reference. Decided on the
  pre-registered structural metrics via a paired run + the Arm A chassis demo (not the full
  2×2×10). See "§5.2 chassis decision" below.
- Tests all green in CI (`test-rsi-loop`): deny-hook, scorer, integrity, aggregate, report.

## How to continue (from the banked state)

The scientific core is proven and committed (M1–M4), and §5.2 is decided. Two optional real-compute
runs remain, each an independent multi-hour Workflow job; neither depends on the other. Both are
driven from the committed run-002 evidence — the scratchpad run dir is ephemeral and reconstructable
from `docs/experiments/run-002/` (ledger + `gen-000/003/004/005` generation dirs + winning-node
snapshots). Rebuild it, then:

1. **M3 steps 4–10 (extend the ladder).** Continue run-002 from step 4 with incumbent **gen-005**.
   The next proposer's clearest target is **tabular-classification**, whose private score is stuck
   at **0.7875** across every generation (gen-000→005) — likely because gen-005's adversarial probe
   generates paraphrase perturbations that cannot discriminate ML-model candidates on a 5-fold-CV
   task; a data-perturbation probe mode (feature noise / row resampling / mild shift) is the
   hypothesis to try. Drive with `/rsi:run <run-dir> --max-steps 10`.
2. **M5 — `/rsi:ignite <run-dir>`.** Paired A/B of two full 8-step campaigns (control vs a
   proposer briefed with gen-005's discovered strategy), ~48 evals. The paper found a Level-2
   _rejection_ (faster convergence, same ceiling) and the command is instrumented to measure that
   honestly, not to pass — expect to document a known-negative.

**§5.2 chassis A/B — DONE** (was item 3). Ship **Arm B** (native `/rsi:step` / `/rsi:run`); keep
autoresearch as pattern reference. Full evidence in `docs/experiments/chassis-ab/`.

Do NOT fabricate any eval score — every ledger line must come from real Workflow compute or be
clearly marked not-yet-run. Operational gotchas for whoever runs these are in the sections below.

## §5.2 chassis decision — RESOLVED (2026-07-20): ship Arm B

**Verdict: ship Arm B (native `/rsi:step` / `/rsi:run`); keep autoresearch as pattern reference.**
Evidence committed under `docs/experiments/chassis-ab/` (PRE-REGISTRATION.md, PILOT-RESULTS.md,
ARM-A-CHASSIS-DEMO.md, PAIRED-RUN-FINDINGS.md + `pilot/`, `arm-a-chassis-demo/`, `paired-run/`).

Why the decision holds without the full campaign: the chassis is **downstream of scoring**, so
both chassis make the **identical** accept/reject decision on the same eval — the primary metric
(best `private_aggregate`) is **chassis-invariant by construction**. The decision therefore turns
on the pre-registered **structural** metrics: fidelity (metric 4) favors native's single atomic
ledger-append over autoresearch's git commit/revert (which had a caught exit-code bug); friction
(metric 5) is decisive — Arm A requires the `metric.txt` shim (the inner eval is Workflow-tool-only,
so autoresearch's shell `Verify:` can't spawn it — a Workflow-capable agent must stay in the loop),
a git-repo scope, and `AR_DISABLE_*` hook overrides, while native needs none. This matches the
pre-registered a priori expectation and the paper's §5.1/§5.2 finding.

Empirically confirmed on real compute: a paired fresh run drove ONE eval result (0.570979 <
baseline 0.587646) to the identical REJECT in both chassis (native score-gate reject; Arm A git
revert `4322a8f`), and the earlier keep-path demo showed the accept branch (iter-1 keep +0.029166).

The DECISION was reached via that **paired run** (which isolates the chassis) plus the Arm A chassis
demo. The full 2×2×10 (2 arms × 2 reps × 10 steps ≈ 40 evals, ~20M tokens, ~20h) was **NOT needed**
for the chassis decision — it would only add RSI-dynamics data (repair stabilization, score/token
slope, harness overhead at scale) — so it is now **OPTIONAL, not pending**. Do NOT fabricate any
eval score — every ledger line must come from real Workflow compute or be clearly marked not-yet-run.

## RUN STATUS (2026-07-19): run-002 at step 3, incumbent gen-005

The M3 exit run is live in scratchpad (`rsi-runs/run-002`, evidence mirrored to
`docs/experiments/run-002/`). Steps done, on the 3-family battery:

- step 0 — gen-000 baseline, private aggregate **0.575** (bin 0.938 / tab 0.788 / instr 0.000)
- step 1 — gen-003 (per-node robustness self-check) **REJECTED** (tie 0.575): the self-check
  saturated (every node self-grades robustness 1.0).
- step 2 — gen-004 (shared **adversarial** probe, decoupled from the solver) **ACCEPTED**,
  private aggregate **0.648** (+0.073), driven by instruction-routing 0.0 → **0.219**.
- step 3 — gen-005 (**lineage-aware probe pool**: always include improve/explore leaves, cap
  scales with the tie count) **ACCEPTED**, private aggregate **0.856** (+0.208) — the largest
  single-step gain. Fixed gen-004's `probe_topk=4` truncation: the probe pool now reaches the
  synonym-tolerant improve leaves, lifting instruction-routing **0.219 → 0.844** while bin-packing
  (0.938, probe saturated → top-public fallback) and tabular (0.788) held. `best` now = gen-005.
  Accept gated by MECHANICAL verifier checks (LLM verifier still blocked by spend limit).

Spend note: the LLM-adversarial verifier subagent remains unavailable (monthly spend limit), so
steps 2–3 were gated by the mechanical battery (reproduce vs pristine scorer, git integrity,
escape-residue, hard-coding audit, too-good outlier) — all clean. Inner-agent Workflow compute
DID run this session (3 family evals × ~0.6M tokens each), so the earlier hard block has eased;
budget for the remaining big-compute items (M3 steps 4–10, M5 `/rsi:ignite`) is the live constraint.

Resume plan: see the "How to continue" section above. In short — continue run-002 from step 4
(incumbent **gen-005**; the `probe_topk` follow-up is RESOLVED; tabular private is the stuck
headroom at 0.7875), and/or run M5 `/rsi:ignite`. §5.2 chassis A/B is DONE (ship Arm B —
`docs/experiments/chassis-ab/`); M4 `/rsi:report` is already done (`docs/experiments/m4-report.md`).

## Pending execution phase (real Workflow compute, ~0.5M tokens / ~30 min per inner eval)

§5.2 chassis A/B is **DONE** (ship Arm B — `docs/experiments/chassis-ab/`) and M4 `/rsi:report`
is **DONE** (`docs/experiments/m4-report.md`). Remaining order: (1) **M3 steps 4–10** (the 10-step
unattended exit run on the 3-family battery), then (2) **M5 `/rsi:ignite`**. Pace multi-hour runs
via `send_later`/ScheduleWakeup re-invoking `/rsi:run` on the same run dir (resume-aware from the
ledger plus best.txt). Final: promote rsi-loop in `.claude-plugin/marketplace.json` (currently
hidden) and do the full as-built PLAN.md reconciliation.

## How to resume a live run

Target: **run-002, incumbent gen-005, next step 4.**

1. `RUN=<scratchpad>/rsi-runs/run-002 && mkdir -p $RUN/generations $RUN/eval`
2. Copy `docs/experiments/run-002/{gen-003,gen-004,gen-005}` into `$RUN/generations/`,
   plus `plugins/rsi-loop/baseline/gen-000` as `$RUN/generations/gen-000`.
3. Copy `docs/experiments/run-002/ledger.jsonl` to `$RUN/ledger.jsonl`; write
   `$RUN/best.txt` = `generations/gen-005` (the incumbent, next step 4) and
   `$RUN/tasks.txt` = the 3-family battery (bin-packing + tabular-classification + instruction-routing).
4. Outer-step procedure: `commands/rsi-step.md` (proposer prompt pattern used for steps 1-3
   is reflected in `agents/proposer.md`; per-eval budget: haiku, 9 nodes, seed 42).

## Operational gotchas (hard-won, do not rediscover)

- The Workflow runtime delivers `args` as a JSON **string** — every generation script starts
  with the parse-both-encodings line; keep it when proposers write new generations.
- Workflow scripts: no `Date.now`/`Math.random` (seeded Lehmer RNG instead), `export const
meta = {...}` pure literal first, plain JS only.
- Private scoring only via `RSI_OUTER_LOOP=1 bash scripts/rsi-score.sh --private ...`
  (the deny hook blocks everything else; `RSI_HOOK_DISARM=1` disarms for plugin dev).
- Inner evals: ~0.5M tokens / ~30 min each on bin-packing (fixed 9-node budget).
- Structural gate before spending eval budget: files present, policy.json valid,
  meta-literal + args-parse lines intact, no private/holdout references in prompts
  outside prohibition sentences.

## Known open issues (from run-001 ledger)

- Self-generated stress suite is rebuilt per run → unstable tie-breaker instrument
  (step-3 rejection root cause). Candidate fix belongs in a future PROPOSED generation
  (e.g. persist suite spec in the generation dir), not in the immutable harness.
- Single-task battery; M3 adds the ML-engineering and harness-engineering families
  (pure-stdlib Python only — no numpy/sklearn in this environment).

## Firewall / harness-integrity model (post-audit)

- Agents run as the **same uid as the harness (root here)**, so OS read-only bits cannot
  PREVENT a write. The immutable-harness guarantee is therefore **detection, not prevention**:
  `scripts/rsi-check-integrity.sh` anchors scorer/task/instance data to git HEAD (plugin
  source) or a `.integrity.sha256` manifest (sandbox / run copies); `rsi-score.sh --private`
  and the verifier refuse to trust a tampered harness (exit 5). Do not reintroduce `chmod`-
  based "hardening" — it gives false assurance under root.
- The deny hook (`hooks/deny-private.py`) is the fast-feedback layer for naive/accidental
  access; the private-read wall for inner agents is structural (sandboxes contain no
  private/). Tests: `tests/test-deny-hook.sh` (60), `tests/test-scorer.sh` (7),
  `tests/test-integrity.sh` (6) — all in the `test-rsi-loop` CI job.
