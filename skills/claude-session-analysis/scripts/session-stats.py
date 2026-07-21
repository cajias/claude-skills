#!/usr/bin/env python3
"""Extract comprehensive stats from a Claude Code session file.

Usage: python3 session-stats.py SESSION.jsonl
"""
import sys
import json
from datetime import datetime
from collections import Counter

if len(sys.argv) < 2:
    print("Usage: python3 session-stats.py SESSION.jsonl", file=sys.stderr)
    sys.exit(1)

session_file = sys.argv[1]

stats = {
    'user_messages': 0,
    'assistant_messages': 0,
    'tool_uses': 0,
    'compactions': 0,
    'continuations': 0,
    'interruptions': 0,
    'first_timestamp': None,
    'last_timestamp': None,
}
tools = Counter()
summaries = []

with open(session_file, 'r') as f:
    for line in f:
        try:
            data = json.loads(line)

            # Track timestamps
            ts = data.get('timestamp')
            if ts:
                if not stats['first_timestamp']:
                    stats['first_timestamp'] = ts
                stats['last_timestamp'] = ts

            # Count message types
            if 'message' in data:
                role = data['message'].get('role')
                if role == 'user':
                    stats['user_messages'] += 1
                elif role == 'assistant':
                    stats['assistant_messages'] += 1

                # Count tool uses and track names
                content = data['message'].get('content', [])
                if isinstance(content, str):
                    content = [{'type': 'text', 'text': content}]
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    if c.get('type') == 'tool_use':
                        stats['tool_uses'] += 1
                        tools[c.get('name', 'unknown')] += 1
                    if c.get('type') == 'text':
                        text = c.get('text', '')
                        if 'continued from a previous conversation' in text:
                            stats['continuations'] += 1
                        if 'interrupted by user' in text.lower():
                            stats['interruptions'] += 1

            # Count summaries (from compactions)
            if data.get('type') == 'summary':
                stats['compactions'] += 1
                summaries.append(data.get('summary', ''))

        except (json.JSONDecodeError, KeyError):
            pass

# Calculate duration
duration = "Unknown"
if stats['first_timestamp'] and stats['last_timestamp']:
    try:
        start = datetime.fromisoformat(stats['first_timestamp'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(stats['last_timestamp'].replace('Z', '+00:00'))
        delta = end - start
        days = delta.days
        hours = delta.seconds // 3600
        if days > 0:
            duration = f"{days} days, {hours} hours"
        else:
            duration = f"{hours} hours, {(delta.seconds % 3600) // 60} minutes"
    except:
        pass

# Health assessment
def health_rating(compactions, interruptions, days):
    issues = []
    if compactions > 15:
        issues.append(f"CRITICAL: {compactions} compactions (extreme context debt)")
    elif compactions > 5:
        issues.append(f"WARNING: {compactions} compactions (moderate context loss)")

    if interruptions > 8:
        issues.append(f"CRITICAL: {interruptions} interruptions (frequent user corrections)")
    elif interruptions > 3:
        issues.append(f"WARNING: {interruptions} interruptions (some user corrections)")

    if days and days > 7:
        issues.append(f"WARNING: {days} day session (consider splitting)")

    return issues if issues else ["HEALTHY: No major issues detected"]

# Output
print("=" * 60)
print("SESSION ANALYSIS")
print("=" * 60)
print(f"File: {session_file}")
print(f"Duration: {duration}")
print(f"First: {stats['first_timestamp']}")
print(f"Last:  {stats['last_timestamp']}")
print()
print("--- Message Counts ---")
print(f"User messages:      {stats['user_messages']:,}")
print(f"Assistant messages: {stats['assistant_messages']:,}")
print(f"Tool uses:          {stats['tool_uses']:,}")
print()
print("--- Session Health ---")
print(f"Context compactions: {stats['compactions']}")
print(f"Session continuations: {stats['continuations']}")
print(f"User interruptions: {stats['interruptions']}")
print()

days = None
if stats['first_timestamp'] and stats['last_timestamp']:
    try:
        start = datetime.fromisoformat(stats['first_timestamp'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(stats['last_timestamp'].replace('Z', '+00:00'))
        days = (end - start).days
    except:
        pass

print("--- Health Assessment ---")
for issue in health_rating(stats['compactions'], stats['interruptions'], days):
    print(f"  {issue}")
print()

print("--- Top 10 Tools ---")
for name, count in tools.most_common(10):
    print(f"  {count:4d} {name}")
print()

if summaries:
    print("--- Compaction Summaries ---")
    for s in summaries[:10]:
        print(f"  - {s[:80]}")
    if len(summaries) > 10:
        print(f"  ... and {len(summaries) - 10} more")
