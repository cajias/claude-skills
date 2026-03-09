#!/usr/bin/env python3
"""Convert a conversation archive JSONL file to readable text.

Usage: python3 archive-to-text.py <path-to-jsonl>
Output: Conversation text to stdout (max 50K chars).
"""

import json
import sys

MAX_CHARS = 50_000


def main():
    if len(sys.argv) < 2:
        print("Usage: archive-to-text.py <jsonl-file>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    output = []
    total = 0

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = entry.get("type", "")
            if msg_type not in ("user", "assistant"):
                continue

            message = entry.get("message", {})
            if not isinstance(message, dict):
                continue

            role = message.get("role", msg_type)
            content = message.get("content", "")

            # content can be a string or a list of content blocks
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, str):
                        parts.append(block)
                    elif isinstance(block, dict):
                        text = block.get("text", "")
                        if text:
                            parts.append(text)
                content = "\n".join(parts)

            if not content or not isinstance(content, str):
                continue

            chunk = f"[{role}]: {content}\n\n"
            total += len(chunk)
            if total > MAX_CHARS:
                # Add what fits and stop
                remaining = MAX_CHARS - (total - len(chunk))
                if remaining > 0:
                    output.append(chunk[:remaining])
                output.append("\n[TRUNCATED — exceeded 50K char limit]\n")
                break
            output.append(chunk)

    print("".join(output))


if __name__ == "__main__":
    main()
