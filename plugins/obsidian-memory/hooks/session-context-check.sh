#!/bin/bash
# Session Context Check - SessionStart Hook
# Lightweight reminder to check persistent memory (prints once at session start)
# ponytail: prints unconditionally. The old guard keyed off $$, a fresh PID per
# invocation, so it never suppressed anything and leaked a /tmp file per run.
# Gate on a real session id if the repetition ever bites.

cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 OBSIDIAN MEMORY AVAILABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For this session, remember:
• Check agent-workspaces/shared/persistent.md for standing context
• Use Obsidian MCP tools for ALL working memory (not local disk)
• Capture decisions, lessons, and preferences as you work

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
