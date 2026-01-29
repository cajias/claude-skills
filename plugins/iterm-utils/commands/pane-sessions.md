---
description: "Map iTerm2 panes to their Claude Code sessions with current task and status"
argument-hint: "[--verbose]"
---

# Pane Sessions Mapper

Map all active iTerm2 panes to their corresponding Claude Code sessions, showing current task and status.

## Instructions

### Step 1: Get All Panes
Use the `mcp__iterm2__iterm2_list_panes` tool to get all panes with their working directories.

### Step 2: Generate Table
Parse the pane list and pipe to the table generator script. Format each pane as `pane_id|cwd`:

```bash
echo "w1t1p1|/Users/cajias/Projects
w2t1p1|/Users/cajias/Projects/foo
w2t2p1|/Users/cajias/Projects/bar" | ${CLAUDE_PLUGIN_ROOT}/scripts/generate-pane-table.sh
```

### Step 3: Output
Display the script output directly - it produces the complete formatted table.

## Status Icons
- 🟢 Active - has an in-progress task
- 🟡 Idle - session exists but no current task
- ⚪ No session - no Claude session found
