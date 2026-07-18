# rsi-loop (placeholder)

AIDE²-style recursive self-improvement loop for Claude Code: an outer-loop agent iteratively
rewrites an inner tree-search research agent, keeping rewrites only when they beat the incumbent
on **private held-out scores** under a **fixed budget**, with layered reward-hacking defenses and
RSI-ladder measurement.

**Status: design phase.** Nothing is implemented yet. The full build spec lives in
[docs/PLAN.md](docs/PLAN.md).

Method sources: [Weco AIDE² report](https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement),
[4-level RSI ladder](https://www.weco.ai/blog/4-levels-of-recursive-self-improvement),
[explainx summary](https://explainx.ai/blog/weco-aide2-recursive-self-improvement-rsi-ladder-july-2026).

Planned surface:

- `/rsi:init` — scaffold a run (generations, task battery, ledger)
- `/rsi:step` / `/rsi:run` — execute outer-loop steps (propose → evaluate → select)
- `/rsi:report` — lineage, scores, and falsifiable RSI-ladder evidence
- `/rsi:ignite` — the Level-2 "ignition" swap test

Not listed in the marketplace until M1+ lands (see plan milestones).
