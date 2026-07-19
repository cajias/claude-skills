# Continuation state — rsi-loop implementation

Snapshot for resuming the KICKOFF.md build in a fresh session. Everything needed lives in
this repo; the scratchpad run directory is ephemeral and fully reconstructable from
`docs/experiments/run-001/`.

## Where the build stands (2026-07-19)

- **M1 — done** (`docs/experiments/m1-smoke-bin-packing.md`): gen-000 verified end-to-end;
  `/rsi:autoresearch` live.
- **M2 — exit criteria met** (`docs/experiments/run-001/README.md`): 3 manual outer steps,
  gen-002 accepted (private 0.9405 > 0.9379), steps 1 and 3 rejected with recorded diagnoses.
- **M3 — CODE COMPLETE** (PR #39, branch `claude/rsi-skills-implementation-o8q1zv`): three-family
  battery (bin-packing + tabular-classification + instruction-routing), `scripts/rsi-aggregate.py`
  (robust cross-seed aggregate + too-good outlier flag), `/rsi:run` driver, verifier wired to
  <50% rule + `--flag-outliers`. Runtime exit criterion (10-step unattended run) is the pending
  execution phase.
- **M4 — MACHINERY BUILT** (PR #39): `baseline/gen-human`, `holdout-tasks/` (interval-scheduling,
  tabular-ring, instruction-ops, timeseries-forecast), `scripts/rsi-report.py` + `/rsi:report`.
  Pending: real report run producing ladder evidence.
- **M5 — MACHINERY BUILT** (PR #39): `/rsi:ignite` Level-2 swap test. Pending: real ignite run.
- Tests all green: deny-hook 66, scorer 18, integrity 12, aggregate 12, report 16; validate + test-skills pass.

## §5.2 chassis decision (RESOLVED by the user) — FULL pre-registered scale

The user chose **full pre-registered scale**: 2 arms (Arm A = `uditgoenka/autoresearch` plugin
driving our harness; Arm B = native `/rsi:run`) × 2 reps × 10 steps ≈ 40 evaluations ≈ 20M+
tokens, ~20h. Arm A install: `npx skills add uditgoenka/autoresearch`; its single-metric
contract maps onto `rsi-aggregate.py`'s `private_aggregate`. This is the pending big-compute
item. Write both arms up under `docs/experiments/`; the pre-registered decision rule (PLAN.md
§5.2) picks the `/rsi:step` chassis. Do NOT fabricate any eval score — every ledger line must
come from real Workflow compute or be clearly marked not-yet-run.

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
budget for the remaining big-compute items (chassis A/B, steps 4–10) is the live constraint.

Resume plan: continue run-002 from step 4 (incumbent **gen-005**). The `probe_topk` follow-up is
now RESOLVED. Next proposer targets remaining headroom (tabular private stuck at 0.788 across
gen-000→005; instruction-routing has ~0.156 left to 1.0). Then §5.2 chassis A/B, M4 `/rsi:report`,
M5 `/rsi:ignite`.

## Pending execution phase (real Workflow compute, ~0.5M tokens / ~30 min per inner eval)

Order: (1) §5.2 chassis A/B (40 evals), (2) M3 10-step exit run on the 3-family battery,
(3) M4 `/rsi:report` (gen-human battery + best-vs-gen000 holdout scoring), (4) M5 `/rsi:ignite`.
Pace multi-hour runs via `send_later`/ScheduleWakeup re-invoking `/rsi:run` on the same run dir
(resume-aware from ledger + best.txt). Final: promote rsi-loop in `.claude-plugin/marketplace.json`
(currently hidden) and do the full as-built PLAN.md reconciliation.

## How to resume a live run

1. `RUN=<scratchpad>/rsi-runs/run-001 && mkdir -p $RUN/generations $RUN/eval`
2. Copy `docs/experiments/run-001/{gen-001,gen-002,gen-003}` into `$RUN/generations/`,
   plus `plugins/rsi-loop/baseline/gen-000` as `$RUN/generations/gen-000`.
3. Copy `docs/experiments/run-001/ledger.jsonl` to `$RUN/ledger.jsonl`;
   `run-state.json` has the incumbent (gen-002) and next step number (4) —
   write `$RUN/best.txt` and `$RUN/tasks.txt` from it.
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
