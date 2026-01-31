#!/bin/bash
# Initialize HLD execution state tracker
# Usage: ./init-state-tracker.sh "Project Name"

set -e

PROJECT_NAME="${1:-HLD Project}"
STATE_DIR=".agent"
STATE_FILE="$STATE_DIR/hld-execution-state.md"

# Create .agent directory if it doesn't exist
mkdir -p "$STATE_DIR"

# Check if state file already exists
if [ -f "$STATE_FILE" ]; then
    echo "Warning: State file already exists at $STATE_FILE"
    echo "Backing up to $STATE_FILE.backup"
    cp "$STATE_FILE" "$STATE_FILE.backup"
fi

# Create initial state tracker
cat > "$STATE_FILE" << EOF
# HLD Execution State: $PROJECT_NAME

## Execution Status
- **Started:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
- **Current Phase:** None
- **Overall Status:** In Progress

## Dependency Graph

| Phase | Name | Depends On | Status | Validation |
|-------|------|-----------|--------|------------|
| (To be populated from HLD parsing) |

## Completed Phases

(No phases completed yet)

## Phase Execution Log

| Phase | Started | Completed | Duration | Validation Result | Notes |
|-------|---------|-----------|----------|-------------------|-------|

## Cross-Phase Resources

| Resource | Created In | Used By | Type | Status |
|----------|-----------|---------|------|--------|

## Investigation Tracker

| Phase | Issue | Attempted Fix | Result | Next Action |
|-------|-------|---------------|--------|-------------|

## Git Tags

| Tag | Phase | Created | Commit |
|-----|-------|---------|--------|

## Rollback Points

| Phase | Rollback Command | Estimated Time |
|-------|------------------|----------------|

---

*Last updated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")*
EOF

echo "State tracker initialized at $STATE_FILE"
echo "Ready for HLD parsing to populate phases."
