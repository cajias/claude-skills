---
description: Level-2 ignition test — does a campaign driven by the best evolved generation beat the baseline campaign at equal budget?
argument-hint: "<source-run-dir> [--max-steps N] [--budget TOKENS]"
---

Run the AIDE² **Level-2 (ignition)** test for the run in "$ARGUMENTS". Level 2
asks whether the system's _self-improvement ability_ has itself improved: does a
campaign whose operating scaffold IS the best evolved generation (`vN`, its
`policy.json` + `prompts/` promoted verbatim into the outer seat) beat the
baseline scaffold (`vN−1` = stock gen-000) from the same start at the same
budget? The paper measured this honestly and did **not** claim it (AIDE47-as
-outer converged faster but showed no asymptotic advantage). Expect to do the
same: this command is instrumented to measure, not to pass.

## Design (a paired A/B, everything held equal but the promoted scaffold)

Both arms are full outer campaigns from the identical `baseline/gen-000`
starting scaffold, over the same task battery, the same per-eval budget and
seeds (42/43/44), the same verifier, deny hook, and the same total step/token
budget. They differ in ONE thing — the operating scaffold's own
`policy.json` + `prompts/`:

- **Arm control**: the stock `baseline/gen-000` scaffold, unmodified.
- **Arm ignited**: the same `baseline/gen-000` scaffold with its
  `{policy.json, prompts/*}` **replaced** by the best discovered inner scaffold's
  bytes (the promotion — PLAN.md §6.1.5). The promoted scaffold is the source
  run's **last accepted M6 inner generation** (discovered under the frozen
  engine), NOT the run-002 lineage — gen-006 carries out-of-vocabulary fields a
  frozen generic engine cannot interpret (§6.1.5).

This is a **literal policy+prompt lift**, not a prose brief. It _supersedes_ the
old M5 `ignite/strategy-brief.md` prose-injection seam (which tested
strategy-briefing, not compounding); that seam is removed. The `policy.json`
vocabulary is unchanged and shared verbatim by both seats — the 8 fields the
frozen engine reads — so no new fields are introduced or permitted (§6.1.5).

## Procedure

0. **Pre-flight power gate (before releasing any A/B budget).** Run
   `bash plugins/rsi-loop/tests/test-phase0-gate.sh` — the deterministic Phase-0
   gate. It drives the real engine over a synthetic landscape (zero LLM, <2s) and
   MUST pass: it proves the assembled instrument resolves a planted +0.15
   policy-lift positive at K=3 while returning `NO_RESULT` on a 0-effect and a
   0.03 effect. If it fails, the instrument cannot resolve its planted positive —
   do not spend. The real ~$8 Phase-0 calibration (`rsi-ignition.py power
--calibrate` on the real battery, step 4) then measures σ_d up front; if the
   budget can't fund `K_req` seeds the run is declared INCONCLUSIVE before spend.

1. Resolve the promoted scaffold from the source run: `SRC=<source-run>/best-scaffold`
   — the source run's last accepted M6 inner generation dir (its `policy.json` +
   `prompts/`), discovered under the frozen engine. `baseline/gen-000` serves as
   BOTH the inner seed artifact AND the outer **control** scaffold (there is no
   separate outer gen-000).

2. Scaffold two fresh runs with `/rsi:init` (both from stock gen-000, full
   battery — `/rsi:init` already produces the flat generation dir the lift
   targets, so no new directory contract is needed), then perform **the lift**
   into the ignited arm only:

   ```bash
   SRC=<source-run>/best-scaffold            # last accepted M6 inner generation (frozen-engine)
   /rsi:init <run>/ignite/arm-control        # outer scaffold = baseline/gen-000 (stock), flat dir
   /rsi:init <run>/ignite/arm-ignited        # outer scaffold = baseline/gen-000 (stock), flat dir
   cp    "$SRC/policy.json"  <run>/ignite/arm-ignited/policy.json      # THE LIFT
   cp -r "$SRC/prompts/."    <run>/ignite/arm-ignited/prompts/
   /rsi:run <run>/ignite/arm-control  --max-steps 8 --budget B --seeds 3 --plateau 0
   /rsi:run <run>/ignite/arm-ignited  --max-steps 8 --budget B --seeds 3 --plateau 0
   ```

   The **only** difference between the arms is the bytes of
   `arm-ignited/{policy.json, prompts/*}`; engine, adapter, battery, seeds,
   budget, verifier, and deny hook are byte-identical.

3. Drive each arm with `/rsi:run` at the **same** `--max-steps N` (default 8, so
   `G=8` meta-generations), the **same** `--budget B`, `--seeds 3`, and
   `--plateau 0` (disable the early stop) so both arms execute an equal step
   budget — "equal budget" is enforced, not assumed. Everything else is
   identical.

4. **Power adequacy up front (before believing any verdict).** Run
   `python3 plugins/rsi-loop/scripts/rsi-ignition.py power --calibrate` on a
   control-vs-control null ΔA sample (N_null ≥ 5) to MEASURE σ_d and print
   `MDE(K)` at the run's K plus `K_req(target_effect)`. If the budget cannot fund
   `K_req` seeds for the effect you care about, declare the run **INCONCLUSIVE up
   front** — the M5 lesson (K=3 → MDE≈0.072 cannot resolve a 0.025-scale effect;
   that needs K≈25). Then build each arm's report:
   `python3 plugins/rsi-loop/scripts/rsi-report.py --ledger <arm>/ledger.jsonl`,
   reading `tokens_to_best` and the arm's **cumulative inner tokens** (sum of
   `inner_tokens` over its ledger) so the equal-budget claim is measured, not
   asserted. Report side by side: best private aggregate, `tokens_to_best`,
   cumulative inner tokens, best-so-far growth rate and `n_accepted_improvements`,
   acceptance rate, and hack rate.

5. **Verdict (honest, computed — not eyeballed).** Feed each arm's per-seed
   best-so-far trajectories `B(g,s)` (g=0..8) to the decision instrument:

   ```bash
   python3 plugins/rsi-loop/scripts/rsi-ignition.py decide \
     --sigma-d <measured> --planted-positive-cleared <true|false>
   # stdin: {"seeds":[42,43,44],"G":8,
   #         "control":{"42":[B0..B8],...},"ignited":{"42":[B0..B8],...}}
   ```

   It returns `SUPPORTED` / `REFUTED` / `NO_RESULT` per the §6.1.4 rate decision
   rule: SUPPORTED requires `ΔA ≥ MDE(K)` AND all seeds `ΔA_s > 0` AND sustained
   over the tail `{6,7,8}` AND `ΔR ≥ 0` — a strictly higher, sustained plateau.
   `ΔR > 0` with `|ΔA| < MDE` (converged faster, same asymptote) is `NO_RESULT`,
   NOT a win — the paper's exact finding, and the **expected** outcome here.
   `NO_RESULT` (paper parity) is the prior; report it honestly. An efficiency edge
   in `tokens_to_best` can accompany `NO_RESULT` but never upgrades the verdict —
   only a strictly higher sustained asymptote produces SUPPORTED. If the
   instrument cannot resolve its planted positive at K, the verdict is
   `NO_RESULT` regardless of the arms (the hard power precondition).

Write the two ledgers, the promoted scaffold's provenance, the `power` calibration
and the `decide` verdict JSON under `<source-run-dir>/ignite/` so the test is
reproducible and auditable. As everywhere, private scores never touch an inner
agent; the immutable harness is never edited during either arm.
