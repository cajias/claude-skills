# ci-build

Gotchas collected from real CI pipelines and build environments — the kind
that fail loudly but point at the wrong cause. Each skill activates through
Claude Code's semantic matching when you hit its trigger condition, so the
fix arrives before the debugging session starts.

## Skills

| Skill                              | Purpose                                                                                                            |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `copilot-cli-github-actions`       | Run GitHub Copilot CLI headlessly in Actions: auth, tool pre-approval, model selection, marketplace install        |
| `cron-block-generation-gotchas`    | Generate crontab entries safely: unquoted-space splitting, cron's stripped `$PATH`, `shlex.quote` + `shutil.which` |
| `gfootball-docker-apple-silicon`   | Dockerfile recipe and runtime pins to build gfootball on Apple Silicon where native pip install fails              |
| `gha-setup-uv-cache-glob-mismatch` | `setup-uv` hard-fails on a gitignored `uv.lock`; fix is `cache-dependency-glob: pyproject.toml`                    |
| `monorepo-cookiecutter-ts-gotchas` | Eleven traps cutting a TypeScript instance of `cajias/monorepo-cookiecutter` and getting its test tiers green      |

## Install

```bash
cp -r plugins/ci-build ~/.claude/plugins/
```
