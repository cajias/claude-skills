#!/usr/bin/env python3
"""Extract user messages from a Claude Code session file.

Filters out continuation messages and short messages.

Usage: cat SESSION.jsonl | python3 user-messages.py [--limit N]
"""
import sys
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--limit', '-n', type=int, default=50, help='Max messages to show')
parser.add_argument('--include-continuations', action='store_true', help='Include continuation messages')
args = parser.parse_args()

count = 0
for line in sys.stdin:
    try:
        data = json.loads(line)
        if 'message' in data and data['message'].get('role') == 'user':
            for c in data['message'].get('content', []):
                if not isinstance(c, dict):
                    continue
                if c.get('type') == 'text':
                    text = c.get('text', '')
                    # Skip continuation messages unless requested
                    if not args.include_continuations and 'continued from a previous conversation' in text:
                        continue
                    # Skip very short messages
                    if len(text) < 10:
                        continue
                    count += 1
                    # Truncate and clean for display
                    display = text[:200].replace('\n', ' ')
                    print(f'{count:3d}. {display}')
                    if count >= args.limit:
                        sys.exit(0)
    except (json.JSONDecodeError, KeyError):
        pass
