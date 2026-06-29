# Skill Eval Harness

## Purpose

Tests every plugin in `plugins/` for four properties:

1. **Plugin structure** — `.claude-plugin/plugin.json` exists, is valid JSON, and
   has required fields (`name`, `description`, `version`).
2. **At least one component** — a plugin must provide at least one of: skills,
   commands, agents, hooks, or an MCP server (a plugin need not ship a skill).
3. **Skill frontmatter** — when a plugin ships `SKILL.md` files, each must start
   with `---` (YAML frontmatter).
4. **No APM references** — no mentions of `apm pack`, `apm marketplace`, or
   `Agent Package Manager` anywhere in the plugin.

## How to run

Run all plugins:

```bash
make test-skills
# or directly:
bash scripts/test-skills.sh
```

Run a single plugin by name:

```bash
bash scripts/test-skills.sh claudeception
```

## Output

On PASS, each plugin prints `PASS`, its name, and the component types it
provides. On FAIL it prints the reasons. Example:

```text
PASS  claudeception      [skills, hooks]
PASS  dev                [commands, agents]
FAIL  some-plugin
      - no components found (needs at least one skill, command, agent, hook, or MCP server)
```

Exit code `0` means all plugins are clean. Any failure exits `1`.

## Adding evals

Create `.claude/evals/<plugin-name>.md` following the existing files in this directory.

Each eval file documents the expected checks for one plugin. The bash grader in
`scripts/test-skills.sh` reads the plugin directory — the `.md` files here are the
human-readable spec that the script implements.

Sections to include:

- **Capability Evals** (`[CAPABILITY EVAL: <id>]`) — what the plugin must have (structure, fields, file layout).
- **Regression Evals** (`[REGRESSION EVAL: <id>]`) — Claude-native compliance
  checks (no APM dependency, installable by copying to `~/.claude/plugins/`).
- **Plugin-Specific Checks** — hook scripts, skill inventory, supporting files unique to this plugin.

## Eval types

| Type            | Tag                       | What it checks                                                                            |
| --------------- | ------------------------- | ----------------------------------------------------------------------------------------- |
| CAPABILITY EVAL | `[CAPABILITY EVAL: <id>]` | Structural correctness — files exist, JSON is valid, frontmatter fields present           |
| REGRESSION EVAL | `[REGRESSION EVAL: <id>]` | Claude-native compliance — no APM format, no hardcoded paths, installable without apm CLI |

## Grader

The grader is a plain bash script (`scripts/test-skills.sh`). It is fully
deterministic — no LLM involvement. Checks use `jq`, `grep`, `wc`, and
file-existence tests.

## Metrics targets

| Metric                        | Target                                     |
| ----------------------------- | ------------------------------------------ |
| pass@1 — structure checks     | 100% (deterministic; any failure is a bug) |
| pass@3 — skill quality checks | > 90%                                      |
