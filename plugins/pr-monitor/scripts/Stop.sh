#!/bin/bash
# Stop Hook: Auto-resume PR monitoring when new commits are detected
# This hook runs when Claude Code would normally stop/idle

set -e

# Read JSON input from stdin
input=$(cat)

# Parse input
stop_hook_active=$(echo "$input" | jq -r '.stop_hook_active // false')

# Prevent infinite loops - if we're already in a stop hook, don't recurse
if [ "$stop_hook_active" = "true" ]; then
  exit 0
fi

# Check if we're monitoring any PRs
# State file format: $STATE_DIR/claude_monitor_pr_<repo>_<pr_number>
STATE_DIR="${HOME}/.claude/pr-monitor"
mkdir -p -m 700 "$STATE_DIR"

# Check each monitored PR
while IFS= read -r state_file; do
  # Extract repo and PR number from filename
  # Format: $STATE_DIR/claude_monitor_pr_<repo>_<pr_number>
  basename=$(basename "$state_file")

  # Read the state file which contains: repo_path, pr_number, last_commit_sha
  if [ ! -f "$state_file" ]; then
    continue
  fi

  repo_path=$(sed -n '1p' "$state_file")
  pr_number=$(sed -n '2p' "$state_file")
  last_sha=$(sed -n '3p' "$state_file" || echo "")

  # Change to repo directory to use gh CLI
  if [ -d "$repo_path" ]; then
    cd "$repo_path"
  else
    # Repo not found, clean up state file
    rm -f "$state_file"
    continue
  fi

  # Get current PR status
  pr_data=$(gh pr view "$pr_number" --json commits,headRefOid,state 2>/dev/null || echo "")

  if [ -z "$pr_data" ]; then
    # PR not accessible, skip
    continue
  fi

  current_sha=$(echo "$pr_data" | jq -r '.headRefOid')
  pr_state=$(echo "$pr_data" | jq -r '.state')
  commit_count=$(echo "$pr_data" | jq '.commits | length')

  # Check if there are new commits
  if [ -n "$current_sha" ] && [ "$current_sha" != "$last_sha" ]; then
    # Update state file with new SHA
    echo "$repo_path" > "$state_file"
    echo "$pr_number" >> "$state_file"
    echo "$current_sha" >> "$state_file"

    # Block stopping and provide reason for continuation
    jq -n --arg reason "New commits detected in PR #${pr_number} (${repo_path##*/}). Current commit: ${current_sha:0:8}. There are now ${commit_count} total commits. Please review the new changes and provide feedback." '{decision: "block", reason: $reason}'
    exit 0
  fi

  # Check if PR was merged or closed
  if [ "$pr_state" != "OPEN" ]; then
    # PR is no longer open, notify and clean up
    rm -f "$state_file"

    jq -n --arg reason "PR #${pr_number} in ${repo_path##*/} has been ${pr_state}. Monitoring stopped. Please review the final state." '{decision: "block", reason: $reason}'
    exit 0
  fi
done < <(find "$STATE_DIR" -name 'claude_monitor_pr_*' -type f 2>/dev/null)

# No new commits detected, allow stopping normally
exit 0
