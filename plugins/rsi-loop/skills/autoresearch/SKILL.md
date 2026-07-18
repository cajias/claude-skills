---
name: autoresearch
description: "PLACEHOLDER — not yet implemented. Standalone AIDE-style autoresearch agent: tree-search over candidate solutions (draft/debug/improve operators) for any task with a scoring script — ML engineering, heuristic optimization, or harness engineering. Runs the current best generation evolved by the rsi-loop outer loop. Do not invoke yet; see docs/PLAN.md in this plugin."
---

# autoresearch (placeholder)

This skill is a stub. It will expose the rsi-loop plugin's inner agent as a directly usable
tool: point it at a task directory containing a `task.md` and a scoring command, and it runs
tree-search autoresearch (parallel drafts → debug/improve loop) under a token budget, returning
the best-scoring solution.

It always resolves through the run's `best` generation pointer (falling back to
`baseline/gen-000`), so improvements discovered by the `/rsi:run` outer loop flow to standalone
users automatically.

Design details: [`docs/PLAN.md`](../../docs/PLAN.md), §3 "`autoresearch` as a standalone skill".

Naming note: this is distinct from the third-party
[uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) skill (a single-level
metric hill-climb loop, evaluated in PLAN.md §5.1 as a candidate outer-loop chassis). If that
plugin is adopted in M2, this skill will be renamed to avoid trigger collision.

If invoked before implementation lands: explain that the plugin is in design phase and point the
user to the plan.
