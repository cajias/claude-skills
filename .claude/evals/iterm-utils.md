# Eval: iterm-utils

Plugin path: plugins/iterm-utils

## Capability Evals

[CAPABILITY EVAL: iterm-utils-structure]
Task: Verify plugin has all required structural files and fields
Success Criteria:

- [ ] .claude-plugin/plugin.json exists and is valid JSON
- [ ] plugin.json has name, description, and version fields
- [ ] At least one command in commands/ with a .md file
- [ ] Each command .md has YAML frontmatter with a description field
- [ ] No APM references (apm pack, apm marketplace, Agent Package Manager)
      Expected Output: All structural checks pass
      Grader: code-based (bash — see scripts/test-skills.sh)

[CAPABILITY EVAL: iterm-utils-skill-quality]
Task: Verify command/skill descriptions are specific and triggerable
Success Criteria:

- [ ] Description is specific (not generic boilerplate)
- [ ] Command/skill content is substantial (> 200 chars per .md file)
- [ ] Triggering context is clear in the description
- [ ] No placeholder text (TODO, TBD) in production commands/skills
      Expected Output: All skill quality checks pass
      Grader: code-based (char count, grep)

## Regression Evals

[REGRESSION EVAL: iterm-utils-claude-native]
Baseline: APM era (pre-migration)
Tests:

- plugin.json uses Claude-native format (not APM format): MUST PASS
- No APM CLI dependency for installation: MUST PASS
- Plugin installable by copying to ~/.claude/plugins/: MUST PASS
  Result: 3/3 must pass

## Plugin-Specific Checks

This plugin provides iTerm2 pane and session management utilities for Claude Code.

### Commands

**pane-sessions** (`commands/pane-sessions.md`)

- Description: "Map iTerm2 panes to their Claude Code sessions with current task and status"
- Argument hint: `[--verbose]`
- What it does: Invokes `mcp__iterm2__iterm2_list_panes`, pipes output through
  `scripts/generate-pane-table.sh`, and displays a formatted markdown table
  showing Window/Tab/Pane identifiers, Claude session IDs, current project
  names, in-progress tasks, and status icons (Active/Idle/No session).
- Specific assertions:
  - [ ] Command references `mcp__iterm2__iterm2_list_panes` tool
  - [ ] Command references `${CLAUDE_PLUGIN_ROOT}/scripts/generate-pane-table.sh`
  - [ ] Three status icons are documented: green (Active), yellow (Idle), white (No session)

### Scripts

**generate-pane-table.sh** (`scripts/generate-pane-table.sh`)

- Reads pane data from stdin in `pane_id|cwd` format
- Parses `w<N>t<N>p<N>` pane ID notation using regex
- Calls `get-session-info.sh` per pane to read `~/.claude/projects/` session files
- Outputs a summary line (window/tab/pane counts) and a markdown table
- Specific assertions:
  - [ ] Script is executable (has shebang `#!/usr/bin/env bash`)
  - [ ] Parses pane IDs matching pattern `w([0-9]+)t([0-9]+)p([0-9]+)`
  - [ ] Outputs markdown table with columns: Win, Tab, Pane, Session, Project, Current Task, Status
  - [ ] Ends with resume hint: `claude -r <session-id>`

**get-session-info.sh** (`scripts/get-session-info.sh`)

- Takes a working directory path as argument
- Transforms path to `~/.claude/projects/` key by replacing `/` with `-`
- Reads the most recent `.jsonl` session file for that project
- Extracts session_id, slug, last timestamp, and current in-progress task
- Outputs a JSON object
- Specific assertions:
  - [ ] Script handles missing CWD argument with usage error and exit 1
  - [ ] Outputs valid JSON in both success and no-session cases
  - [ ] Falls back to pending task when no in-progress task is found

### Plugin-level assertions

- [ ] plugin.json keywords include "iterm2", "terminal", "sessions", "panes"
- [ ] Plugin depends on `mcp__iterm2__iterm2_list_panes` (iTerm2 MCP integration) — document this as a runtime prerequisite
- [ ] No `skills/` directory exists — plugin uses `commands/` instead; structure eval must not require a `skills/` dir

## Metrics Target

- pass@1: 100% for structure (deterministic)
- pass@3: > 90% for skill quality
