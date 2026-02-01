---
name: claude-session-analysis
description: |
  Analyze Claude Code sessions to extract configuration improvements. Use when:
  (1) Want to optimize Claude Code setup (skills, permissions, CLAUDE.md),
  (2) Need to find what tools should be pre-granted (repeated permission requests),
  (3) Looking for skills to create (repeated investigation patterns),
  (4) Finding rules to add to CLAUDE.md (user corrections indicate missing guidance),
  (5) Diagnosing why sessions went poorly (compactions, interruptions).
  The goal is actionable improvements, not just metrics.
author: Claude Code
version: 2.0.0
date: 2026-01-26
tags: [optimization, sessions, skills, permissions, configuration]
---

# Claude Code Session Analysis

## Problem

Sessions often have friction: repeated permission requests, investigation cycles, user
corrections. Analyzing past sessions reveals what skills, permissions, and CLAUDE.md
rules would have made the work smoother. The goal is **configuration optimization**,
not just metrics.

## Context / Trigger Conditions

Use this skill when:

- Want to improve Claude Code configuration based on past sessions
- Looking for tools that should be pre-granted (asked for repeatedly)
- Finding skills to create (same investigation done multiple times)
- Identifying rules for CLAUDE.md (user kept correcting same mistakes)
- Diagnosing why a session had many interruptions or compactions

## Solution

### 1. Session File Locations

```bash
# Project-specific sessions
~/.claude/projects/-Users-USERNAME-Projects-PROJECT_NAME/

# Session files are named by UUID
SESSION_ID.jsonl                    # Main conversation
SESSION_ID/subagents/agent-*.jsonl  # Subagent conversations
SESSION_ID/tool-results/*.txt       # Large tool outputs
```

**Finding sessions for a project:**

```bash
# List all session directories for a project
ls -la ~/.claude/projects/-Users-cajias-Projects-PROJECT_NAME/

# Find sessions by date
ls -lt ~/.claude/projects/-Users-*-PROJECT/ | head -20
```

### 2. Session File Format

Each line is a JSON object with these key fields:

```json
{
  "type": "user" | "assistant" | "file-history-snapshot" | "queue-operation",
  "message": {
    "role": "user" | "assistant",
    "content": [{"type": "text", "text": "..."} | {"type": "tool_use", ...}]
  },
  "timestamp": "ISO8601",
  "sessionId": "UUID"
}
```

### 3. Diagnostic Commands

**Count context compactions:**

```bash
grep -c "Conversation compacted" SESSION_FILE.jsonl
```

**Find all sessions with compactions in a project:**

```bash
grep -l "Conversation compacted" ~/.claude/projects/-Users-*-PROJECT/*.jsonl
```

**Total compactions across all sessions:**

```bash
grep -c "Conversation compacted" ~/.claude/projects/-Users-*-PROJECT/*.jsonl 2>/dev/null | \
  awk -F: '{s+=$2} END {print "Total compactions:", s}'
```

**Extract user messages:**

```bash
grep -h '"role":"user"' SESSION_FILE.jsonl | \
  grep -o '"text":"[^"]*"' | \
  head -20
```

**Find user corrections/frustrations:**

```bash
grep -h '"role":"user"' SESSION_FILE.jsonl | \
  grep -o '"text":"[^"]*"' | \
  grep -iE "forgot|skip|should have|already|told you|repeat|wrong|mistake|again"
```

**Find repeated messages (indicates loops):**

```bash
grep -h '"text":"[^"]*"' SESSION_FILE.jsonl | \
  sort | uniq -c | sort -rn | head -10
```

**Find TDD-related patterns:**

```bash
grep -o '"text":"[^"]*"' SESSION_FILE.jsonl | \
  grep -iE "RED|GREEN|REFACTOR|test first|write test|failing test"
```

### 4. Analyzing Context Compaction Impact

**Find what was summarized:**

```bash
# Look for summary type messages
grep '"type":"summary"' SESSION_FILE.jsonl | jq '.summary' 2>/dev/null
```

**Find session continuation points:**

```bash
grep -i "continued from a previous conversation" SESSION_FILE.jsonl
```

**Identify compaction timing:**

```bash
grep "Conversation compacted" SESSION_FILE.jsonl | \
  grep -o '"timestamp":"[^"]*"'
```

### 5. Subagent Analysis

**List all subagents in a session:**

```bash
ls ~/.claude/projects/-Users-*-PROJECT/SESSION_ID/subagents/
```

**Find subagent that failed:**

```bash
grep -l "error\|failed\|exception" SESSION_ID/subagents/*.jsonl
```

### 6. Python-Based Parsing (For Large/Complex Sessions)

When grep patterns fail on large sessions, use the Python scripts in `scripts/` for reliable JSONL parsing.

**Full session analysis (recommended):**

```bash
SCRIPTS=~/.claude/skills/claude-session-analysis/scripts
python3 $SCRIPTS/session-stats.py SESSION.jsonl
```

**Individual scripts:**

```bash
# Extract tool usage counts
cat SESSION.jsonl | python3 $SCRIPTS/tool-usage.py

# Extract user messages (skips continuations)
cat SESSION.jsonl | python3 $SCRIPTS/user-messages.py --limit 20

# Extract compaction summaries
cat SESSION.jsonl | python3 $SCRIPTS/summaries.py
```

**Scripts included:**

- `session-optimizer.py` - **Main script** - extracts configuration recommendations
- `session-stats.py` - Comprehensive metrics with health assessment
- `tool-usage.py` - Tool usage frequency
- `user-messages.py` - User messages (with `--limit` and `--include-continuations` flags)
- `summaries.py` - Compaction summaries

### 7. Configuration Optimization (Primary Goal)

**Run the optimizer script:**

```bash
SCRIPTS=~/.claude/skills/claude-session-analysis/scripts
python3 $SCRIPTS/session-optimizer.py SESSION.jsonl
```

This extracts actionable recommendations:

- **Tools to pre-grant** - Commands requested 10+ times
- **Skills to create** - Investigation patterns that repeated
- **CLAUDE.md rules** - User corrections indicate missing guidance

**What each finding means:**

| Finding                        | Action                             |
| ------------------------------ | ---------------------------------- |
| `Bash(glab *) requested 50x`   | Add to allowed tools in settings   |
| `"!reference" investigated 3x` | Create a skill documenting the fix |
| `User said "no, use X" 5x`     | Add rule to CLAUDE.md              |

### 8. Session Health Benchmarks

| Metric        | Healthy | Warning  | Critical |
| ------------- | ------- | -------- | -------- |
| Compactions   | 0-5     | 6-15     | 16+      |
| Interruptions | 0-3     | 4-8      | 9+       |
| Duration      | <1 day  | 1-7 days | >1 week  |

**Interpretation:**

- **44 compactions** = extreme context debt, session should have been split
- **16+ interruptions** = agent frequently going wrong direction
- **Multi-week sessions** = accumulated context loss makes later work unreliable

### 9. Pattern Recognition

**Signs of lost context:**

- Same exploration text repeated 3+ times
- User messages containing "again" or "already"
- Multiple identical tool calls in sequence
- Sudden shift from GREEN phase back to exploration

**Signs of TDD violations:**

- Implementation file edits without prior test file creation
- "Let me implement" without "tests are failing" context
- No RED/GREEN/REFACTOR pattern in todo items

## Example Analysis

```bash
# Full diagnostic for a problematic session
SESSION="/Users/cajias/.claude/projects/-Users-cajias-Projects-myproject/abc123.jsonl"

echo "=== Compaction Count ==="
grep -c "Conversation compacted" "$SESSION"

echo "=== User Corrections ==="
grep -h '"role":"user"' "$SESSION" | grep -o '"text":"[^"]*"' | \
  grep -iE "forgot|wrong|already" | head -5

echo "=== Repeated Messages ==="
grep -h '"text":"' "$SESSION" | sort | uniq -c | sort -rn | head -5

echo "=== TDD Phase Mentions ==="
grep -o '"text":"[^"]*"' "$SESSION" | grep -iE "RED|GREEN|REFACTOR" | head -5
```

## Verification

Analysis is successful when you can answer:

1. **Tools to pre-grant**: What commands were requested 10+ times?
2. **Skills to create**: What topics were investigated repeatedly?
3. **CLAUDE.md rules**: What did the user keep correcting?
4. **Session health**: Was the session too long? Too many compactions?

## Notes

- Session files can be large (100MB+) - use `head` or `limit` flags
- JSONL lines are often truncated in grep output - use Python scripts for full parsing
- Subagent files follow same format as main session
- Tool results may be stored separately in `tool-results/` directory
- Timestamps are ISO8601 format, useful for correlating with git commits
- **Scripts location**: `~/.claude/skills/claude-session-analysis/scripts/`
