# python-tooling

Reference skills for Python toolchain failures whose symptom points nowhere near
the cause: a passing type looking wrong to `isinstance`, a `pip install` landing
an unrelated package, a teardown error blamed on the mock library, a formatter
inflating a PR by a thousand lines, and a test runner silently using the wrong
interpreter. Each skill names the real mechanism and the fix.

## Skills

| Skill                             | Purpose                                                                                                                            |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `importlib-reload-class-identity` | `importlib.reload()` mints new class objects, so `isinstance` rejects correct-looking instances; isolate in a subprocess.          |
| `kronos-pypi-collision`           | `pip install kronos` resolves to an unrelated Django package; install the intended model from its GitHub repo.                     |
| `python-slots-mock-patch-object`  | `mock.patch.object()` teardown raises "object attribute is read-only" when the target class declares `__slots__`.                  |
| `ruff-jupyter-diff-inflation`     | `ruff check --fix` rewrites `.ipynb` source fields and adds 700-1000+ diff lines per notebook; scope it in `pyproject.toml`.       |
| `uv-worktree-venv-fallthrough`    | `uv run` falls through to PATH binaries when a worktree `.venv` is empty, faking `ModuleNotFoundError`; run `uv sync --extra dev`. |
