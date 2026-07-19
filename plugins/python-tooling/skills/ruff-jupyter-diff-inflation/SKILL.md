---
name: ruff-jupyter-diff-inflation
description: |
  Prevent or diagnose massive PR diffs (700-1000+ lines per .ipynb) when
  running `ruff check --fix` or `make lint-fix` in a Python project that
  checks in Jupyter notebooks. Use when: (1) a lint cleanup PR explodes
  from a small expected diff to thousands of lines; (2) `git diff` of a
  notebook shows `source` field changing from a single string to an array
  of lines (or vice versa); (3) deciding how to scope ruff in a project
  with both .py files and committed notebooks. Covers the structural
  Jupyter source-format normalization that ruff performs and the
  pyproject.toml change to suppress it.
author: Claude Code
version: 1.0.0
date: 2026-04-14
---

# Ruff Jupyter Diff Inflation

## Problem

`ruff check --fix` (and therefore `make lint-fix`, `make validate`, or any
wrapper) **canonicalizes Jupyter notebook cell `source` fields** from the
compact single-string form to the canonical line-array form. This is a
structural reformat of the underlying JSON, not a code change. The semantic
change (e.g. removing one unused import) is buried inside hundreds of lines
of `"source": "x\n"` → `"source": ["x\n", ...]` reformatting per cell.

Concretely: a one-line F401 fix in a notebook can produce a 938-line diff.

This is invisible until you run `git diff --stat` after `--fix` and see
diffs like:

```
strategies/crypto/rvs_swing_backtest.ipynb    | 938 ++++++++++++++++++++++++--
strategies/crypto/shock_guard_backtest.ipynb  | 682 +++++++++++++++++--
strategies/crypto/timesfm_grid_backtest.ipynb | 744 +++++++++++++++++---
```

…when you only expected to fix a handful of import statements.

## Context / Trigger Conditions

- A "tiny" lint-cleanup PR balloons to 5-15× its expected line count
- `git diff` on a `.ipynb` shows reordering of JSON keys (`metadata`
  before/after `source`), addition of `"execution_count": null`, and
  source-string → source-array conversion
- The codebase commits executed notebooks (with outputs) rather than
  stripping them
- `ruff` was added or updated, or its config recently changed
- You're trying to land a focused fix and the notebook diff is making
  review impractical

## Solution

**Exclude notebooks from ruff entirely**, in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"
# Notebooks are exploratory research artifacts; their formatting and lint
# concerns are handled separately (nbstripout, nbqa, or manual curation).
# Ruff's --fix canonicalizes the source field and produces large, review-
# unfriendly diffs, so we skip them entirely here.
extend-exclude = ["*.ipynb"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4"]
ignore = ["E501"]
```

**Critical:** `extend-exclude` must be on `[tool.ruff]` (the top-level
section), not on `[tool.ruff.lint]`. The lint subsection has its own
`exclude` but `extend-exclude` is a top-level concept.

If you already ran `--fix` and the notebook diffs are staged or in the
working tree:

```bash
git checkout -- path/to/notebook.ipynb  # revert each affected notebook
```

Then add the `extend-exclude` config and re-run lint to verify it skips
the notebooks.

## Verification

```bash
# Should not list any .ipynb files
make lint 2>&1 | grep -i ipynb

# Should match the expected scope (just .py files)
git diff --stat -- ':!*.ipynb'
```

The PR diff after this fix should match what you'd expect from the actual
code changes (a few files, a few dozen lines), not the inflated form.

## Example

Real session: PR aimed to fix 102 ruff errors on `main`. Auto-fix yielded
33 fixes, but `git diff --stat` showed:

```
nautilus/pyproject.toml                       |  11 +
nautilus/src/nautilus_trading/live/runner.py  |   2 +-
strategies/crypto/kronos/backtest.py          |  13 +-
strategies/crypto/timesfm_grid.py             |   4 +-
strategies/crypto/rvs_swing_backtest.ipynb    | 938 +++...
strategies/crypto/shock_guard_backtest.ipynb  | 682 +++...
strategies/crypto/timesfm_grid_backtest.ipynb | 744 +++...
```

The 4 .py changes were the real fix (33 lines net). The 3 notebooks were
all structural noise. After `git checkout -- *.ipynb` and adding
`extend-exclude = ["*.ipynb"]`, the PR became 4 files, 21 +/8 - lines —
reviewable in a minute instead of unreviewable in an hour.

## Notes

- **Why this matters specifically for notebooks**: Jupyter allows two
  equivalent forms for cell `source`: a compact JSON string with embedded
  `\n`, or a JSON array of lines. nbformat tools sometimes write the
  compact form (it's smaller); ruff always normalizes to the array form.
  Both are valid Jupyter, but switching form shows up as a massive diff.

- **Alternative paths considered and rejected**:
  - Per-file-ignores for notebook-typical rules (E402, B007, F811, F841,
    C408, C416, B905) does silence errors but does NOT prevent the
    `--fix` reformat from running on remaining rules. The reformat is
    triggered by *any* fix touching the notebook.
  - `nbqa` + `nbstripout` are purpose-built for notebook lint hygiene and
    avoid the reformat issue. Worth adopting in a separate PR if notebook
    quality enforcement is desired.

- **Closely related gotcha — sys.path bootstrap E402**: Runner scripts
  that need to inject the repo root into `sys.path` before importing the
  package being tested will trigger E402 unavoidably. The clean fix is
  per-file-ignores, e.g.:

  ```toml
  [tool.ruff.lint.per-file-ignores]
  "../strategies/crypto/kronos/backtest.py" = ["E402"]
  "../strategies/crypto/kronos/paper_trade.py" = ["E402"]
  ```

  `noqa: E402` on each import line works too but pollutes the file.
  Per-file-ignores capture the intent ("this is a bootstrap script") at
  config level. Path is relative to the `pyproject.toml` location.

- **Vulture sibling gotcha**: signal handlers (`def _handler(signum,
  frame)`) trigger `unused variable` warnings from vulture even though
  the args are required by Python's signal API. Fix: rename to
  `_signum, _frame` (underscore convention) — silences vulture without
  needing a whitelist entry.

## References

- [Ruff: extend-exclude](https://docs.astral.sh/ruff/settings/#extend-exclude)
- [Ruff: per-file-ignores](https://docs.astral.sh/ruff/settings/#per-file-ignores)
- [Jupyter notebook format spec — cell source](https://nbformat.readthedocs.io/en/latest/format_description.html#cell-types)
- [nbqa — run any standard Python code quality tool on a Jupyter notebook](https://nbqa.readthedocs.io/)
