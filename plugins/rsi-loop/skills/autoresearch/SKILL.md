---
name: autoresearch
description: "Standalone AIDE-style autoresearch agent: tree-search over candidate solutions (draft/debug/improve operators) for any task directory with a task.md and score.py — ML engineering, heuristic optimization, or harness engineering. Runs the current best generation evolved by the rsi-loop outer loop (falling back to baseline/gen-000). Use when the user wants to solve an optimization task by iterative search, or invokes /rsi:autoresearch."
---

# autoresearch

Runs the rsi-loop inner agent standalone: point it at a task directory containing `task.md`,
`score.py`, and `public/`, and it executes tree-search autoresearch (parallel drafts →
greedy debug/improve loop) under a token budget, returning the best-scoring solution.

Follow the procedure in [`commands/rsi-autoresearch.md`](../../commands/rsi-autoresearch.md):
sandbox from public materials only (`scripts/rsi-sandbox.sh`), launch the generation's
`inner-agent.workflow.mjs` with `{sandbox, genDir, taskName, seed, policy}`, report the best
node's public score. Private scoring is outer-loop-only (`RSI_OUTER_LOOP=1`) and never enters
the inner agent's context.

The generation is resolved through the run's `best` pointer (falling back to
`baseline/gen-000`), so improvements discovered by the `/rsi:run` outer loop flow to standalone
users automatically. First verified run: see
[`docs/experiments/m1-smoke-bin-packing.md`](../../docs/experiments/m1-smoke-bin-packing.md).

Design details: [`docs/PLAN.md`](../../docs/PLAN.md), §3 "`autoresearch` as a standalone skill".

Naming note: this is distinct from the third-party
[uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) skill (a single-level
metric hill-climb loop, evaluated in PLAN.md §5.1 as a candidate outer-loop chassis). If that
plugin is adopted in M2, this skill will be renamed to avoid trigger collision.

If invoked before implementation lands: explain that the plugin is in design phase and point the
user to the plan.
