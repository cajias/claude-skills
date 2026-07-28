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
