#!/bin/bash
# Session Context Check - UserPromptSubmit Hook
# Lightweight reminder to check persistent memory (only outputs on first few messages)

# Use a state file to track if we've shown the reminder in this session
STATE_FILE="/tmp/obsidian-memory-session-$$"

# Only show on first message of session (state file doesn't exist)
if [ ! -f "$STATE_FILE" ]; then
    touch "$STATE_FILE"
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
fi
