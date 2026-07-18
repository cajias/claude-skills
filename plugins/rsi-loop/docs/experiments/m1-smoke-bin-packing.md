# M1 smoke test — gen-000 on bin-packing

- Date: 2026-07-18 · Workflow run `wf_fb46ac93-14f` · seed 42
- Generation: `baseline/gen-000` (AIDE0: 5 drafts → greedy debug/improve, full-history context)
- Inner model: haiku, effort low · 9 nodes (cap 9), 0 buggy
- Inner spend: 472,481 tokens, 9 agents, 29m0s wall clock
- Sandbox: public materials only (verified by `rsi-sandbox.sh`); deny-private hook suite 29/29

## Scores

| Split | Score | Notes |
| --- | --- | --- |
| Public (inner-visible) | 0.964762 | best = node-0 (First Fit Decreasing draft); optimal on 3/5 instances |
| Private (outer-only) | 0.937937 | 7 unseen instances, up to 120 items; 1.0 on prv-uniform-15, weakest 0.86 on prv-bimodal-100 |

Private scoring executed outside the inner context via
`RSI_OUTER_LOOP=1 rsi-score.sh --private` after the run ended.

## Observations

1. **Public plateau, as the paper predicts for AIDE0**: all 5 drafts independently converged
   on FFD/BFD (identical 0.964762), and all 4 improve nodes (all children of node-0, greedy
   selection) failed to beat it despite escalating local search. Greedy single-lineage search
   plus full-history context produced zero progress after the draft phase — exactly the
   headroom the outer loop is supposed to exploit (bandit lineages, fork-on-stall, context
   engineering).
2. **Generalization gap** (0.965 → 0.938) concentrated on bimodal instances — informative
   signal for the private split, invisible to the inner agent. Good: the split is doing its job.
3. **Harness failures found and fixed**: the Workflow runtime delivers `args` as a JSON
   string; the generation script now accepts both encodings (two instant failures before the
   fix, runs `wf_6fd076d5-b97`, `wf_06bcb22b-9b4`).
4. All agents returned real scorer output (structured schema enforced); no fabricated scores
   observed — every reported public score reproduces from the committed solutions.

## M1 exit criteria status

- [x] gen-000 solves the task end-to-end under a token cap
- [x] private score computed strictly outside the inner agent's context
- [x] deny hook behaviorally tested (29 cases)
- [x] `/rsi:autoresearch` command wrapper (added with this record)
