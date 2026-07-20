# rsi-loop

AIDE²-style recursive self-improvement loop for Claude Code: an outer-loop agent iteratively
rewrites an inner tree-search research agent, keeping rewrites only when they beat the incumbent
on **private held-out scores** under a **fixed budget**, with layered reward-hacking defenses and
RSI-ladder measurement.

**Status: M1–M3 shipped; M4–M5 machinery built.** The standalone inner agent, the outer step
(propose → evaluate → verify → select), the full three-family task battery, the unattended
`/rsi:run` driver, robust aggregation + reward-hack outlier detection, the hand-tuned
`gen-human` baseline, the `holdout-tasks/` generalization set, `/rsi:report`, and `/rsi:ignite`
are all implemented. The build roadmap and current milestone state live in
[docs/PLAN.md](docs/PLAN.md) and [docs/CONTINUATION.md](docs/CONTINUATION.md).

Method sources: [Weco AIDE² report](https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement),
[4-level RSI ladder](https://www.weco.ai/blog/4-levels-of-recursive-self-improvement),
[explainx summary](https://explainx.ai/blog/weco-aide2-recursive-self-improvement-rsi-ladder-july-2026).

## Commands

- `/rsi:autoresearch <task-dir>` — standalone AIDE-style inner agent: tree-search autoresearch
  on any task with a `task.md` and `score.py` (runs the current best evolved generation)
- `/rsi:init` — scaffold a run (generations, task battery, ledger)
- `/rsi:step [n]` — execute outer-loop steps (propose → evaluate → verify → select)
- `/rsi:run` — drive `/rsi:step` unattended, bounded by `--max-steps`, an inner-token
  `--budget`, and a `--plateau` stop condition; resume-aware for multi-day runs
- `/rsi:report` — lineage, scores, and falsifiable RSI-ladder evidence (slope vs. the
  hand-tuned baseline, holdout generalization deltas, hack-rate trend)
- `/rsi:ignite` — the Level-2 "ignition" swap test (best generation into the proposer role)

## Task battery

Three AIDE² families under `tasks/`, each with a public/private split and an immutable scorer:
`bin-packing` (heuristic optimization), `tabular-classification` (ML engineering; public =
5-fold CV, private = held-out test set), and `instruction-routing` (harness engineering; the
solution is a tiny agent scaffold). Second-order generalization is measured on `holdout-tasks/`
— one unseen task per family plus a far-OOD time-series forecast — which no run ever trains on.

## Safety

Inner agents run in sandboxes built from public materials only; the plugin's PreToolUse hook
(`hooks/deny-private.py`) denies any read of a `private/` split or write to the immutable
harness. Only the outer loop scores private data, gated behind `RSI_OUTER_LOOP=1`. Integrity is
DETECTION, not prevention (agents share the harness uid): `rsi-check-integrity.sh` anchors
scorers/data to git HEAD or a checksum manifest, and private scoring refuses a tampered harness.
CI runs the full suite — `test-deny-hook.sh`, `test-scorer.sh`, `test-integrity.sh`,
`test-aggregate.sh`, and `test-report.sh`.
