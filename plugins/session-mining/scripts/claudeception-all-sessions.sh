#!/usr/bin/env bash
#
# claudeception-all-sessions.sh
#
# Invokes the /claudeception skill on all Claude Code sessions to extract
# reusable knowledge and create skills from past work.
#
# Usage:
#   ./claudeception-all-sessions.sh [options]
#
# Options:
#   --dry-run         Show what would be done without executing
#   --filter PATTERN  Only process sessions matching pattern (in firstPrompt)
#   --exclude PATTERN Exclude sessions matching pattern (default: "I'm Ralph")
#   --limit N         Process at most N sessions
#   --parallel N      Run N sessions in parallel (default: 1)
#   --since DAYS      Only process sessions modified in the last N days
#                     Use negative values for oldest (e.g., --since -1 = oldest day)
#   --project PATH    Only process sessions from a specific project path
#   --output DIR      Directory to save extraction results (default: ~/.claude/claudeception-results)
#   --model MODEL     Model to use (default: sonnet)
#   --max-messages N  Skip sessions with more than N messages (default: 100)
#   --cleanup         Remove all result files from output directory
#   -v, --verbose     Verbose output
#   -h, --help        Show this help

set -euo pipefail

# Defaults
DRY_RUN=false
FILTER=""
EXCLUDE="I'm Ralph"
LIMIT=0
PARALLEL=1
SINCE_DAYS=0
PROJECT_FILTER=""
OUTPUT_DIR="$HOME/.claude/claudeception-results"
MODEL="sonnet"
VERBOSE=false
CLEANUP=false
MAX_MESSAGES=100

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() { echo -e "${BLUE}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
debug() { [[ "$VERBOSE" == "true" ]] && echo -e "[DEBUG] $*" || true; }

usage() {
    sed -n '2,/^$/p' "$0" | sed 's/^# //; s/^#//'
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --filter) FILTER="$2"; shift 2 ;;
        --exclude) EXCLUDE="$2"; shift 2 ;;
        --limit) LIMIT="$2"; shift 2 ;;
        --parallel) PARALLEL="$2"; shift 2 ;;
        --since) SINCE_DAYS="$2"; shift 2 ;;
        --project) PROJECT_FILTER="$2"; shift 2 ;;
        --output) OUTPUT_DIR="$2"; shift 2 ;;
        --model) MODEL="$2"; shift 2 ;;
        --max-messages) MAX_MESSAGES="$2"; shift 2 ;;
        -v|--verbose) VERBOSE=true; shift ;;
        --cleanup) CLEANUP=true; shift ;;
        -h|--help) usage ;;
        *) error "Unknown option: $1"; usage ;;
    esac
done

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Sessions directory
SESSIONS_DIR="$HOME/.claude/projects"

# Cleanup result files
cleanup_results() {
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        log "No results directory found"
        return 0
    fi

    local md_count log_count
    md_count=$(find "$OUTPUT_DIR" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
    log_count=$(find "$OUTPUT_DIR" -name "*.log" -type f 2>/dev/null | wc -l | tr -d ' ')

    log "Found $md_count result files and $log_count log files"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  [DRY RUN] Would delete all files in $OUTPUT_DIR"
        return 0
    fi

    rm -f "$OUTPUT_DIR"/*.md "$OUTPUT_DIR"/*.log 2>/dev/null || true
    success "Cleaned up result files"
}

if [[ ! -d "$SESSIONS_DIR" ]]; then
    error "Sessions directory not found: $SESSIONS_DIR"
    exit 1
fi

# Temp file for session list
SESSION_LIST=$(mktemp)
trap "rm -f $SESSION_LIST" EXIT

# Collect all sessions into temp file
collect_sessions() {
    log "Collecting sessions from $SESSIONS_DIR" >&2

    local tmp_all=$(mktemp)

    # First pass: collect all matching sessions (without date filter)
    find "$SESSIONS_DIR" -name "sessions-index.json" -type f | while read -r index_file; do
        local project_path
        project_path=$(jq -r '.originalPath // ""' "$index_file" 2>/dev/null || echo "")

        # Apply project filter if specified
        if [[ -n "$PROJECT_FILTER" && "$project_path" != *"$PROJECT_FILTER"* ]]; then
            continue
        fi

        # Build jq filter
        local jq_filter='.entries[]'

        # Exclude pattern
        if [[ -n "$EXCLUDE" ]]; then
            jq_filter="$jq_filter | select((.firstPrompt // \"\") | test(\"$(echo "$EXCLUDE" | sed 's/"/\\"/g')\") | not)"
        fi

        # Include pattern
        if [[ -n "$FILTER" ]]; then
            jq_filter="$jq_filter | select((.firstPrompt // \"\") | test(\"$(echo "$FILTER" | sed 's/"/\\"/g')\"; \"i\"))"
        fi

        # Max messages filter
        if [[ "$MAX_MESSAGES" -gt 0 ]]; then
            jq_filter="$jq_filter | select((.messageCount // 0) <= $MAX_MESSAGES)"
        fi

        # Extract session IDs with metadata (use | as delimiter since prompts may have tabs)
        # Use projectPath from each entry (more reliable than originalPath)
        jq -r "$jq_filter | [.sessionId, (.firstPrompt // \"No prompt\" | .[0:80] | gsub(\"[\\n\\r\\t|]\"; \" \")), .modified // \"\", .projectPath // \"$project_path\"] | join(\"|\")" "$index_file" 2>/dev/null || true

    done | sort -t'|' -k3 > "$tmp_all"  # Sort by modified date (field 3), oldest first

    # Apply date filter
    if [[ "$SINCE_DAYS" -ne 0 ]]; then
        if [[ "$SINCE_DAYS" -lt 0 ]]; then
            # Negative: from oldest day(s)
            local days_from_oldest=${SINCE_DAYS#-}  # Remove minus sign
            local oldest_date
            oldest_date=$(head -1 "$tmp_all" | cut -d'|' -f3 | cut -dT -f1)  # Get date part of oldest

            if [[ -n "$oldest_date" ]]; then
                local cutoff_date
                cutoff_date=$(date -j -v+"${days_from_oldest}"d -f "%Y-%m-%d" "$oldest_date" +%Y-%m-%dT23:59:59 2>/dev/null || \
                              date -d "$oldest_date + $days_from_oldest days" +%Y-%m-%dT23:59:59 2>/dev/null || echo "")

                if [[ -n "$cutoff_date" ]]; then
                    debug "Filtering oldest $days_from_oldest day(s): $oldest_date to ${cutoff_date:0:10}" >&2
                    awk -F'|' -v cutoff="$cutoff_date" '$3 <= cutoff' "$tmp_all" > "$SESSION_LIST"
                else
                    cp "$tmp_all" "$SESSION_LIST"
                fi
            else
                cp "$tmp_all" "$SESSION_LIST"
            fi
        else
            # Positive: from recent days
            local cutoff_date
            cutoff_date=$(date -v-"${SINCE_DAYS}"d +%Y-%m-%dT%H:%M:%S 2>/dev/null || \
                          date -d "$SINCE_DAYS days ago" +%Y-%m-%dT%H:%M:%S 2>/dev/null || echo "")

            if [[ -n "$cutoff_date" ]]; then
                awk -F'|' -v cutoff="$cutoff_date" '$3 >= cutoff' "$tmp_all" > "$SESSION_LIST"
            else
                cp "$tmp_all" "$SESSION_LIST"
            fi
        fi
    else
        cp "$tmp_all" "$SESSION_LIST"
    fi

    rm -f "$tmp_all"

    local count
    count=$(wc -l < "$SESSION_LIST" | tr -d ' ')
    log "Found $count sessions matching criteria (oldest first)" >&2
    echo "$count"
}

# Process a single session
process_session() {
    local line="$1"

    # Parse line (delimiter is |)
    local session_id first_prompt modified project
    IFS='|' read -r session_id first_prompt modified project <<< "$line"

    local result_file="$OUTPUT_DIR/${session_id}.md"
    local log_file="$OUTPUT_DIR/${session_id}.log"

    # Skip if already processed (and has content)
    if [[ -f "$result_file" && -s "$result_file" ]]; then
        debug "Skipping already processed: $session_id"
        return 0
    fi

    log "Processing session: $session_id"
    debug "  Prompt: ${first_prompt:0:60}..."
    debug "  Project: $project"

    # Determine the directory to run from (sessions are tied to project directories)
    local run_dir="${project:-$HOME}"
    if [[ ! -d "$run_dir" ]]; then
        run_dir="$HOME"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  [DRY RUN] Would invoke: (cd $run_dir && claude --resume $session_id --no-session-persistence --model $MODEL --print '/claudeception')"
        return 0
    fi

    # Run claudeception on this session
    local start_time
    start_time=$(date +%s)

    # The prompt to send
    local prompt="/claudeception

Review this session and extract any valuable knowledge into skills. Focus on:
1. Non-obvious solutions or debugging techniques
2. Error resolutions where the root cause wasn't obvious
3. Tool/API integration patterns
4. Workflow optimizations

If no valuable knowledge is found, respond with 'No extractable knowledge identified.'"

    # Use --no-session-persistence so no temp sessions are saved
    # The session history is loaded from the original but nothing is persisted
    # Note: </dev/null prevents claude from consuming stdin (which breaks the while loop)
    # Run from the project directory where the session was created
    if (cd "$run_dir" && claude --resume "$session_id" \
              --no-session-persistence \
              --model "$MODEL" \
              --print \
              "$prompt") < /dev/null > "$result_file" 2> "$log_file"; then
        local end_time duration
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        success "Completed $session_id in ${duration}s"

        # Check if any skills were extracted
        if grep -q "No extractable knowledge" "$result_file" 2>/dev/null; then
            debug "  No skills extracted"
        else
            log "  Skills may have been extracted - check $result_file"
        fi
        return 0
    else
        # Check if it's a missing session error
        if grep -q "No conversation found" "$log_file" 2>/dev/null; then
            warn "Session no longer exists: $session_id (skipping)"
            rm -f "$result_file" "$log_file"
            return 0  # Don't count as failure, just skip
        fi
        warn "Failed to process $session_id - see $log_file"
        return 1
    fi
}

# Main execution
main() {
    # Handle cleanup command
    if [[ "$CLEANUP" == "true" ]]; then
        cleanup_results
        exit 0
    fi

    local total
    total=$(collect_sessions)

    if [[ "$total" -eq 0 ]]; then
        warn "No sessions found to process"
        exit 0
    fi

    # Apply limit if specified
    local sessions_to_process="$SESSION_LIST"
    if [[ "$LIMIT" -gt 0 ]]; then
        local limited_list=$(mktemp)
        head -n "$LIMIT" "$SESSION_LIST" > "$limited_list"
        sessions_to_process="$limited_list"
        local limited_count
        limited_count=$(wc -l < "$limited_list" | tr -d ' ')
        log "Limited to $limited_count sessions"
    fi

    # Process sessions
    local processed=0
    local failed=0

    if [[ "$PARALLEL" -gt 1 ]]; then
        log "Processing with parallelism=$PARALLEL"

        # Export necessary variables and functions for parallel execution
        export DRY_RUN OUTPUT_DIR MODEL VERBOSE
        export -f process_session log warn error success debug

        cat "$sessions_to_process" | xargs -P "$PARALLEL" -I {} bash -c 'process_session "$@"' _ {}
    else
        debug "Reading sessions from: $sessions_to_process"
        debug "File contents: $(wc -l < "$sessions_to_process") lines"
        while IFS= read -r line || [[ -n "$line" ]]; do
            [[ -z "$line" ]] && continue
            debug "Processing line: ${line:0:50}..."
            if process_session "$line"; then
                ((processed++)) || true
            else
                ((failed++)) || true
            fi
        done < "$sessions_to_process"
    fi

    echo ""
    log "Processing complete"
    log "  Processed: $processed"
    log "  Failed: $failed"
    log "  Results saved to: $OUTPUT_DIR"
}

main
