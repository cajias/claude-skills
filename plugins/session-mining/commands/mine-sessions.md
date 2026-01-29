---
name: mine-sessions
description: Mine past Claude Code sessions for extractable knowledge. Runs claudeception on historical sessions to identify patterns, lessons, and improvement opportunities.
arguments:
  - name: options
    description: "Options: --since DAYS, --limit N, --dry-run, --filter PATTERN, --project PATH"
    required: false
---

# Mine Sessions for Knowledge

This command processes past Claude Code sessions to extract valuable knowledge.

## What It Does

1. Scans session history across all projects
2. Filters sessions by date, size, or content
3. Invokes `/claudeception` on each session
4. Extracts skills, patterns, and lessons learned
5. Saves results to `~/.claude/claudeception-results/`

## Usage

Run the script with options:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/claudeception-all-sessions.sh [options]
```

## Common Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Preview what would be processed |
| `--since N` | Recent N days (positive) or oldest N days (negative) |
| `--limit N` | Process at most N sessions |
| `--filter PATTERN` | Only sessions matching pattern |
| `--project PATH` | Only sessions from specific project |
| `--max-messages N` | Skip sessions with more than N messages |
| `--cleanup` | Remove result files |

## Examples

**Preview oldest sessions:**
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/claudeception-all-sessions.sh --since -1 --dry-run
```

**Process last 7 days, limit to 10:**
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/claudeception-all-sessions.sh --since 7 --limit 10
```

**Filter by topic:**
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/claudeception-all-sessions.sh --filter "obsidian" --limit 5
```

## Output

Results are saved to `~/.claude/claudeception-results/`:
- `{session-id}.md` - Extracted knowledge
- `{session-id}.log` - Processing log

## Execution

When the user runs `/mine-sessions`, execute the script with any provided options:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/claudeception-all-sessions.sh $ARGUMENTS
```

If no arguments provided, show the help:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/claudeception-all-sessions.sh --help
```
