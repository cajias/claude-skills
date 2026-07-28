# ignite-m6 — isomorphic-ignition runbook

M6 ignition is the AIDE² **Level-2** test: does a campaign whose operating scaffold IS the best evolved
generation — its `policy.json` + `prompts/` promoted verbatim into the outer seat — reach a strictly
higher, sustained asymptote than the stock gen-000 scaffold at **equal budget**? Both arms start from the
identical `baseline/gen-000` and differ in exactly one thing: the bytes of `arm-ignited/{policy.json,
prompts/*}`. The expected, honest outcome is `NO_RESULT` (paper parity — "converged faster, no asymptotic
advantage"); this runbook is instrumented to **measure**, not to pass. See `PREREG.md` for the contract.

## (a) Discover the best scaffold — fresh gen-000 M6 inner campaign

The lift source is discovered under the **FROZEN 8-field engine**, NOT the run-002 / gen-006 lineage
(gen-006 carries out-of-vocabulary fields a generic frozen engine cannot interpret).

```bash
/rsi:init  <discovery-run>                                   # generations/gen-000 = copy of baseline/gen-000
/rsi:run   <discovery-run> --max-steps 8 --seeds 3 --budget B   # frozen engine, full battery
```

The last accepted generation — the dir named in `<discovery-run>/best.txt` — becomes `best-scaffold`, the
lift source for arm-ignited.

## (b) Paired A/B via the cp-seam

```bash
SRC=<discovery-run>/best-scaffold                                 # last accepted M6 inner generation (frozen-engine)
/rsi:init <run>/ignite/arm-control                                # outer scaffold = baseline/gen-000 (stock)
/rsi:init <run>/ignite/arm-ignited                                # outer scaffold = baseline/gen-000 (stock)
cp    "$SRC/policy.json"  <run>/ignite/arm-ignited/policy.json    # THE LIFT
cp -r "$SRC/prompts/."    <run>/ignite/arm-ignited/prompts/
/rsi:run <run>/ignite/arm-control  --max-steps 8 --budget B --seeds 3 --plateau 0
/rsi:run <run>/ignite/arm-ignited  --max-steps 8 --budget B --seeds 3 --plateau 0
```

`--plateau 0` disables the early stop so both arms spend an equal step budget. The only difference between
the arms is the two `cp` lines above.

## Phase-0 calibration (paid, ~$8) — MEASURE σ_d before any campaign

Run a control-vs-control null ΔA sample (N_null ≥ 5) and feed the deltas to `power --calibrate`:

```bash
echo '{"null_deltas":[0.01,-0.02,0.03,-0.01,0.02,-0.03]}' \
  | python3 scripts/rsi-ignition.py power --calibrate --K 3 --target-effect 0.025
```

It prints the **measured** σ_d, the MDE(K) table, and K_req(target-effect).
**STOP RULE:** if the budget cannot fund K_req seeds for the smallest interesting effect, declare the run
**INCONCLUSIVE up front** and spend nothing on a campaign (the M5 lesson: K=3 → MDE ≈ 0.072 cannot resolve
a 0.025-scale effect; that needs K ≈ 25).

## Verdict

Build each arm's report, then compute the verdict — never eyeballed:

```bash
python3 scripts/rsi-report.py --ledger <run>/ignite/arm-control/ledger.jsonl
python3 scripts/rsi-report.py --ledger <run>/ignite/arm-ignited/ledger.jsonl

python3 scripts/rsi-ignition.py decide --sigma-d <measured> --planted-positive-cleared true <<'JSON'
{"seeds":[42,43,44],"G":8,
 "control":{"42":[B0,...,B8],"43":[B0,...,B8],"44":[B0,...,B8]},
 "ignited":{"42":[B0,...,B8],"43":[B0,...,B8],"44":[B0,...,B8]}}
JSON
```

- **SUPPORTED** — ΔA ≥ MDE AND all seeds ΔA_s > 0 AND sustained over tail {6,7,8} AND ΔR ≥ 0: ignited
  reaches a strictly higher, sustained plateau — Level 2 clears.
- **REFUTED** — ΔA ≤ −MDE (or faster-losing): ignited plateau measurably worse.
- **NO_RESULT** — power precondition fails, OR |ΔA| < MDE (within noise — the paper's outcome and the
  expected one), OR ΔA ≥ MDE while ΔR < 0, OR the sign/sustained gate fails. Level 2 not supported ≠
  refuted. An efficiency edge in `tokens_to_best` may accompany `NO_RESULT` but never upgrades the verdict.

## Dry-run verification (non-LLM, already passing)

These four ran green before any spend:

```bash
node scripts/rsi-phase0-gate.mjs                       # GATE CLEARS (planted +0.149 ≫ MDE; 0-effect & 0.03 → NO_RESULT)
python3 scripts/rsi-ignition.py decide --self-check    # 4/4 built-in cases pass

echo '{"null_deltas":[0.01,-0.02,0.03,-0.01,0.02,-0.03]}' \
  | python3 scripts/rsi-ignition.py power --calibrate --K 3 --target-effect 0.025   # measured σ_d + K_req on synthetic null

echo '{"tasks":{"tabular-classification":{"per_instance":[0.90,0.88,0.92,0.85,0.91,0.87,0.93,0.89],"se_max":0.02}}}' \
  | python3 scripts/rsi-aggregate.py --power-check --planted-delta 0.03 --alpha 0.05  # powered → exit 0
```

## Status

Free work complete (PREREG + runbook committed, instrument verified). Paid phases 0/1/2 GATED on explicit
`BUDGET_CEILING_USD` authorization. No eval scores exist yet — `trajectories.json` / `verdict.json` are
written only after real Workflow compute.

## Verdict (measured — 2026-07-28)

**Outcome: `NO_RESULT`**, declared up front on a power / battery-resolution basis. Total spend ~$13 of the
$420 ceiling (13 inner sub-runs: 1 cost-probe + 6 gen-000 baseline + 6 gen-001). See `verdict.json` /
`trajectories.json` for the machine-readable record.

**Runtime fix first (PR #60).** The M6 inner shim used `await import()`, which the Workflow runtime
forbids; a cost-probe caught it at **$0** before any campaign spend. Fixed by inlining the engine into a
self-contained shim. The campaign ran on the fixed shim.

**Cost ran 1.75× the plan.** One inner sub-run measured **584,264 tokens / ~39 min** (9 uncapped haiku
nodes — the planned `B_inner` token cap was never built; the engine comment says so and Workflow
`budget.total` is `null`) vs. the 335K planning value. A full paired R=3 A/B is therefore ~**$442**,
~1–2.5 days.

**Discovery found a real, verified lift.** Under the frozen 8-field engine, gen-001 — a _prompt-only_
k-fold-CV selection-signal mutation (policy.json unchanged, shim byte-identical) — moved the aggregate
**0.8265 → 0.844** (+0.0175). Verifier verdict CLEAN: public reproduced exactly (s43 0.865), git-clean, no
hard-coding, public-vs-private gap ≤0.0475 (honest generalization, not the >0.30 of an overfit hacker). So
the scaffold **can** self-improve within the frozen vocabulary — the discovery gate did **not** fire, and
the A/B was warranted on that axis.

**Why we stop before the A/B — the battery cannot resolve the effect.** The gain lands _entirely_ on
tabular-classification (0.7825 → 0.8175 median); bin-packing is 100% saturated (every node, every seed,
every generation ties at exactly 0.8705 — FFD at the greedy ceiling, zero differentiating signal). The
tabular ceiling ≈ 0.86 private against a gen-000 ≈ 0.78 gives ~0.08 headroom → at most ~0.040 in the
two-task mean. That maximum is below MDE(3):

| Quantity                                          | Value       |
| ------------------------------------------------- | ----------- |
| Measured σ_d (paired per-seed ΔA SD)              | 0.0492      |
| MDE at K=3                                        | 0.0706      |
| Battery ceiling (aggregate)                       | 0.8665      |
| **Max achievable ΔA (battery-capped)**            | **0.040**   |
| K_req for the 0.040 max effect                    | 10 seeds    |
| K_req for a realistic 0.02 effect                 | 38 seeds    |
| `decide` on a plausible small-gap pair (ΔA=0.005) | `NO_RESULT` |

A paired A/B at K=10 is ~$418 for R=1 alone. So the A/B verdict is a **predetermined `NO_RESULT`-by-
underpower**; spending ~$400 to confirm it would be the exact M5 mistake — the honest non-claim belongs up
front, not after a wasted campaign.

**Paper parity.** Control and ignited would reach the same **battery-imposed** ceiling — AIDE²'s "converged
faster, no asymptotic advantage." `NO_RESULT` is the pre-registered expected success, not a failure.

**What would change the verdict (future work, out of scope here):** de-saturate the bin-packing battery
(harder instances) so it contributes differentiating signal, and/or fund K ≈ 10 seeds. Either raises the
instrument's resolving power above the effect the scaffold can actually produce.
