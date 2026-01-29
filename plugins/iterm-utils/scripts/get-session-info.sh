#!/bin/bash
# Get Claude Code session info for a given working directory
# Usage: get-session-info.sh <cwd>

CWD="$1"

if [ -z "$CWD" ]; then
  echo "Usage: $0 <cwd>"
  exit 1
fi

# Transform CWD to project dir path (replace / with -)
PROJECT_DIR=$(echo "$CWD" | sed 's|/|-|g')
SESSION_FILE=$(ls -t ~/.claude/projects/${PROJECT_DIR}/*.jsonl 2>/dev/null | head -1)

if [ -n "$SESSION_FILE" ]; then
  # Extract session ID from filename
  SESSION_ID=$(basename "$SESSION_FILE" .jsonl)

  # Get the slug (session name) from file
  SLUG=$(grep -o '"slug":"[^"]*"' "$SESSION_FILE" | tail -1 | cut -d'"' -f4)

  # Get last timestamp
  LAST_TS=$(tail -1 "$SESSION_FILE" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)

  # Get current in_progress todo (activeForm field)
  CURRENT_TASK=$(grep 'TodoWrite' "$SESSION_FILE" | tail -1 | grep -o '"status":"in_progress"[^}]*"activeForm":"[^"]*"' | grep -o '"activeForm":"[^"]*"' | cut -d'"' -f4 | head -1)

  # If no in_progress todo, check for pending
  if [ -z "$CURRENT_TASK" ]; then
    CURRENT_TASK=$(grep 'TodoWrite' "$SESSION_FILE" | tail -1 | grep -o '"status":"pending"[^}]*"content":"[^"]*"' | head -1 | grep -o '"content":"[^"]*"' | cut -d'"' -f4 | head -c 50)
  fi

  # Output as JSON for easy parsing
  cat <<EOF
{
  "session_id": "$SESSION_ID",
  "slug": "$SLUG",
  "last_ts": "$LAST_TS",
  "current_task": "$CURRENT_TASK"
}
EOF
else
  echo '{"session_id": null}'
fi
