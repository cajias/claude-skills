---
description: "Map iTerm2 panes to their Claude Code sessions with current task and status"
argument-hint: "[--verbose]"
---

# Pane Sessions Mapper

Map all active iTerm2 panes to their corresponding Claude Code sessions, showing current task and status.

## Instructions

### Step 1: Get All Panes

Use the `mcp__iterm2__iterm2_list_panes` tool to get all panes with their working directories.
Each pane ID looks like `w<window>t<tab>p<pane>` (e.g. `w1t2p1`).

### Step 2: Look Up Each Session

For each pane, run the session-info script with that pane's working directory:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/get-session-info.sh "<cwd>"
```

It prints JSON with `session_id`, `slug`, `last_ts`, and `current_task`.
A result of `{"session_id": null}` means no Claude session exists for that directory.

### Step 3: Render the Table

Print a summary line with the window / tab / pane counts, then this table:

```markdown
| Win | Tab | Pane | Session | Project | Current Task | Status |
| --- | --- | ---- | ------- | ------- | ------------ | ------ |
```

- **Win / Tab / Pane** — the numbers parsed out of the pane ID
- **Session** — `session_id`, or `(none)` when null
- **Project** — the basename of the pane's working directory
- **Current Task** — `current_task`, or `-` when empty
- **Status** — see the icons below

Close with the resume hint: Resume with `claude -r <session-id>`.

## Status Icons

- 🟢 Active - has an in-progress task
- 🟡 Idle - session exists but no current task
- ⚪ No session - no Claude session found
