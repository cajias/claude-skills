---
name: python-slots-mock-patch-object
description: |
  Fix for `AttributeError: '<ClassName>' object attribute '<method>' is
  read-only` raised during `mock.patch.object()` teardown. Use when:
  (1) a Python test using `unittest.mock.patch.object(instance, "method")`
  passes the patched code but raises an AttributeError during context-exit
  (visible in the stack as `mock.py:1635` calling `delattr(self.target,
  self.attribute)`); (2) the target class declares `__slots__`; (3) the
  test was working before someone added `__slots__` to a base class or
  the target class itself; (4) a refactor introduced `__slots__` "for
  efficiency" and broke a previously-green test suite. Covers root cause
  (`__slots__` blocks `delattr` because it doesn't allocate `__dict__`,
  so the attribute can't be removed after the patch sets it), the
  diagnostic signature, the canonical fix (drop `__slots__` if the class
  is a mock target), and when `__slots__` IS the right call (when memory
  matters AND the class is never patched).
author: Claude Code
version: 1.0.0
date: 2026-05-09
---

# `__slots__` + `mock.patch.object` Incompatibility

## Problem

`mock.patch.object(target, attribute)` works in two phases:

1. **Setup**: `setattr(target, attribute, mock_object)` — replaces the
   attribute with a MagicMock for the duration of the patch context.
2. **Teardown**: `delattr(target, attribute)` (or `setattr` of original)
   — removes the patch when the context exits.

If the target's class declares `__slots__`, **the teardown's `delattr`
fails**:

```
AttributeError: '<ClassName>' object attribute '<method>' is read-only
```

Stack trace points at `mock.py:1635` in `_patch.__exit__`:

```python
delattr(self.target, self.attribute)
```

Root cause: `__slots__` doesn't allocate `__dict__` for instances. Each
slot is a fixed descriptor, not a dynamically removable attribute.
Setting via `setattr` works (replaces the slot's value), but deletion
fails because the slot itself is part of the class definition, not the
instance's free attribute storage.

The setup phase works without warning, so the regression often only
surfaces during cleanup — which is **after** the test's actual assertion
has run. The test "passes" mid-flight and fails on teardown, making the
error look like infrastructure noise rather than a real bug.

## Context / Trigger Conditions

Look for this exact pattern:

- Test file uses `unittest.mock.patch.object(instance, "method_name")`,
  either as a context manager, decorator, or `mock.patch.object(...).start()`.
- Production class has `__slots__ = ("...",)` declared.
- Error message: `'<ClassName>' object attribute '<method>' is
  read-only`.
- Stack trace shows the error in `mock.py:_patch.__exit__` →
  `delattr(self.target, ...)`.
- Test was green before a refactor that added `__slots__` (or moved the
  class into a hierarchy where a base class has `__slots__`).
- Multiple unrelated tests fail with the same error pattern simultaneously
  after a single change.

## Solution

### Default fix: drop `__slots__`

For the vast majority of cases, **the class shouldn't have `__slots__`
in the first place** if it's a mock target. Memory savings of
`__slots__` are real but small (~80 bytes per instance vs. `__dict__`
overhead) and only matter at scale (millions of instances).

```python
# Before
class _ConfigBuilder:
    __slots__ = ("_fn",)
    def __init__(self, fn): self._fn = fn
    def build(self, args): return self._fn(args)

# After
class _ConfigBuilder:
    # NOTE: deliberately no __slots__ — these instances are targets of
    # mock.patch.object(builder, "build") in tests/.../test_*.py, and
    # __slots__ blocks the delattr that mock teardown does. Memory
    # savings of __slots__ are negligible at the ~N instances we have.
    def __init__(self, fn): self._fn = fn
    def build(self, args): return self._fn(args)
```

The inline NOTE is important — without it, a future refactor will
re-add `__slots__` and re-break the tests.

### When `__slots__` IS the right call

Keep `__slots__` if all three apply:

1. The class is instantiated at scale (10K+ instances live concurrently).
2. Memory profiling shows `__dict__` overhead is meaningful.
3. **The class is never a mock target.**

If conditions 1+2 hold but 3 doesn't, refactor the test to mock
something other than the class itself — e.g. mock a function the class
calls, or mock the class's CONSTRUCTOR (not an instance method) so the
patch operates on the class object (which has `__dict__`) rather than
the instance (which has only slots).

### Alternative fix: mock at a different surface

If `__slots__` truly must stay:

```python
# Don't do this — __slots__ will fight you on teardown:
with mock.patch.object(builder_instance, "build") as mock_build:
    ...

# Do this instead — patch the underlying function:
with mock.patch.object(builder_instance, "_fn") as mock_fn:
    ...

# Or patch at the class level (class object has __dict__):
with mock.patch.object(_ConfigBuilder, "build") as mock_build:
    ...
```

Trade-off: class-level patching affects ALL instances, which may break
other tests in the same file. Patching `_fn` (an internal) couples the
test to the class's private structure.

## Verification

After applying the fix:

1. Run the previously-failing test in isolation — should pass cleanly,
   no AttributeError on teardown.
2. Run the full test suite — confirm pass count returns to the pre-`__slots__`
   baseline.
3. Confirm `mock.patch.object(instance, "method")` is in the test code
   that was failing (not `mock.patch.object(SomeClass, "method")` which
   patches at the class level — that works fine with `__slots__`).

## Example — what happened in nautilus-trading 2026-05-09

**The setup:**

PR #51 (`refactor(specs): collapse Protocol + builder classes`) introduced
`_ConfigBuilder` as a callable wrapper to share builder logic across
multiple `STRATEGY_SPEC.builder=` references. The agent author added
`__slots__ = ("_fn",)` as a "Pythonic" choice for an instance with one
attribute.

**The bug:**

Two pre-existing tests:

```python
# tests/backtest/test_strategy_runner.py
def test_actor_builder_called_before_strategy_builder():
    spec = STRATEGY_SPECS["kronos"]
    with mock.patch.object(spec.builder, "build") as mock_build:
        run_strategy(spec)
        mock_build.assert_called_once_with(...)
    # AttributeError raised HERE on context exit, after assertion passed
```

These tests had been green for months. PR #51's `__slots__` addition
silently broke them. The agent's pre-merge verify said "477 passed,
0 failed" — but in fact a subset of tests had been excluded from that
run, and the regression only surfaced when the next merged-into-main
branch picked it up.

**The fix:**

Single line removed from `_ConfigBuilder`:

```python
# class _ConfigBuilder:
#     __slots__ = ("_fn",)   # ← removed; added comment explaining why
```

477/0/1 restored. Total time: ~5 minutes once the diagnosis was clear.

**Diagnostic clue we missed for ~30 minutes** (only because the simplify
loop's verify step caught it): the AttributeError signature
*"'X' object attribute 'Y' is read-only"* with `Y` being a method name.
For a slot, that signature reads naturally, but it's the SAME signature
as for a `@property` with no setter — so the first guess is "did
someone make `build` a read-only property?" That's the wrong tree. The
right one: check if the class has `__slots__`.

## Notes

- This bug class is **pre-merge invisible**: setup-phase setattr works
  silently, the assertion runs, the test "passes" — only the
  context-exit cleanup fails. If a test runner only reports pass/fail
  without per-test teardown errors, the regression is even harder to
  catch.
- **Frozen dataclasses with `__slots__`** (Python 3.10+ supports
  `@dataclass(frozen=True, slots=True)`) hit the same trap. The trip
  wire is the same: `delattr` blocked by slots.
- **Pydantic v2 BaseModel uses `__slots__` internally**. If you mock
  methods on Pydantic models, you'll hit this. Workaround: mock the
  Pydantic class's METHOD at the class level, not the instance.
- **C extension classes (Cython, Rust, etc.)** also commonly enforce
  `__slots__`-like behavior. If you can't `mock.patch.object` a method
  on a Cython-backed class, this is why.
- **`__slots__` saves memory but blocks reflection.** Two costs of the
  same trade-off. Mock-based tests are reflection.

## References

- [Python docs: `__slots__`](https://docs.python.org/3/reference/datamodel.html#slots)
  — see "Notes on using **slots**" section: "Without a **dict**
  variable, instances cannot have new variables not listed in the
  **slots** definition."
- [Python docs: `unittest.mock.patch.object`](https://docs.python.org/3/library/unittest.mock.html#patch-object)
- Originating session: nautilus-trading PR #51 fix-up, 2026-05-09. Surfaced
  by the simplify-loop's verify gate (3-round convergence run).
