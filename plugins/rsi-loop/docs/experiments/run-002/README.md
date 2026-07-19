# run-002 — M3 exit run (three-family battery)

The first RSI campaign on the full three-family battery (bin-packing +
tabular-classification + instruction-routing), from the AIDE0 baseline. Fixed
budget per evaluation (9 nodes, haiku, seed 42). Selection is on the robust
private aggregate; the inner agent never sees the private split. Full step
records in `ledger.jsonl`.

| Step | Generation | Mutation                   | bin-pack | tabular | instr-route | Private agg | Outcome            |
| ---- | ---------- | -------------------------- | -------- | ------- | ----------- | ----------- | ------------------ |
| 0    | gen-000    | baseline AIDE0             | 0.938    | 0.788   | 0.000       | 0.575       | incumbent          |
| 1    | gen-003    | robustness-aware selection | 0.938    | 0.788   | 0.000       | 0.575       | **rejected** (tie) |

**M3 exit criterion** is a multi-step unattended run with a sane ledger; this
directory is that ledger as it accumulates.

## Step 1 — a faithful rejection with a load-bearing diagnosis

gen-003's mutation (each node self-generates answer-preserving perturbations of
the _public_ inputs, measures a robustness fraction, and selects on
`public × robustness`) was well-aimed at the baseline's dominant weakness —
instruction-routing's public-1.0 / private-0.0 overfitting collapse. The
mechanism partly worked but the **selection instrument saturated**:

- On instruction-routing, every one of the 9 nodes self-reported robustness
  1.0 (they each tested only perturbations they already handle), so
  `combined = public × robustness` tied all nodes at 1.0 and the loop returned
  node-0 (a plain draft, private **0.0**). A synonym-aware node-7 — which added
  "sum/total/plus for add" handling aimed exactly at the private paraphrases —
  reached private **0.344** but tied on the combined score and was not selected.
  (Its solution is preserved here as `gen-003-instr-node7-synonym-aware.py`.)
- On tabular-classification the check _did_ discriminate: node-7's
  floating-point nondeterminism under row-shuffling scored robustness 0.8 and
  was correctly rejected in favor of node-8 (robustness 1.0). But node-8's
  public dropped to 0.83 (< gen-000's 0.85) and its private held at 0.788.
- On bin-packing the returned FFD draft matched the baseline exactly.

Net: the returned bests reproduced gen-000's per-task private scores exactly, so
the aggregate tied at 0.575 and the step was rejected. This is the run-001
tie-breaker-saturation failure in a new form: **an inner agent grading its own
robustness gives itself 1.0.** The diagnosis recorded in the ledger drives the
next proposal — the self-robustness instrument must be adversarial (harder,
held-out-style perturbations the node does not already pass), or diverse
high-public candidates must be handed to the outer private scorer rather than
collapsed by a saturated self-score.

## Faithfulness notes

- The outer loop scored each generation's **own returned best**, never a
  hand-picked better node — the generation's selection policy is exactly what is
  under evaluation, so returning node-0 (0.0) instead of node-7 (0.344) is
  gen-003's result to own, not something the harness corrects.
- Private scoring ran outer-side only (`RSI_OUTER_LOOP=1`); each score passed
  the git/manifest integrity gate before it was trusted.
- Per-task gen-000 baseline scores come from the M3 battery validation runs
  (`../m3-battery-validation.md`).
