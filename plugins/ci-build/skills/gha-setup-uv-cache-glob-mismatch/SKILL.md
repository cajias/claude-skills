---
name: gha-setup-uv-cache-glob-mismatch
description: |
  Fix for GitHub Actions workflows using `astral-sh/setup-uv@v4` (or v5)
  failing immediately with `Error: No file matched to [**/uv.lock]` and
  cascading to skip every downstream job. Use when:
  (1) a GHA workflow shows the first uv-using job as failed and most
  others as skipped/cancelled after a push, despite the underlying
  steps being correct;
  (2) the failing job's log contains literally
  `Error: No file matched to [**/uv.lock]` right after
  `Run astral-sh/setup-uv@v4`;
  (3) the repo's `.gitignore` includes `uv.lock` (common for libraries
  that want consumers to resolve their own deps);
  (4) running `uv sync` works locally but every uv-using GHA step
  blows up before reaching `uv sync`.
  Root cause: setup-uv's cache layer defaults
  `cache-dependency-glob: **/uv.lock`, requires the glob to MATCH at
  least one tracked file, and treats a no-match as a hard failure.
  Fix is one line per setup-uv invocation:
  `cache-dependency-glob: pyproject.toml`.
author: Claude Code
version: 1.0.0
date: 2026-05-09
---

# astral-sh/setup-uv cache-dependency-glob mismatch in GHA

## Problem

Your GitHub Actions workflow uses `astral-sh/setup-uv@v4` to install
uv and cache its venv between runs. On the first push, the workflow's
first job fails immediately with:

```text
Run astral-sh/setup-uv@v4
Error: No file matched to [**/uv.lock]
```

Every job that has `needs: lint` (or whatever the first job is) then
shows `status: skipped` / `conclusion: cancelled`. From the GHA UI
this looks like "4 of 5 jobs cancelled" — implying a queueing /
permissions / concurrency issue. The actual cause is a **single line
of YAML** that depends on a file the repo doesn't track.

## Trigger conditions

All of these:

- Workflow uses `astral-sh/setup-uv@v4` (or `@v5`).
- Repo is uv-managed (has `pyproject.toml`, uses `uv sync` /
  `uv run`).
- Repo's `.gitignore` includes `uv.lock` (libraries commonly do this;
  apps usually track the lock).
- `git ls-files uv.lock` returns nothing (confirms not tracked).
- Workflow's setup-uv block does NOT specify
  `cache-dependency-glob:` (so it falls back to the default
  `**/uv.lock`).

If any one of these is false, this skill probably doesn't apply.

## Root cause

`astral-sh/setup-uv`'s caching layer needs a glob pattern that
matches at least one tracked file in the repo — that file's SHA
becomes part of the cache key, so the cache invalidates when deps
change.

The default value is `**/uv.lock`. For repos that track the lock
file, that's perfect: the cache key is the lock's SHA, the cache
invalidates on every `uv sync` that updates the lock.

For repos that gitignore the lock, `**/uv.lock` matches zero tracked
files. Setup-uv could fall back to "no caching" but it doesn't —
it errors out with `No file matched to [**/uv.lock]` and exits
non-zero. Every step using `needs:` of this job gets cascaded into
`skipped`, masking the real problem.

## Solution

Pin `cache-dependency-glob` to a file that IS tracked AND changes
when deps change. The canonical answer is `pyproject.toml`:

```yaml
- uses: astral-sh/setup-uv@v4
  with:
    cache-dependency-glob: pyproject.toml
```

Apply this to **every** setup-uv invocation in the workflow — not
just the first one. Each job runs setup-uv from scratch, so missing
the override on any single job re-introduces the bug.

`pyproject.toml` is the right choice because:

- It's always tracked (PEP 621 manifest).
- It changes when deps change — the `[project] dependencies = [...]`
  array, `[project.optional-dependencies]`, and any
  `[tool.uv.sources]` overrides all live there.
- Its SHA gives cache invalidation comparable to (slightly coarser
  than) the lock file's SHA.

Multi-package monorepo? Use a glob that catches every package's
manifest:

```yaml
cache-dependency-glob: |
  pyproject.toml
  packages/*/pyproject.toml
```

## Verification

1. Push the workflow change.
2. Open the latest GHA run. The setup-uv step should now show:

   ```text
   Run astral-sh/setup-uv@v4
   ...
   Cache hit: false  (first run)
   Successfully installed uv X.Y.Z
   ```

   On subsequent runs (same `pyproject.toml`):

   ```text
   Cache hit: true
   ```

3. Downstream jobs no longer show `cancelled` / `skipped`; they run
   their actual steps.
4. Check that `uv sync --extra dev` (or whatever your workflow runs)
   succeeds — the cache might have been the only blocker but
   verify nothing else is wrong.

## Example — full setup-uv block (corrected)

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - uses: astral-sh/setup-uv@v4
        with:
          cache-dependency-glob: pyproject.toml
      - run: uv sync --extra dev
      - run: uv run ruff check .
      - run: uv run mypy nautilus_competition/
```

## Alternatives (worse)

| Approach | Why it's worse |
|---|---|
| Track `uv.lock` in git | Defeats the gitignore intent for libraries — consumers should resolve their own deps. |
| `enable-cache: false` | Wastes 30–60s per CI run on uv install + dep resolution. Across N parallel jobs that's real money. |
| `if: hashFiles('uv.lock') != ''` guard | Band-aid. The action still defaults to the broken glob; you've just hidden the failure mode behind a conditional. |
| `cache-dependency-glob: '**/*.toml'` | Too broad; cache invalidates on any toml edit (e.g. ruff config) even when deps haven't changed. |

The `pyproject.toml` glob is the canonical fix.

## Notes

- Same pattern applies to `astral-sh/setup-uv@v5` — the default
  `cache-dependency-glob: **/uv.lock` carried forward.
- The error message ("No file matched to") is misleading because the
  natural reaction is "let me create the file" — but for libraries,
  you specifically WANT it not to exist in the repo. Don't track the
  lock just to silence the error.
- If your repo previously WORKED with default settings and recently
  broke, check whether someone added `uv.lock` to `.gitignore` (or
  removed it from being tracked) recently. The setup-uv action behavior
  didn't change; the repo's tracked-file set did.
- Cross-reference: `~/.claude/skills/uv-worktree-venv-fallthrough/SKILL.md`
  documents a related uv gotcha at the LOCAL level — fresh worktrees'
  empty `.venv` cause `uv run` to fall through to system Python. CI
  and worktrees are different contexts but both bite uv-managed
  projects.

## References

- astral-sh/setup-uv repo (default `cache-dependency-glob`):
  <https://github.com/astral-sh/setup-uv>
- uv lock file behavior:
  <https://docs.astral.sh/uv/concepts/projects/sync/#the-lockfile>
- uv "When to commit the lockfile" (libraries vs applications):
  <https://docs.astral.sh/uv/concepts/projects/sync/#when-to-commit-the-lockfile>
- Concrete origin: debugging PR #4 in
  `cajias/nautilus-competition` (2026-05-09). The freshly-merged CI
  workflow showed 4/5 jobs as skipped + 1 failed. Reading the failed
  job's log surfaced
  `Error: No file matched to [**/uv.lock]`. Repo's `.gitignore`
  contained `uv.lock` (it's a library, not an app). Fixing all 5
  `astral-sh/setup-uv@v4` invocations to
  `cache-dependency-glob: pyproject.toml` flipped 4/5 jobs to
  running-and-green; only one Python-3.12-specific click rendering
  test remained failing (unrelated to this skill).
