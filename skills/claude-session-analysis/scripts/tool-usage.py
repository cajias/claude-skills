#!/usr/bin/env python3
"""Extract tool usage counts from a Claude Code session file.

Usage: cat SESSION.jsonl | python3 tool-usage.py
   or: python3 tool-usage.py < SESSION.jsonl
"""
import sys
import json

tools = {}
for line in sys.stdin:
    try:
        data = json.loads(line)
        if 'message' in data and 'content' in data['message']:
            for c in data['message']['content']:
                if not isinstance(c, dict):
                    continue
                if c.get('type') == 'tool_use':
                    name = c.get('name', 'unknown')
                    tools[name] = tools.get(name, 0) + 1
    except (json.JSONDecodeError, KeyError):
        pass

for name, count in sorted(tools.items(), key=lambda x: -x[1]):
    print(f'{count:4d} {name}')
