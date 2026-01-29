#!/usr/bin/env python3
"""
Session Optimizer - Extract configuration improvements from Claude Code sessions.

Analyzes a session file to find:
1. Tools to pre-grant (frequently requested)
2. Skills to create (repeated investigations)
3. CLAUDE.md rules (user corrections)

Usage: python3 session-optimizer.py SESSION.jsonl
"""

import json
import sys
import re
from collections import Counter, defaultdict
from datetime import datetime

if len(sys.argv) < 2:
    print("Usage: python3 session-optimizer.py SESSION.jsonl", file=sys.stderr)
    sys.exit(1)

session_file = sys.argv[1]

# Data collectors
bash_commands = Counter()
tool_requests = Counter()
user_corrections = []
investigation_patterns = []
repeated_lookups = Counter()
error_patterns = Counter()

# Patterns for detection
CORRECTION_KEYWORDS = [
    'no,', 'no ', 'wrong', 'stop', "don't", "dont", 'not what',
    'should be', 'actually,', 'i said', 'i meant', 'still not',
    'already', 'forgot', 'i told you'
]

INVESTIGATION_KEYWORDS = [
    'let me check', 'let me investigate', 'let me look',
    'trying to understand', 'not sure why', 'let me see',
    'need to figure out', 'debugging', 'looking into'
]

with open(session_file, 'r') as f:
    for line in f:
        try:
            data = json.loads(line)
            msg = data.get('message', {})
            role = msg.get('role', '')

            for c in msg.get('content', []):
                if not isinstance(c, dict):
                    continue

                # Track tool usage
                if c.get('type') == 'tool_use':
                    tool_name = c.get('name', 'unknown')
                    tool_requests[tool_name] += 1

                    # Extract bash command patterns
                    if tool_name == 'Bash':
                        cmd = c.get('input', {}).get('command', '')
                        if cmd:
                            # Categorize command
                            parts = cmd.split()
                            if parts:
                                base = parts[0]
                                if base in ['git', 'glab', 'npm', 'yarn', 'docker', 'kubectl']:
                                    pattern = f"{base} {parts[1]}" if len(parts) > 1 else base
                                    bash_commands[f"Bash({base} *)"] += 1
                                elif 'lint' in cmd or 'format' in cmd:
                                    bash_commands["Bash(*lint*)"] += 1

                # Track user corrections
                if role == 'user' and c.get('type') == 'text':
                    text = c.get('text', '').lower()
                    if any(kw in text for kw in CORRECTION_KEYWORDS):
                        if 'continued from' not in text and len(text) < 500:
                            user_corrections.append(c.get('text', '')[:200])

                # Track investigation patterns
                if role == 'assistant' and c.get('type') == 'text':
                    text = c.get('text', '').lower()
                    if any(kw in text for kw in INVESTIGATION_KEYWORDS):
                        # Extract what's being investigated
                        full_text = c.get('text', '')[:150]
                        investigation_patterns.append(full_text)

                    # Track error messages being handled
                    if 'error' in text or 'failed' in text or 'exception' in text:
                        # Extract potential error identifiers
                        for match in re.findall(r'[A-Z][A-Z_]+(?:Error|Exception|Failed)', c.get('text', '')):
                            error_patterns[match] += 1

        except (json.JSONDecodeError, KeyError):
            pass

# Analyze repeated investigations
investigation_topics = Counter()
for inv in investigation_patterns:
    # Extract key nouns/topics
    words = inv.lower().split()
    for word in words:
        if len(word) > 5 and word not in ['check', 'investigate', 'looking', 'trying', 'understand']:
            investigation_topics[word] += 1

# Output recommendations
print("=" * 70)
print("SESSION OPTIMIZATION RECOMMENDATIONS")
print("=" * 70)
print(f"\nFile: {session_file}")

# 1. Tools to pre-grant
print("\n" + "=" * 70)
print("1. TOOLS TO PRE-GRANT")
print("   (Commands used frequently - consider adding to allowed tools)")
print("=" * 70)

high_frequency = [(cmd, count) for cmd, count in bash_commands.most_common(20) if count >= 10]
if high_frequency:
    for cmd, count in high_frequency:
        print(f"   {count:4d}x  {cmd}")
    print("\n   Add to settings.json or .claude/settings.local.json:")
    print('   "permissions": {')
    print('     "allow": [')
    for cmd, _ in high_frequency[:5]:
        print(f'       "{cmd}",')
    print('     ]')
    print('   }')
else:
    print("   No commands used 10+ times")

# 2. Skills to create
print("\n" + "=" * 70)
print("2. SKILLS TO CREATE")
print("   (Repeated investigations suggest missing knowledge)")
print("=" * 70)

# Find repeated investigation topics
repeated_topics = [(topic, count) for topic, count in investigation_topics.most_common(20) if count >= 3]
if repeated_topics:
    print("\n   Topics investigated multiple times:")
    for topic, count in repeated_topics[:10]:
        print(f"   {count:4d}x  {topic}")
    print("\n   Consider creating skills for frequently investigated topics.")
else:
    print("   No repeated investigation patterns found")

# Show actual investigation snippets
if investigation_patterns:
    print("\n   Sample investigations:")
    seen = set()
    count = 0
    for inv in investigation_patterns:
        short = inv[:80].replace('\n', ' ')
        if short not in seen:
            print(f"   - {short}...")
            seen.add(short)
            count += 1
            if count >= 5:
                break

# 3. CLAUDE.md rules
print("\n" + "=" * 70)
print("3. CLAUDE.md RULES TO ADD")
print("   (User corrections indicate missing guidance)")
print("=" * 70)

if user_corrections:
    print(f"\n   Found {len(user_corrections)} user corrections:")
    seen = set()
    for corr in user_corrections[:10]:
        short = corr[:100].replace('\n', ' ')
        if short not in seen:
            print(f"   - \"{short}...\"")
            seen.add(short)
    print("\n   Review these corrections and add rules to prevent repeats.")
else:
    print("   No obvious user corrections found")

# 4. Error patterns
print("\n" + "=" * 70)
print("4. ERROR PATTERNS ENCOUNTERED")
print("   (Consider documenting fixes as skills)")
print("=" * 70)

if error_patterns:
    for err, count in error_patterns.most_common(10):
        if count >= 2:
            print(f"   {count:4d}x  {err}")
else:
    print("   No repeated error patterns found")

# 5. Tool usage summary
print("\n" + "=" * 70)
print("5. TOOL USAGE SUMMARY")
print("=" * 70)

for tool, count in tool_requests.most_common(15):
    print(f"   {count:4d}x  {tool}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"   Total tool calls: {sum(tool_requests.values()):,}")
print(f"   User corrections: {len(user_corrections)}")
print(f"   Investigation cycles: {len(investigation_patterns)}")
print(f"   Unique error types: {len(error_patterns)}")
print()
