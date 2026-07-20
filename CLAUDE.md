# CLAUDE.md

Claude Code plugin/skill marketplace. Editing here triggers automation — read this first.

## Auto-formatting on every edit

A PostToolUse hook in `.claude/settings.json` runs `make lint-file FILE=<rel>` on every
`Edit|Write|MultiEdit` under the project root. Your writes are rewritten (prettier +
`markdownlint --fix`) immediately, and lint failure exits 2. Do not hand-format.

Gap: `lint-file`'s Python branch matches only `*semantic-search/*.py`, so
`plugins/claudeception/**/*.py` edits are **not** auto-formatted — lint-staged catches them at commit.

## Python

`uv` + `ruff` only (no pip, no black). lint-staged `cd`s into `plugins/semantic-search` and
`plugins/claudeception` separately and runs `uv run ruff format` / `ruff check --fix`.
`make deps-python` pulls torch (multi-GB) — skip unless needed.

## Install

`make install` symlinks each `plugins/*/` into `~/.claude/plugins/<name>`. Live symlinks:
edits take effect without reinstalling.

## Lint/format ignores

- Prettier globs `{md,json,yml,yaml,mjs,js}`; `.mjs`/`.js` added 2026-07-20 (#44).
- `lint:md` runs `--dot` and markdownlint ignores `.gitignore`, so gitignored dot-dirs
  (`.claude/worktrees/`, `.remember/`, `**/.venv/`) need explicit `.markdownlintignore` entries —
  otherwise lint descends into sibling worktrees and fails on another branch's files.
- `plugins/rsi-loop/docs/experiments/` is frozen run evidence, deliberately lint/format-ignored. Never reformat.
- Verbatim-imported `plugins/*/skills/` (7 dirs, see ignore files) are skipped by both tools.

## CI

6 jobs: `ci.yml` (lint, semantic-search, claudeception, ai-writing, rsi-loop) + `commit-lint.yml`.
Conventional commits enforced. `scripts/test-skills.sh` runs in neither CI nor pre-commit
(`make test-skills` only); `scripts/validate.sh` is not in CI but runs at husky pre-commit.
