#!/usr/bin/env bash
# Generate pane sessions table from pane data
# Usage: generate-pane-table.sh < pane_data.txt
# Input format: one line per pane: "pane_id|cwd"
# Example: w1t1p1|/home/user/Projects

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Collect pane data and stats
windows=""
tabs=""
pane_count=0
rows=""

while IFS='|' read -r pane_id cwd; do
  [[ -z "$pane_id" ]] && continue

  # Parse window/tab/pane from ID (e.g., w1t2p1)
  if [[ "$pane_id" =~ w([0-9]+)t([0-9]+)p([0-9]+) ]]; then
    win="${BASH_REMATCH[1]}"
    tab="${BASH_REMATCH[2]}"
    pane="${BASH_REMATCH[3]}"

    # Track unique windows and tabs
    if [[ ! "$windows" =~ " $win " ]]; then
      windows="$windows $win "
    fi
    tab_key="${win}_${tab}"
    if [[ ! "$tabs" =~ " $tab_key " ]]; then
      tabs="$tabs $tab_key "
    fi
    ((pane_count++))

    # Get session info
    session_json=$("$SCRIPT_DIR/get-session-info.sh" "$cwd" 2>/dev/null)
    session_id=$(echo "$session_json" | grep -o '"session_id": *"[^"]*"' | cut -d'"' -f4)
    current_task=$(echo "$session_json" | grep -o '"current_task": *"[^"]*"' | cut -d'"' -f4)

    # Determine status
    if [[ -z "$session_id" || "$session_id" == "null" ]]; then
      status="⚪ No session"
      session_id="(none)"
      current_task="-"
    elif [[ -n "$current_task" ]]; then
      status="🟢 Active"
    else
      status="🟡 Idle"
      current_task="-"
    fi

    # Get project name from CWD
    project=$(basename "$cwd")

    rows="${rows}| $win | $tab | $pane | $session_id | $project | $current_task | $status |
"
  fi
done

# Count unique windows and tabs
win_count=$(echo "$windows" | wc -w | tr -d ' ')
tab_count=$(echo "$tabs" | wc -w | tr -d ' ')

# Output
echo "📍 **iTerm2 Pane → Claude Session Mapping**"
echo ""
echo "**Summary:** $win_count windows, $tab_count tabs, $pane_count panes"
echo ""
echo "| Win | Tab | Pane | Session | Project | Current Task | Status |"
echo "|-----|-----|------|---------|---------|--------------|--------|"
printf "%s" "$rows"
echo ""
echo "💡 **Resume with:** \`claude -r <session-id>\`"
