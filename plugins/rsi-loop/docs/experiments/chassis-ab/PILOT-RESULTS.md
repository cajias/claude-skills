# §5.2 Chassis A/B — PILOT Results

**Phase 2 pilot** (`PRE-REGISTRATION.md`: "2 arms × 1 rep × ~3 steps to validate
the harness end-to-end"). This document is committed as evidence and is written
to be scrupulously honest about what was and was not exercised. Every score below
is quoted verbatim from the two pilot ledgers; nothing is invented.

Ledgers (source of truth):

- `arm-a`: `…/rsi-pilot/arm-a/ledger.jsonl`
- `arm-b`: `…/rsi-pilot/arm-b/ledger.jsonl`

## TL;DR

- The pilot **did not test the autoresearch chassis.** Both arms ran on the
  **same native `/rsi:step` outer loop**. The "Arm A vs Arm B" labels are two
  independent native runs with different proposer draws — **not a chassis
  comparison.**
- What it **did** establish is real and valuable: the Workflow runtime is live
  and not spend-limited, the native chassis works end-to-end on real compute, it
  reproduces the run-002 RSI arc (including one genuine diagnose → repair →
  improve accept), and the reward-hack verifier fired for real on the one accept.
- The pre-registered **decision rule MUST NOT be applied** to these numbers as a
  chassis verdict. See the next section.

## What this pilot did and did not test

**Did NOT test (the headline finding).** The third-party `autoresearch` skill's
`iterate` loop was **never handed control** for Arm A. Both "arms" were driven by
the **identical** native `/rsi:step` procedure: the orchestrator ran bash for
sandbox / private score / ledger, the Workflow tool for the inner evals, and the
`rsi-proposer` / `rsi-verifier` subagents. Therefore:

- "Arm A" and "Arm B" here are **two independent runs of the native chassis**,
  differing only in the non-deterministic proposer draw. They are **not** Arm A
  (autoresearch-driven) vs Arm B (native) as pre-registered.
- The `metric.txt` / `cat metric.txt` shim and `scripts/rsi-arm-a-metric.sh` were
  **built and validated separately** (the adapter reproduced run-002 gen-005's
  aggregate `0.856396` exactly and scored a live smoke-test solution at
  `0.937937`), and `scripts/rsi-arm-a-guard.sh` exists. But **wiring
  autoresearch's `Verify:` / `Guard:` / git-commit-revert loop to actually drive
  the orchestration was NOT done.** That wiring is the real Arm A and remains the
  **key untested piece** for the full campaign.
- Consequently the **decision rule is not exercised** by this pilot. No arm is
  adopted or rejected here.

**DID test (the actual contribution).**

1. **Workflow runtime is LIVE and not spend-limited.** 216 inner sub-agents
   across 5 Workflow jobs, **0 errors** (smoke 9 + baseline 18 + step1 54 +
   step2 73 + step3 62). Those 5 jobs cover **21 task-evals** (1 + 2 + 6 + 6 + 6).
   The run-002 monthly-spend-limit contingency did **not** bite this session.
2. **The native `/rsi:step` chassis works end-to-end.** Every stage exercised on
   real compute: baseline → propose (`rsi-proposer`) → structural gate → sandbox
   → inner eval (Workflow) → private score + aggregate → score gate → verifier
   (`rsi-verifier`, on would-be-accepts only) → accept/reject → ledger append →
   `best.txt` update.
3. **Faithful RSI dynamics** reproducing the run-002 arc (detailed below).
4. **Reward-hack defenses fired for real.** The single accept went through the
   full mechanical + LLM verifier battery and survived; rejections were recorded
   honestly with diagnoses; no fabricated scores.

## Ledger tables (verbatim)

Family columns are **private** per-task scores; `agg` is `private_aggregate`
(mean of per-task medians, single seed ⇒ median == score). Both runs share the
identical `gen-000` baseline.

### Run labelled `arm-a` (native run 1)

| Step | Generation | Parent  | bin      | instr | tabular | private_agg | Outcome              |
| ---- | ---------- | ------- | -------- | ----- | ------- | ----------- | -------------------- |
| 0    | gen-000    | —       | 0.937937 | 0.000 | 0.9375  | 0.625146    | incumbent (baseline) |
| 1    | gen-001    | gen-000 | 0.937937 | 0.000 | 0.825   | 0.587646    | rejected             |
| 2    | gen-002    | gen-000 | 0.937937 | 0.000 | 0.7875  | 0.575146    | rejected             |
| 3    | gen-003    | gen-000 | 0.937937 | 0.000 | 0.875   | 0.604312    | rejected             |

Run `arm-a` **never accepted**: incumbent stayed `gen-000` (0.625146) throughout.

### Run labelled `arm-b` (native run 2)

| Step | Generation | Parent  | bin      | instr | tabular | private_agg | Outcome                  |
| ---- | ---------- | ------- | -------- | ----- | ------- | ----------- | ------------------------ |
| 0    | gen-000    | —       | 0.937937 | 0.000 | 0.9375  | 0.625146    | incumbent (baseline)     |
| 1    | gen-001    | gen-000 | 0.937937 | 0.000 | 0.825   | 0.587646    | rejected                 |
| 2    | gen-002    | gen-000 | 0.937937 | 0.250 | 0.775   | 0.654312    | **ACCEPTED** (+0.029166) |
| 3    | gen-003    | gen-002 | 0.937937 | 0.000 | 0.775   | 0.570979    | rejected (regression)    |

Run `arm-b` accepted `gen-002`; the step-3 regression correctly did **not**
overwrite `best.txt`, which stayed `gen-002` (0.654312).

## RSI dynamics observed (reproduces the run-002 arc)

- **Step 0 (baseline).** Both runs scored `private_aggregate` **0.625146** (bin
  0.937937 / instr 0.000 / tabular 0.9375). This differs from run-002's 0.575
  because inner LLM drafts are **non-deterministic across runs even at fixed seed
  42** — the seed drives the node-selection Lehmer RNG, not the subagents'
  generated code — and this session drew a **stronger tabular baseline**
  (0.9375 vs run-002's 0.788).
- **Step 1 (robustness self-check).** **Both rejected**, identical agg
  **0.587646**. The instrument **saturated**: every node self-grades robustness
  1.0, so instruction-routing stays public 1.0 / private 0.0. This exactly
  reproduces the run-002 step-1 failure mode ("an agent grading its own
  robustness gives itself 1.0"). Diagnosis recorded: the probe must be
  adversarial / decoupled from the solver.
- **Step 2 (decoupled adversarial probe) — the two runs diverge here.**
  - Run `arm-a` used a **shared re-rank probe** and was **rejected** at
    **0.575146**: the probe re-ranked an all-overfit candidate pool and
    instruction-routing stayed private 0.0.
  - Run `arm-b` used an **independent-oracle probe** (the probe author computes
    answers itself from the task definition and never sees candidate code) and
    was **ACCEPTED** at **0.654312** (+0.029166 over baseline), lifting instr
    **0.0 → 0.25**. The accept passed the **full verifier battery** (reproduce
    vs pristine scorer, hard-coding audit, git integrity, escape-residue,
    too-good outlier) — verdict `clean` / `accept-eligible`. The 0.25 is a
    **genuine general-purpose parser** (add/multiply handlers generalize to
    unseen private paraphrases; narrower handlers honestly return empty; scores
    reproduce exactly; bimodal 8×1.0 / 24×0.0, no outlier). A **real diagnose →
    repair → improve arc.**
- **Step 3 — both rejected.**
  - Run `arm-a` `gen-003` reached **0.604312** (< baseline 0.625146): the
    oracle-probe design did not land a general parser as best this draw, instr
    back to 0.0 (tabular did climb to 0.875, not enough).
  - Run `arm-b` `gen-003` fell to **0.570979** (< its incumbent 0.654312): the
    broadening improve operator **lost** gen-002's gain (instr 0.25 → 0.0,
    tabular slipped) — the non-deterministic draw did not reproduce the general
    parser the gen-002 probe had selected.
- **Takeaway.** The instruction-routing repair is **fragile across
  non-deterministic draws**. run-002 needed the lineage-aware probe-pool fix at
  gen-005 to stabilize it — a known property — which is why a 3-step pilot is
  not enough to see stabilization.

## Per pre-registered metric (metrics 1–5)

| #   | Metric (pre-reg)                | Pilot result                                                                                                                                                                                               |
| --- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Primary: best private aggregate | **NOT a chassis comparison — both runs native.** run-b best 0.654312 vs run-a 0.625146, delta **+0.029166** (> 0.02) — a difference between two native proposer-draw trajectories, **not** Arm A vs Arm B. |
| 2   | Score-per-token slope           | Not meaningfully estimable at 3 steps; run-b showed one real +0.029166 step then regressed; run-a monotone-below-baseline.                                                                                 |
| 3   | Harness overhead                | Not separately instrumented in the pilot; ~10.2M inner-eval tokens dominate (see below).                                                                                                                   |
| 4   | Protocol fidelity               | Clean (details below): ledgers complete, gates fired correctly, verifier ran, incumbent tracking correct.                                                                                                  |
| 5   | Friction                        | The autoresearch loop was never wired to drive Arm A — the central Arm A friction is **untested**, not resolved. Metric adapter + guard scripts built and validated in isolation only.                     |

**Metric 1 caveat, stated plainly:** the +0.029166 gap exceeds the pre-registered
0.02 "within noise" threshold, but that threshold was defined to compare **Arm A
vs Arm B chassis**. Since both runs here are the **native chassis**, the gap
measures **proposer-draw variance**, and applying the decision rule to it would
be invalid.

## Token accounting

**~10.2M inner tokens total this session.** This **corrects the earlier ~9M
estimate.**

| Phase     | Inner tokens   |
| --------- | -------------- |
| smoke     | 413,560        |
| baseline  | 833,721        |
| step 1    | 2,709,635      |
| step 2    | 3,509,282      |
| step 3    | 2,718,977      |
| **total** | **10,185,175** |

The ledgers additionally carry per-step `inner_tokens` fields; the figures above
are the session-level accounting.

## Fidelity notes (metric 4)

- **Ledgers complete.** Every step has a real ledger line with real Workflow
  compute behind it; no line is fabricated or marked not-yet-run.
- **Ledger-append-before-`best.txt`** ordering honored throughout.
- **Incumbent tracking correct.** Run `arm-a` never accepted → stayed `gen-000`.
  Run `arm-b` accepted `gen-002` → `best.txt` = `gen-002`; the step-3 regression
  (0.570979 < 0.654312) correctly did **not** overwrite it.
- **Score gate correct.** Accept iff candidate strictly beats incumbent;
  0.587646, 0.575146, 0.604312, 0.570979 all correctly rejected against their
  incumbents.
- **Verifier ran.** The LLM-adversarial verifier **was available** this session
  and gated the one accept (run-b gen-002, verdict `clean`). The pre-reg's
  spend-limit contingency did **not** bite — a difference from run-002, where
  only the mechanical battery could run.
- **Caveat.** These fidelity observations are for the **native chassis**, since
  that is what actually ran. They are **not** evidence about autoresearch's
  fidelity.

## Reward-hack / faithfulness guards

- Private scoring stayed **outer-side only** (`RSI_OUTER_LOOP=1`); the integrity
  gate (git HEAD / `.integrity.sha256`, exit 5 on tamper) ran before any trusted
  private score.
- The single accept (run-b gen-002) passed the **full mechanical + LLM battery**
  and survived: reproduce vs pristine scorer (reproduced_aggregate 0.654312),
  hard-coding audit, integrity, escape residue, and outlier all clean.
- Rejections were recorded honestly with diagnoses; no hacked win slipped past
  the guard because the one candidate that reached the verifier was a genuine
  generalizing parser.

## Next / what the full campaign must do

1. **Actually wire autoresearch to drive Arm A** — this is the pilot's central
   gap. Invoke its `iterate` loop with `Verify: cat metric.txt` (fed by the
   validated `rsi-arm-a-metric.sh` shim), `Guard: rsi-arm-a-guard.sh`,
   `git`-commit = accept / `git revert HEAD --no-edit` = reject, and the
   pre-declared `AR_DISABLE_*` hook disables. Only then is the chassis
   comparison real.
2. **Run the pre-registered protocol**: 2 arms × 2 reps × 10 steps on the
   3-family battery (≈ 20M+ tokens), so the primary metric is a genuine Arm A vs
   Arm B measurement rather than proposer-draw variance.
3. **Steps > 3 are required.** The fragile instruction-routing repair (accepted
   at step 2, lost at step 3) shows a 3-step window cannot see stabilization;
   run-002 only stabilized at gen-005 via the lineage-aware probe-pool fix.
4. Keep both arms writing the shared `ledger.jsonl` schema and preserve the
   losing arm's run in `docs/experiments/` as evidence, per the pre-registration.
