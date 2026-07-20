#!/bin/bash
# Simple claudeception stats - readable by Claude

LOG=~/.claude/claudeception.log
HOOK_LOG=~/.claude/claudeception-hook.log

echo "=== CLAUDECEPTION STATS ==="
echo "Period: Last 7 days"
echo ""

echo "FUNNEL:"
echo "  Hook invocations: $(grep -c "UserPromptSubmit hook triggered" "$HOOK_LOG" 2>/dev/null || echo 0)"
echo "  Analyses run:     $(grep -c "Claudeception extraction started" "$LOG" 2>/dev/null || echo 0)"
echo "  Skills created:   $(grep -c "Created skill:" "$LOG" 2>/dev/null || echo 0)"
echo "  Duplicates blocked: $(grep -c "Similar skills exist" "$LOG" 2>/dev/null || echo 0)"
echo ""

echo "RECENT EXTRACTIONS:"
grep "Created skill:" "$LOG" 2>/dev/null | tail -5 || echo "  (none)"
echo ""

echo "RECENT SKIPS (why no extraction):"
grep -E "too short|No skill extraction|Similar skills" "$LOG" 2>/dev/null | tail -5 || echo "  (none)"
echo ""

echo "SKILLS DIRECTORY:"
ls -1 ~/.claude/my-claude-skills/skills/ 2>/dev/null | wc -l | xargs echo "  Total skills:"
echo ""

echo "To improve extraction, Claude should:"
echo "  1. Read this log: ~/.claude/claudeception.log"
echo "  2. Check recent sessions for missed opportunities"
echo "  3. Adjust extraction criteria in SKILL.md"
