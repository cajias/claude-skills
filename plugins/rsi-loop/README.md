# rsi-loop

AIDE²-style recursive self-improvement loop for Claude Code: an outer-loop agent iteratively
rewrites an inner tree-search research agent, keeping rewrites only when they beat the incumbent
on **private held-out scores** under a **fixed budget**, with layered reward-hacking defenses and
RSI-ladder measurement.

**Status: M1–M2 shipped.** The standalone inner agent and the outer step (propose → evaluate →
verify → select) are implemented and have a completed run on file; M3–M5 (full task battery,
`/rsi:run`, measurement, ignition test) are still to come. The build roadmap and current
milestone state live in [docs/PLAN.md](docs/PLAN.md) and
[docs/CONTINUATION.md](docs/CONTINUATION.md).

Method sources: [Weco AIDE² report](https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement),
[4-level RSI ladder](https://www.weco.ai/blog/4-levels-of-recursive-self-improvement),
[explainx summary](https://explainx.ai/blog/weco-aide2-recursive-self-improvement-rsi-ladder-july-2026).

## Commands

Shipped:

- `/rsi:autoresearch <task-dir>` — standalone AIDE-style inner agent: tree-search autoresearch
  on any task with a `task.md` and `score.py` (runs the current best evolved generation)
- `/rsi:init` — scaffold a run (generations, task battery, ledger)
- `/rsi:step [n]` — execute outer-loop steps (propose → evaluate → verify → select)

Planned (M3–M5, see PLAN.md):

- `/rsi:run` — loop `/rsi:step` until budget/steps exhausted
- `/rsi:report` — lineage, scores, and falsifiable RSI-ladder evidence
- `/rsi:ignite` — the Level-2 "ignition" swap test

## Safety

Inner agents run in sandboxes built from public materials only; the plugin's PreToolUse hook
(`hooks/deny-private.py`) denies any read of a `private/` split or write to the immutable
harness. Only the outer loop scores private data, gated behind `RSI_OUTER_LOOP=1`. The firewall
is covered by `tests/test-deny-hook.sh` and the scorer by `tests/test-scorer.sh` (both run in CI).
