---
name: rsi-loop
description: "AIDE²-style recursive self-improvement outer loop: propose a rewrite of the inner research agent, evaluate it on a task battery under a fixed budget, and keep it only if it beats the incumbent on private held-out scores. Use when the user wants to run or understand an rsi-loop outer step, or invokes /rsi:init, /rsi:step, or /rsi:run. See docs/PLAN.md."
---

# rsi-loop

The outer-loop protocol of the rsi-loop plugin (implemented as of M2; the full
build roadmap and remaining milestones are in [`docs/PLAN.md`](../../docs/PLAN.md)).

One outer step, driven by [`commands/rsi-step.md`](../../commands/rsi-step.md):

1. **Propose** — the `rsi-proposer` agent rewrites the incumbent generation
   (`best`) as one focused mutation, guided by the run ledger.
2. **Evaluate** — the candidate's inner tree-search agent runs on each task in
   a fresh public-only sandbox under a fixed token budget; collect public scores.
3. **Private scoring** — the outer harness (never the inner agent) scores the
   winner on the held-out `private/` split.
4. **Verify** — the `rsi-verifier` agent adversarially re-checks the claimed
   winner for reward hacking before it can be accepted.
5. **Select** — accept only if the private aggregate strictly beats the
   incumbent and the verifier is clean; append the ledger line either way.

Scaffold a run with [`/rsi:init`](../../commands/rsi-init.md), then run steps
with [`/rsi:step`](../../commands/rsi-step.md). Expect most steps to be
rejections — that is faithful AIDE² behavior. The first completed run is
recorded in [`docs/experiments/run-001/`](../../docs/experiments/run-001/).

Private scores never enter any inner-agent context: inner agents run in
sandboxes built from public materials only, and the plugin's PreToolUse hook
denies private-split access. Only the outer loop, via `RSI_OUTER_LOOP=1`,
scores private data.
