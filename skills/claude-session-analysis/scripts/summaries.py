#!/usr/bin/env python3
"""Extract compaction summaries from a Claude Code session file.

Usage: cat SESSION.jsonl | python3 summaries.py
"""
import sys
import json

for line in sys.stdin:
    try:
        data = json.loads(line)
        if data.get('type') == 'summary':
            summary = data.get('summary', '')
            if summary:
                print(f'- {summary}')
    except (json.JSONDecodeError, KeyError):
        pass
