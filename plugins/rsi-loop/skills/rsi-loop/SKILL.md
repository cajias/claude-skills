---
name: rsi-loop
description: "AIDE²-style recursive self-improvement outer loop: propose a rewrite of the inner research agent, evaluate it on a heterogeneous task battery under a fixed budget, and keep it only if it beats the incumbent on private held-out scores. Use when the user wants to run or understand an rsi-loop outer step, or invokes /rsi:init, /rsi:step, or /rsi:run. See docs/PLAN.md."
---

# rsi-loop

The outer-loop protocol of the rsi-loop plugin. The full build roadmap and
milestones are in [`docs/PLAN.md`](../../docs/PLAN.md).

One outer step, driven by [`commands/rsi-step.md`](../../commands/rsi-step.md):

1. **Propose** — the `rsi-proposer` agent rewrites the incumbent generation
   (`best`) as one focused mutation, guided by the run ledger.
2. **Evaluate** — the candidate's inner tree-search agent runs on each task in
   a fresh public-only sandbox under a fixed token budget; collect public scores.
3. **Private scoring** — the outer harness (never the inner agent) scores the
   winner on the held-out `private/` split; the robust cross-seed aggregate
   (`scripts/rsi-aggregate.py`) is the selection statistic.
4. **Verify** — the `rsi-verifier` agent adversarially re-checks the claimed
   winner for reward hacking before it can be accepted: the <50%-of-claim rule,
   a hard-coding audit, scorer-integrity diffs, and the statistical too-good
   outlier detector (`rsi-aggregate.py --flag-outliers`).
5. **Select** — accept only if the private aggregate strictly beats the
   incumbent and the verifier is clean; append the ledger line either way.

## Task battery (three AIDE² families)

The battery under `tasks/` spans all three families the paper uses to force
generalizable improvements:

- **bin-packing** — heuristic/combinatorial optimization (ALE-Bench analog).
- **tabular-classification** — ML engineering; public score is 5-fold CV
  accuracy, private is a held-out test set (MLE-Bench analog).
- **instruction-routing** — harness engineering; the solution _is_ a tiny agent
  scaffold, scored on unseen phrasings in private (the self-referential family).

## Running

Scaffold a run with [`/rsi:init`](../../commands/rsi-init.md), take single steps
with [`/rsi:step`](../../commands/rsi-step.md), or drive many steps unattended
with [`/rsi:run`](../../commands/rsi-run.md) (bounded by `--max-steps`,
`--budget`, and a `--plateau` stop condition; `--seeds K` cuts tiny-battery
noise). Expect most steps to be rejections — that is faithful AIDE² behavior.
The first completed run is recorded in
[`docs/experiments/run-001/`](../../docs/experiments/run-001/).

Private scores never enter any inner-agent context: inner agents run in
sandboxes built from public materials only, and the plugin's PreToolUse hook
denies private-split access. Only the outer loop, via `RSI_OUTER_LOOP=1`,
scores private data.
