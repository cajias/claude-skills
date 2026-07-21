# CLAUDE.md

Claude Code plugin/skill marketplace. Editing here triggers automation — read this first.

## Commands

- `make validate` — plugin-structure + marketplace-sync checks (also runs at husky pre-commit; NOT in CI).
- `make test-skills` — per-plugin structural eval via `scripts/test-skills.sh`; runs in neither CI nor
  pre-commit. One plugin: `bash scripts/test-skills.sh <name>`.
- `make install` — symlink every `plugins/*/` into `~/.claude/plugins/` (live symlinks; edits apply without reinstall).
- `make lint` (markdownlint + ls-lint) / `make fix` (lint:fix then prettier). Single file: `make lint-file FILE=<rel>`.
- Python tests are CI-only; run locally per plugin: `cd plugins/semantic-search && uv run pytest`, or
  `cd plugins/claudeception && uv sync --extra dev && uv run pytest`.

## Layout

Three sibling trees validated by DIFFERENT mechanisms — don't conflate them:

- `plugins/*/` (19) — installable plugins, each with `.claude-plugin/plugin.json`. All 19 are registered
  in `.claude-plugin/marketplace.json` via `./plugins/<name>` sources. plugin.json `version` is
  source-of-truth; marketplace.json must match it or `validate.sh` fails. Plugins on disk but absent from
  marketplace.json are treated as intentionally hidden (allowed).
- `skills/*/` (37) — standalone skills (each needs `SKILL.md` + `README.md`); enforced by CI's "required
  skill files" step and `validate.sh`.
- `agents/*.md` (5) — standalone agent defs; frontmatter needs `name`/`description`/`model` (model ∈ `sonnet|haiku|opus`).

## Auto-formatting on every edit

A PostToolUse hook in `.claude/settings.json` runs `make lint-file FILE=<rel>` on every
`Edit|Write|MultiEdit` under the project root. Your writes are rewritten (prettier +
`markdownlint --fix`) immediately, and lint failure exits 2. Do not hand-format.

`lint-file`'s Python branch matches `plugins/<name>/**.py` and runs `ruff format` + `ruff check --fix`
whenever that plugin ships a `pyproject.toml` — currently `semantic-search` and `claudeception` (#46).
A `.py` under a plugin with no `pyproject.toml` falls through untouched; lint-staged still formats the
two `uv` plugins at commit.

## Python

`uv` + `ruff` only (no pip, no black). lint-staged `cd`s into `plugins/semantic-search` and
`plugins/claudeception` separately and runs `uv run ruff format` / `ruff check --fix`.
`make deps-python` pulls torch (multi-GB) — skip unless needed.

## Lint/format ignores

- Prettier globs `{md,json,yml,yaml,mjs,js}`; `.mjs`/`.js` added 2026-07-20 (#44).
- `lint:md` runs `--dot` and markdownlint ignores `.gitignore`, so gitignored dot-dirs
  (`.claude/worktrees/`, `.remember/`, `**/.venv/`) need explicit `.markdownlintignore` entries —
  otherwise lint descends into sibling worktrees and fails on another branch's files.
- `plugins/rsi-loop/docs/experiments/` is frozen run evidence, deliberately lint/format-ignored. Never reformat.
- Verbatim-imported `plugins/*/skills/` (7 dirs, see ignore files) are skipped by both tools.

## CI

6 jobs: `ci.yml` (lint, semantic-search, claudeception, ai-writing, rsi-loop) + `commit-lint.yml`.
Conventional commits enforced (see `.commitlintrc.json`).
