# M3 findings — run-002 (three-family battery, --seeds 3 pivot)

## Summary

The M3 extension ran the RSI loop on the full three-family battery (bin-packing + tabular-classification +
instruction-routing) to a **plateau stop**: 10 ledger steps, ~37.9M inner tokens. Net result is one accepted
improvement — gen-006's data-perturbation probe, robust aggregate **0.644 → 0.725** — plus two rich negative results
that map the local ceiling of gen-005's neighborhood on this battery. The headline of the run is methodological: the
mid-run switch from single-seed to 3-seed-median selection, which revealed that the previously banked 0.856 was a lucky
draw and reset the honest incumbent bar to 0.644.

## Finding 1: single-seed private scores are unreliable on tiny splits

gen-005 had been accepted at a single-seed private aggregate of **0.856**. Re-baselining it under 3-seed-median
selection (seeds 42/43/44) collapsed the aggregate to **0.644** — a **-0.21** correction. The 0.856 was a simultaneous
lucky draw across three tiny private splits; the per-seed vectors make this concrete:

```text
gen-005 re-baseline @ seeds 42/43/44
  bin-packing            [0.937937, 0.937937, 0.937937]  median 0.938
  tabular-classification [0.0,      0.775,    0.7875 ]   median 0.775
  instruction-routing    [0.4375,   0.15625,  0.21875]   median 0.219
  aggregate (mean of per-task medians)                   0.644
```

The tabular and instruction-routing splits swing across the full range depending on seed (tabular hits 0.0 on one seed;
instruction-routing ranges 0.156–0.438). A single-seed score sits anywhere in that range, so a lucky draw inflates the
aggregate well above the robust value. This confirms PLAN.md's own "prefer multi-seed" caveat directly, and motivated
the switch to selecting on the **mean of per-task medians** across three seeds for every subsequent step.

## Finding 2: the data-perturbation probe is a real, repeatable gain (gen-006 ACCEPTED)

gen-006 makes the adversarial probe **modality-aware**: numeric-tabular tasks no longer get paraphrase variants (which
cannot discriminate ML models — the input is a data matrix, not prose), but a train-perturbation battery —
bootstrap resampling, subsampling, feature jitter, noise-permutation, and feature-holdout — scored by prediction
stability. Re-evaluated at seeds 3, this clears the honest bar:

```text
gen-006 data-perturbation probe @ seeds 42/43/44
  bin-packing            [0.937937 x3]           median 0.938
  tabular-classification [0.825, 0.8,   0.0  ]   median 0.800  (gen-005: 0.775)
  instruction-routing    [1.0,   0.4375, 0.25]   median 0.438  (gen-005: 0.219)
  aggregate                                       0.725  >  0.644  (+0.081)
```

The verifier was **clean** — mechanical checks V1/V3/V4/V5 (reproduce vs pristine scorer, git integrity, escape-residue,
hard-coding/outlier) plus the LLM adversarial audit all passed. tabular median rose 0.775 → 0.800 and
instruction-routing 0.219 → 0.438, so the gain is spread across the two families the probe targets, not a single-task
artifact. gen-006 becomes the new incumbent.

## Finding 3: instruction-routing (n=32 private) is fundamentally probe-limited

Two independent attempts to push instruction-routing past gen-006 both failed, and failed the same way — at the target
task, on the median, not on variance:

```text
gen-008 multi-draw de-noising @ seeds 42/43/44   (reduce probe variance by averaging draws)
  tabular-classification [0.825, 0.8375, 0.95   ]  median 0.838
  instruction-routing    [0.3125, 0.5,   0.21875]  median 0.313   (gen-006: 0.438)
  aggregate                                         0.696  <  0.725   rejected

gen-009 correctness-coverage probe @ seeds 42/43/44   (fix probe bias on a synthesized coverage set)
  tabular-classification [0.5125, 0.0,   0.875   ]  median 0.513
  instruction-routing    [0.1875, 0.125, 0.34375 ]  median 0.188   (gen-006: 0.438)
  aggregate                                         0.546  <  0.725   rejected
```

gen-008 tried to cut probe **variance** by averaging multiple draws; instruction-routing's median fell 0.438 → 0.313.
The failure is a **bias** problem, not a variance one — averaging draws pulls the selected node toward the mean model,
which generalizes worse here, so smoothing hurts. gen-009 tried to fix probe **bias** by scoring on a synthesized
correctness-coverage set; it produced healthy, monotonic probe rankings yet still dropped the median to 0.188, because
the synthesized coverage set does not match the private distribution.

Conclusion: no public-data-only probe tried here — self-consistency, multi-draw de-noising, or correctness-coverage —
reliably predicts this split's private generalization. On this battery, gen-006 is the ceiling of gen-005's
neighborhood; the two rejections bound a local optimum.

## RSI-ladder read-out

- **Level 0 (the loop improves the agent):** met. gen-000 (0.575) → gen-006 (robust 0.725) is a real,
  verifier-clean gain under the honest 3-seed rule. Caveat: part of the apparent step-3 headline gain was single-seed
  luck; the honest incumbent bar is 0.644, and the durable improvement over baseline is measured against that.
- **Levels 1/2:** unchanged from the banked m4-report — not re-run in this extension. No claim is made here beyond
  Level 0.

## Harness robustness gap (noted, not fixed)

`inner-agent.workflow.mjs` records a node from the agent's self-reported public score **without verifying that
`solution.py` exists on disk**. When the top-public fallback names a node whose file is missing, a phantom node is
recorded. This fired once during the run (bin-packing, gen-007 single-seed step). The fix belongs in a future
generation's selection logic, **not** in the immutable harness — flagging it here so a later proposer picks it up.

## Honest caveats

- The tasks are miniature; the private splits are tiny (instruction-routing n=32) and noisy.
- 3-seed median mitigates single-seed variance but does not eliminate it — three seeds still leaves per-task swings
  (tabular hits 0.0 on individual seeds even for accepted generations).
- The two step-8/9 rejections map a **local** ceiling on this probe battery, not a global limit on the task; a
  different instrument or larger private split could still move instruction-routing.
