---
name: importlib-reload-class-identity
description: |
  Diagnose and fix the silent class-identity drift caused by `importlib.reload()`
  on modules that define classes whose instances live elsewhere. Use when:
  (1) a pytest fixture uses `importlib.reload(some_module)` to "flush caches"
  and downstream tests then fail with `isinstance` checks rejecting objects
  that LOOK correct; (2) you see a diagnostic warning of the form "expected X,
  got X" — same class name, different class identity (`type(obj).__name__ ==
  "X"` but `obj is not isinstance(X)`); (3) one fragile test fixture causes
  dozens-to-hundreds of cascading failures in unrelated test files; (4) tests
  pass in isolation but fail when run as part of the full suite, with order
  dependence pointing at the reload site; (5) you have an entry-point /
  plugin / discovery system whose post-reload registry is empty even though
  the underlying entries still exist. Covers root cause (Python class objects
  are first-class identities; reload mints new ones; pre-reload instances
  keep old identity), the diagnostic signature, and the canonical fix
  (subprocess isolation via `subprocess.run([sys.executable, "-c", ...])`
  or `pytest-forked` — never `importlib.reload` for class-exposing modules).
author: Claude Code
version: 1.0.0
date: 2026-05-08
---

# importlib.reload Class-Identity Drift

## Problem

`importlib.reload(some_module)` recreates everything in `some_module` — including
the class objects defined there. The new class is a different Python object from
the original, even though it has the same `__name__`, `__qualname__`, and
identical fields. Any instance created **before** the reload retains a reference
to the **old** class. After the reload:

```python
import some_module
old_instance = some_module.SomeClass(value=1)

import importlib
importlib.reload(some_module)

isinstance(old_instance, some_module.SomeClass)  # False ← THE BUG
type(old_instance).__name__ == some_module.SomeClass.__name__  # True ← MISLEADING
type(old_instance) is some_module.SomeClass  # False
```

This is the same well-known footgun behind "isinstance lies after reload" (see
PEP 489 motivation), but it bites hardest in **plugin / entry-point discovery
systems** that:

1. Define a class (e.g. `StrategySpec`, `Plugin`, `Resource`) in module A.
2. Expect external modules to expose constants like `MY_PLUGIN = SomeClass(...)`.
3. Discover those constants at import time and store them.
4. Defensively check `isinstance(loaded_obj, SomeClass)` to validate the
   discovered object.

If anything later calls `importlib.reload(module_A)`, the discovery code sees
the **new** `SomeClass`, but the constants in the strategy modules still hold
the **old** class. The defensive `isinstance` check rejects every entry, and
the registry ends up empty — usually with a diagnostic warning that's
maddeningly unhelpful: *"expected SomeClass, got SomeClass"*.

## Context / Trigger Conditions

You are likely hitting this bug if any of the following:

- A pytest fixture flushes caches via something like

  ```python
  importlib.reload(specs_module)
  importlib.reload(strategies_module)
  importlib.reload(cli_module)
  ```

  and post-fixture tests start failing.
- Tests pass in isolation (`pytest path/to/test.py::test_x`) but fail in the
  full suite — order-dependent breakage points at one reload site.
- A discovery / entry-point / registry function returns empty data after
  some test runs, even though the entries are still installed and visible
  via `importlib.metadata.entry_points()` or equivalent.
- You see warnings like `expected StrategySpec, got StrategySpec` /
  `expected Plugin, got Plugin` in test logs — same name, different class.
- A single broken test fixture cascades into dozens or hundreds of failures
  across unrelated test files.
- You diagnose with `print(id(type(obj)), id(SomeClass))` and they differ
  while names match.

## Solution

**Don't reload the module. Use subprocess isolation instead.**

`importlib.reload` is fundamentally fragile for any module that defines a
class whose instances exist elsewhere. The fix isn't to make reload smarter
— it's to give each invalidation-needing test its own Python process.

### Pattern A — subprocess.run with inline -c

Best for small assertions. Each invocation gets a fresh import graph:

```python
import subprocess
import sys

def test_external_plugin_is_discovered(installed_plugin: None) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from my_pkg.discovery import REGISTRY; "
            "assert 'my_external' in REGISTRY, sorted(REGISTRY)",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"subprocess assertion failed:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
```

### Pattern B — pytest-forked or pytest-xdist --boxed

Best for whole tests that need isolation. Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = ["pytest-forked", ...]
```

Then mark tests:

```python
@pytest.mark.forked  # each test runs in its own subprocess
def test_plugin_discovery():
    ...
```

### Pattern C — pytest-xdist with --dist=loadfile

Best for entire test files that need isolation. Add `--forked` or
`--dist=loadfile` to `pyproject.toml`'s `addopts`. Run-time cost: minimal
for small test counts.

### Anti-pattern — "evict more sys.modules" approach

Tempting but a trap. To make reload work, you'd need to evict every module
that:

1. Imports the reload target, OR
2. Imports a class from the reload target, OR
3. Holds an instance of any class defined in the reload target, OR
4. Holds an instance of any class defined in a module that itself imports
   the reload target...

This list is unbounded and grows whenever new code touches the registry.
Subprocess isolation has none of these failure modes.

## Verification

After applying the fix:

1. Run the previously-failing tests in isolation — they should still pass.
2. Run the full suite — pre-existing cascading failures should collapse
   to zero.
3. Search the codebase for other `importlib.reload` calls in test code:

   ```bash
   grep -rn "importlib.reload\|reload(" tests/ --include="*.py"
   ```

   Audit each one. If the reloaded module exports a class whose instances
   live elsewhere, fix it the same way.

## Example — what happened in nautilus-trading 2026-05-08

**Setup:**

- `nautilus_trading.cli._strategy_specs` defines `class StrategySpec`.
- 9 strategy modules under `strategies/{forex,crypto}/` each export
  `STRATEGY_SPEC = StrategySpec(...)` — instances created at the strategies'
  import time.
- An entry-point group `nautilus_trading.strategies` lets external packages
  contribute strategies the same way.
- `_discover_strategy_specs()` at module load time iterates entry-points,
  calls `ep.load()`, validates `isinstance(spec, StrategySpec)`, builds a
  registry dict.

**The bug:**

- A pytest fixture for an external-strategy smoke test ran
  `importlib.reload(nautilus_trading.cli._strategy_specs)` to "flush the
  registry cache" so the freshly-installed external strategy would be
  discovered.
- The reload created a new `StrategySpec` class identity. The 9 in-repo
  strategies' `STRATEGY_SPEC` constants kept the old class identity (their
  modules were not reloaded).
- Re-running discovery, every `isinstance(spec_obj, StrategySpec)` check
  rejected the in-repo specs with the diagnostic warning
  *"expected StrategySpec, got StrategySpec"*.
- Result: post-fixture, the registry was empty. 73 tests across 12 unrelated
  test files cascaded to failure (CLI tests asserting registry contents,
  paper-trade runner tests building configs from the registry, strategy
  config parity tests, etc.).

**Diagnostic clue we missed for ~10 minutes:**

The warning message *"expected StrategySpec, got StrategySpec"* — same name,
different class — is the loud tell. If you see "expected X, got X" anywhere
in your logs, suspect class-identity drift before suspecting anything else.

**The fix:**

Rewrote the smoke fixture to invoke its assertions in a fresh subprocess:

```python
@pytest.fixture(scope="module")
def installed_external_strategy() -> Iterator[None]:
    uv = _uv_or_skip()
    subprocess.run(
        [uv, "pip", "install", "--editable", str(FIXTURE_DIR), "--quiet"],
        check=True,
    )
    try:
        yield
    finally:
        subprocess.run(
            [uv, "pip", "uninstall", FIXTURE_DIST_NAME, "--quiet"],
            check=True,
        )

def test_external_strategy_is_discovered(installed_external_strategy: None) -> None:
    result = subprocess.run(
        [sys.executable, "-c",
         "from nautilus_trading.cli._strategy_specs import STRATEGY_SPECS; "
         "assert 'external_strat' in STRATEGY_SPECS"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
```

The reload chain (`_flush_strategy_caches`) was deleted entirely. The
`sys.path` shim and `_drop_external_strat_from_sys_modules` helper went with
it — they were also workarounds for the in-process reload approach.

**Outcome:** 73 → 0 cascading failures, lint clean, single-commit fix.

## Notes

- The diagnostic signature *"expected X, got X"* (same name, different class)
  is the most reliable tell. Any time you see it, suspect this bug class
  before anything else.
- Frozen dataclasses are particularly affected because their `__eq__` is
  field-based but `isinstance` is identity-based — old and new instances
  compare as equal but fail isinstance checks.
- The same bug can hit `issubclass()` checks, exception-class catching,
  Pydantic / msgspec validators, and anything else that compares class
  identity.
- This is documented (briefly) in the [`importlib.reload`
  docs](https://docs.python.org/3/library/importlib.html#importlib.reload):
  *"As with all other objects in Python the old objects are only reclaimed
  after their reference counts drop to zero."* But the practical
  consequences for `isinstance` are not spelled out.
- If you must reload (e.g. for hot-reload in a development server), accept
  that you cannot use `isinstance` against post-reload classes for any
  pre-reload instance. Either re-create those instances after reload, or
  use duck typing / structural checks.
- `importlib.reload` is fine for modules that only expose **functions**
  (no class definitions whose instances live elsewhere). Functions don't
  have the same identity-leak problem because nothing typically does
  `isinstance(obj, some_func)`.

## References

- [Python docs: `importlib.reload`](https://docs.python.org/3/library/importlib.html#importlib.reload)
- [Python docs: subprocess](https://docs.python.org/3/library/subprocess.html)
- [pytest-forked plugin](https://pypi.org/project/pytest-forked/)
- [pytest-xdist `--boxed` flag](https://pytest-xdist.readthedocs.io/en/stable/boxed.html)
- Originating session: nautilus-trading Phase C code review, 2026-05-08, Round 2.
