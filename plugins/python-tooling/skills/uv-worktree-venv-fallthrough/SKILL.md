---
name: uv-worktree-venv-fallthrough
description: |
  Fix for phantom Python test failures in fresh git worktrees of
  uv-managed projects, caused by `uv run` falling through to a
  PATH-resolved command (e.g. homebrew Python 3.9's pytest) when the
  worktree's `.venv` doesn't have the command installed. Use when:
  (1) `uv run pytest --collect-only -q` in a freshly-created worktree
  reports `ModuleNotFoundError: No module named 'msgspec'` (or any
  other project runtime dep) on test files that import the package;
  (2) you see `ImportError: cannot import name 'UTC' from 'datetime'`
  or `dataclass() got an unexpected keyword argument 'slots'` despite
  `pyproject.toml` requiring Python 3.10+/3.12+;
  (3) the same `uv run pytest` succeeds on the main worktree but fails
  on a sibling worktree;
  (4) `which pytest` (or `which ruff`, `which mypy`) inside the
  worktree resolves to `/opt/homebrew/bin/...` instead of
  `<worktree>/.venv/bin/...`;
  (5) you're orchestrating parallel agents in worktree-isolation mode
  and they report wildly inconsistent test results vs the main tree.
  Root cause is `uv run`'s fallthrough to `$PATH` when the venv doesn't
  have the command, combined with empty `.venv` in fresh worktrees.
  Fix is one command: `uv sync --extra dev`.
author: Claude Code
version: 1.0.0
date: 2026-05-09
---

# uv worktree venv fallthrough

## Problem

`uv run <cmd>` in a uv-managed Python project will run `<cmd>` from
the project's `.venv/bin/` if it exists there. **If it doesn't, `uv
run` falls through to `$PATH`.** Combined with `git worktree add`
(which gives the new worktree an empty `.venv`), this silently picks
up the system Python's `pytest` / `ruff` / `mypy` — typically
homebrew's Python 3.9 on macOS — instead of the project's pinned
3.12+. The wrong-Python interpreter then can't import 3.10+/3.12+
language features, producing errors that LOOK like code bugs but
are actually environment bugs.

This is especially painful in parallel-agent workflows: each agent's
worktree starts with an empty venv, and every agent re-discovers the
same trap before any test runs.

## Trigger conditions

Any of these:

- `uv run pytest --collect-only -q` in a fresh worktree raises
  `ModuleNotFoundError` on a runtime dep that's clearly listed in
  `pyproject.toml`:

  ```text
  ImportError while importing test module 'tests/test_schemas.py'.
  ModuleNotFoundError: No module named 'msgspec'
  ```

- The error mentions a Python feature your `pyproject.toml` requires
  by minimum version, but the runtime is older:

  ```text
  ImportError: cannot import name 'UTC' from 'datetime'
  TypeError: dataclass() got an unexpected keyword argument 'slots'
  ```

- `which pytest` from inside the worktree resolves to
  `/opt/homebrew/bin/pytest` or `/usr/bin/pytest`, not
  `<worktree>/.venv/bin/pytest`.

- The exact same `uv run pytest` invocation from the project's main
  worktree (or `~/.../<repo>` checkout) succeeds.

- A subagent dispatched to a worktree reports test-collection failures
  that the main session can't reproduce on `main`.

## Root cause

`uv run` resolves commands in this order:

1. `<cwd>/.venv/bin/<cmd>`
2. `$PATH`

When you run `git worktree add` (or any tool that creates an isolated
worktree — including the `isolation: "worktree"` option on the Agent
tool), the new worktree:

- Inherits the repo's `pyproject.toml` and `uv.lock`.
- Does **NOT** inherit the parent's `.venv` directory.
- Gets an empty `.venv` (or none) until you run `uv sync` for the
  first time.

So `uv run pytest` sees no `.venv/bin/pytest` and falls through to
homebrew's `pytest`, which is bound to homebrew's Python 3.9. That
Python tries to import the project's package, hits 3.10+ language
features (`datetime.UTC`, `dataclass(slots=True)`, `match` statements,
PEP 604 `X | Y` unions, etc.), and crashes.

The error messages point at the project's source files, so the
natural reaction is "the project's code is broken" — but the project
code is fine; it's just being parsed by the wrong interpreter.

## Solution

One command, run from inside the worktree, before any `uv run`:

```bash
cd <worktree>
uv sync --extra dev
```

This populates `<worktree>/.venv/` with the project's runtime + dev
dependencies, including a venv-local `pytest` binary that's bound to
the correct Python (the one matching `pyproject.toml`'s
`requires-python`).

After `uv sync`, the next `uv run pytest` resolves to
`<worktree>/.venv/bin/pytest` and the trap is gone.

## Verification

```bash
# 1. .venv now has pytest
ls .venv/bin/pytest && head -1 .venv/bin/pytest
# Expect first line is a shebang pointing into the worktree's .venv:
#   #!<worktree>/.venv/bin/python

# 2. uv run resolves correctly
which pytest             # may still show homebrew (PATH unchanged)
uv run which pytest      # MUST show <worktree>/.venv/bin/pytest

# 3. Collection is green
uv run pytest --collect-only -q | tail -3
# Expect: "<N> tests collected" with no ModuleNotFoundError
```

## Implication for parallel-agent workflows

Every agent dispatched with `isolation: "worktree"` (or any flow
that calls `git worktree add` before running Python commands) MUST
run `uv sync --extra dev` as its first command, before any other
`uv run` invocation. Otherwise the agent will spend cycles
investigating phantom failures that don't exist on `main`.

**Prompt template addition** (paste into agent dispatch prompts that
target uv-managed Python repos):

```text
First action in the worktree: `uv sync --extra dev`. Do not skip
this — fresh worktrees have an empty .venv and `uv run` will fall
through to system Python (often the wrong version), producing
phantom ModuleNotFoundError / ImportError that look like code bugs.
```

A repo-level convenience: a `Makefile` target or
`scripts/init-worktree.sh` that wraps `uv sync --extra dev` so the
agent only has to run one named command.

## Example — full diagnostic chain

A subagent reports:

```text
"pre-existing pytest collection errors on main"
- test_schemas.py: ModuleNotFoundError: No module named 'msgspec'
- test_orchestrator.py: ImportError: cannot import name 'UTC' from 'datetime'
- test_team_loader.py: TypeError: dataclass() got an unexpected keyword argument 'slots'
```

Diagnostic steps:

```bash
# Reproduce in main worktree?
cd ~/Projects/workspace/<repo>
uv run pytest --collect-only -q | tail -3
# "174 tests collected" — clean. So it's worktree-specific.

# In the failing worktree:
cd <worktree>
which pytest                  # /opt/homebrew/bin/pytest  ← system Python!
uv run which pytest           # /opt/homebrew/bin/pytest  ← uv falling through!
ls .venv/bin/pytest 2>&1      # ls: .venv/bin/pytest: No such file or directory

# The fix:
uv sync --extra dev           # ~10s in this repo
uv run which pytest           # <worktree>/.venv/bin/pytest  ← correct
uv run pytest --collect-only -q | tail -3
# "174 tests collected" — green.
```

Total resolution time: under a minute once the pattern is
recognized. Without this skill, expect 20–40 minutes chasing the
"`UTC` not in `datetime`" error through the codebase before realizing
it's an environment bug.

## Notes

- The trap is uv-specific. Pip / poetry don't have the same
  fallthrough — `pip install` failures are loud, and `poetry run`
  raises if the env isn't set up. uv's fallthrough is a feature
  (intentional convenience for ad-hoc invocations) that becomes a
  trap inside worktrees.
- It also applies to commands other than pytest: `uv run ruff`,
  `uv run mypy`, `uv run vulture`, `uv run python -m <module>`, etc.
  All of them fall through to PATH if the venv lacks the binary.
- This is unrelated to `uv.lock` drift between worktree and main —
  the lock file is shared (it's tracked in git), only the
  realized `.venv` is per-worktree.
- If your project doesn't have `[project.optional-dependencies]
  dev = [...]`, use `uv sync` (no `--extra`) — same effect for
  runtime deps, just without dev tools. But you usually want dev
  tools in a worktree because you're about to run them.
- Recently-added uv versions (≥ 0.5) hash the venv against the
  worktree path; if you symlink `.venv` from main into the worktree
  to "share" envs, expect uv to refuse and rebuild. Don't try to
  sidestep `uv sync` with a symlink — just run it.

## References

- uv `run` semantics:
  <https://docs.astral.sh/uv/reference/cli/#uv-run>
- uv `sync` semantics:
  <https://docs.astral.sh/uv/reference/cli/#uv-sync>
- git worktree:
  <https://git-scm.com/docs/git-worktree>
- Concrete origin: investigation of "pre-existing pytest collection
  errors" in `cajias/nautilus-competition` worktree (May 2026). The
  worktree had no `.venv/bin/pytest`, so `uv run pytest` fell through
  to homebrew's Python 3.9, which couldn't import `msgspec` (not
  installed in 3.9's site-packages) and crashed on
  `dataclass(slots=True)` (3.9 lacks the kwarg). After `uv sync
  --extra dev`, all 174 tests collected green and the "errors" were
  retroactively classified as a NO-OP environmental issue.
