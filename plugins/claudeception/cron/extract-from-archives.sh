#!/usr/bin/env bash
# extract-from-archives.sh — Process recent conversation archives for skill extraction.
#
# Finds JSONL archives modified in last 2 hours, converts to text,
# asks Claude (headless) to extract skills, and pipes to extract-skills.py.
# Caps at 5 sessions per run.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARCHIVE_DIR="$HOME/.config/superpowers/conversation-archive"
PROCESSED_DIR="$HOME/.claude/claudeception-metrics/processed"
LOG_FILE="$HOME/.claude/claudeception-cron.log"
EXTRACT_SKILLS="$SCRIPT_DIR/../hooks/extract-skills.py"
ARCHIVE_TO_TEXT="$SCRIPT_DIR/archive-to-text.py"
MAX_SESSIONS=5
TMPDIR="${TMPDIR:-/tmp}"

mkdir -p "$PROCESSED_DIR"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" >> "$LOG_FILE"
}

log "=== Cron extraction run started ==="

if [ ! -d "$ARCHIVE_DIR" ]; then
    log "Archive directory not found: $ARCHIVE_DIR"
    exit 0
fi

processed=0

# Collect files into array first (avoids subshell from pipe)
mapfile -t jsonl_files < <(find "$ARCHIVE_DIR" -name '*.jsonl' -mmin -120 -type f 2>/dev/null | head -50)

for jsonl_file in "${jsonl_files[@]}"; do
    if [ "$processed" -ge "$MAX_SESSIONS" ]; then
        log "Hit max sessions ($MAX_SESSIONS), stopping"
        break
    fi

    # Use filename as marker (unique session ID)
    marker_name="$(basename "$jsonl_file" .jsonl)"
    if [ -f "$PROCESSED_DIR/$marker_name" ]; then
        continue
    fi

    log "Processing: $jsonl_file"

    # Convert JSONL to readable text, write to temp file
    conv_file=$(mktemp "$TMPDIR/claudeception-conv.XXXXXX")
    if ! python3 "$ARCHIVE_TO_TEXT" "$jsonl_file" > "$conv_file" 2>/dev/null; then
        log "  Failed to convert archive to text: $jsonl_file"
        rm -f "$conv_file"
        continue
    fi

    conv_size=$(wc -c < "$conv_file")
    if [ "$conv_size" -lt 200 ]; then
        log "  Conversation too short ($conv_size bytes), skipping"
        touch "$PROCESSED_DIR/$marker_name"
        rm -f "$conv_file"
        continue
    fi

    log "  Converted to text ($conv_size bytes)"

    # Build extraction prompt in a temp file
    prompt_file=$(mktemp "$TMPDIR/claudeception-prompt.XXXXXX")
    cat > "$prompt_file" <<'PROMPT_HEADER'
Analyze this conversation for skill-worthy knowledge. Extract reusable patterns, discoveries, workarounds, or best practices.

Rules:
- Only extract knowledge that is REUSABLE across projects
- Must be NON-OBVIOUS (required investigation)
- Must be VERIFIED (actually worked in the conversation)
- Skip project-specific details

If skills found, respond with ONLY a JSON object (no markdown fences):
{"skills": [{"name": "kebab-case-name", "title": "Title", "description": "One liner", "problem": "Problem description", "triggers": "When to use", "solution": "The approach", "verification": "How to verify", "tags": ["tag1"], "confidence": 0.8}]}

If nothing worth extracting, respond with: {"skills": []}

CONVERSATION:
PROMPT_HEADER
    cat "$conv_file" >> "$prompt_file"
    rm -f "$conv_file"

    # Call Claude in headless mode
    response_file=$(mktemp "$TMPDIR/claudeception-response.XXXXXX")
    if ! claude -p --output-format json < "$prompt_file" > "$response_file" 2>/dev/null; then
        log "  Claude headless call failed for: $jsonl_file"
        rm -f "$prompt_file" "$response_file"
        continue
    fi
    rm -f "$prompt_file"

    log "  Got Claude response ($(wc -c < "$response_file") bytes)"

    # Extract skills JSON from Claude's response wrapper
    skills_json=$(python3 -c "
import sys, json
try:
    data = json.loads(open('$response_file').read())
    text = data.get('result', '') if isinstance(data, dict) else str(data)
    inner = json.loads(text)
    print(json.dumps(inner))
except Exception:
    try:
        print(json.dumps(data))
    except Exception:
        print('{}')
" 2>/dev/null) || skills_json="{}"
    rm -f "$response_file"

    # Check if we got valid skills
    has_skills=$(echo "$skills_json" | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(len(d.get('skills', [])))
except Exception:
    print(0)
" 2>/dev/null) || has_skills=0

    if [ "$has_skills" -gt 0 ]; then
        log "  Found $has_skills skills, piping to extract-skills.py"
        echo "$skills_json" | python3 "$EXTRACT_SKILLS" 2>>"$LOG_FILE" || {
            log "  extract-skills.py failed"
        }
    else
        log "  No skills extracted"
    fi

    # Mark as processed
    touch "$PROCESSED_DIR/$marker_name"
    processed=$((processed + 1))
    log "  Done (session $processed/$MAX_SESSIONS)"
done

log "=== Cron extraction run finished (processed: $processed) ==="
