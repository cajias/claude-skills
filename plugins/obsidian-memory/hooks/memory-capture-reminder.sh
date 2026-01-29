#!/bin/bash
# Stop hook: Remind Claude to capture learnings to Obsidian memory
# This runs after Claude completes a task

cat << 'EOF'
## Memory Capture Reminder

Before ending this task, consider capturing to Obsidian:

**Quick Checks:**
- [ ] Any decisions made? → `decisions/` as ADR
- [ ] User corrections or preferences? → `agent-workspaces/shared/persistent.md`
- [ ] Lessons learned? → `knowledge-base/lessons-learned/`
- [ ] Patterns discovered? → `knowledge-base/` with `#pattern` tag
- [ ] Facts about people? → `people/[name].md`
- [ ] Unsure where it belongs? → `agent-workspaces/shared/inbox.md`

**Use MCP tools:** `write_note`, `patch_note` to capture before session ends.
EOF
