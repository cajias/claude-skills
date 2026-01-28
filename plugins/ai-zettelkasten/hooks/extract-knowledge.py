#!/usr/bin/env python3
"""AI Zettelkasten extraction hook - delegates to CLI.

This hook is invoked by Claude Code to extract knowledge from sessions.
It delegates to the zk-extract CLI command which handles the actual
extraction logic with proper dependencies managed by uvx.

Usage (by Claude Code):
    echo '{"items": [...]}' | python extract-knowledge.py

The hook expects JSON on stdin with the following format:
    {
        "items": [
            {
                "type": "fact|decision|pattern|correction",
                "title": "Short descriptive title",
                "content": "Full content/body",
                "tags": ["tag1", "tag2"],
                "confidence": 0.9
            }
        ]
    }
"""
import subprocess
import sys


def main():
    """Run the extraction via uvx with proper dependencies."""
    # Use uvx to run with proper dependencies
    result = subprocess.run(
        ["uvx", "--from", "ai-zettelkasten", "zk-extract"],
        stdin=sys.stdin,
        capture_output=False
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
