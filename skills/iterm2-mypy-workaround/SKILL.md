---
name: iterm2-mypy-workaround
description: |
  Fix mypy "Name iterm2.Session is not defined" or "Name iterm2.Window is not defined"
  errors in iterm-c4 project. Use when: (1) mypy fails with name-defined errors on
  iterm2 types despite ignore_missing_imports=true in pyproject.toml, (2) working with
  the iTerm2 Python API in type-annotated code. The iterm2 package lacks proper type
  stubs, requiring a specific import + type-ignore pattern.
author: Claude Code
version: 1.0.0
date: 2026-02-01
---

# iterm2 Package mypy Type Resolution

## Problem

The `iterm2` Python package doesn't ship proper type stubs. Even with
`ignore_missing_imports = true` configured for `iterm2.*` in mypy settings,
using `iterm2.Session`, `iterm2.Window`, `iterm2.App` etc. in type annotations
causes `error: Name "iterm2.X" is not defined [name-defined]`.

## Context / Trigger Conditions

- Project uses `iterm2>=2.7` package
- mypy configured with `strict = true`
- `[[tool.mypy.overrides]]` has `module = ["iterm2.*"]` with `ignore_missing_imports = true`
- Error: `Name "iterm2.Session" is not defined [name-defined]`

## Solution

Use this pattern (established in iterm-c4's `discovery.py`):

```python
from __future__ import annotations

import iterm2  # noqa: TC002

# On function signatures using iterm2 types:
async def my_func(
    session: iterm2.Session,  # type: ignore[name-defined]
) -> None:
    ...
```

Key points:

1. Import `iterm2` at module level with `# noqa: TC002` (suppresses ruff's
   "move to TYPE_CHECKING" rule)
2. Add `# type: ignore[name-defined]` on each line using iterm2 types in signatures
3. Do NOT put `import iterm2` inside `if TYPE_CHECKING:` — mypy still can't resolve it

## Verification

- `uv run mypy iterm_c4/your_module.py` passes with no errors
- `uv run ruff check iterm_c4/your_module.py` passes (TC002 suppressed)

## Notes

- This pattern is used consistently across iterm-c4: discovery.py, monitor.py, session.py
- The `from __future__ import annotations` is required for all other TYPE_CHECKING imports
  to work (ClaudeSession, PermissionPrompt, etc.)
- Ruff's TC003 rule (move stdlib imports to TYPE_CHECKING) works fine for collections.abc
  imports but NOT for iterm2
