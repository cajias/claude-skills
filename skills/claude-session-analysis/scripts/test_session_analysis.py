#!/usr/bin/env python3
"""Regression tests for the string-content normalization fix in the three
session-analysis scripts.

The fix under test (present in all three scripts)::

    content = msg.get('content', [])
    if isinstance(content, str):
        content = [{'type': 'text', 'text': content}]

Before the fix, a user message whose ``content`` was a plain string (rather
than a list of content blocks) was iterated character-by-character; each
character is a ``str`` (not a ``dict``) and was skipped, so the whole message
was silently dropped. After the fix the string is wrapped in a single text
block and processed normally.

The scripts are standalone (no package, no importable module), so each test
runs the script as a subprocess and inspects its stdout:

- ``user-messages.py``    reads JSONL from **stdin**
- ``session-stats.py``    reads a session file path from **argv[1]**
- ``session-optimizer.py`` reads a session file path from **argv[1]**

Run with system pytest::

    python3 -m pytest skills/claude-session-analysis/scripts/test_session_analysis.py -v

or, without pytest, execute the file directly (falls back to a plain runner)::

    python3 skills/claude-session-analysis/scripts/test_session_analysis.py
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
USER_MESSAGES = SCRIPTS_DIR / "user-messages.py"
SESSION_STATS = SCRIPTS_DIR / "session-stats.py"
SESSION_OPTIMIZER = SCRIPTS_DIR / "session-optimizer.py"


def _jsonl(records):
    """Serialize a list of dicts into JSONL text (one JSON object per line)."""
    return "".join(json.dumps(rec) + "\n" for rec in records)


def _write_session(tmp_path, name, records):
    """Write JSONL records to a temp session file and return its path."""
    session = tmp_path / name
    session.write_text(_jsonl(records))
    return session


def _run_stdin(script, stdin_text, *extra_args):
    """Run a script feeding JSONL on stdin."""
    return subprocess.run(
        [sys.executable, str(script), *extra_args],
        input=stdin_text,
        capture_output=True,
        text=True,
    )


def _run_file(script, session_path, *extra_args):
    """Run a script passing a session file path as argv."""
    return subprocess.run(
        [sys.executable, str(script), str(session_path), *extra_args],
        capture_output=True,
        text=True,
    )


def test_user_messages_prints_string_and_list_content(tmp_path):
    """A string-content user message is printed alongside a list-content one.

    Before the fix only the list-content message survived.
    """
    string_msg = "please rebase the branch onto main"
    list_msg = "run the full test suite please"
    records = [
        {"message": {"role": "user", "content": string_msg}},
        {"message": {"role": "user", "content": [{"type": "text", "text": list_msg}]}},
    ]

    result = _run_stdin(USER_MESSAGES, _jsonl(records))

    assert result.returncode == 0, result.stderr
    assert string_msg in result.stdout
    assert list_msg in result.stdout


def test_user_messages_filters_continuation_string(tmp_path):
    """A continuation string is still filtered out after normalization.

    This proves the text-handling path (continuation filter) actually runs on
    normalized string content, not that the message was dropped wholesale.
    """
    real_msg = "please rebase the branch onto main"
    continuation = "This was continued from a previous conversation about deploys"
    records = [
        {"message": {"role": "user", "content": continuation}},
        {"message": {"role": "user", "content": real_msg}},
    ]

    result = _run_stdin(USER_MESSAGES, _jsonl(records))

    assert result.returncode == 0, result.stderr
    assert real_msg in result.stdout
    assert "continued from a previous conversation" not in result.stdout


def test_session_stats_counts_string_content(tmp_path):
    """String-content messages feed the continuation/interruption counters."""
    records = [
        {
            "message": {
                "role": "user",
                "content": "This session continued from a previous conversation earlier",
            }
        },
        {
            "message": {
                "role": "user",
                "content": "The last action was interrupted by user before it finished",
            }
        },
    ]
    session = _write_session(tmp_path, "session.jsonl", records)

    result = _run_file(SESSION_STATS, session)

    assert result.returncode == 0, result.stderr
    assert "Session continuations: 1" in result.stdout
    assert "User interruptions: 1" in result.stdout


def test_session_optimizer_detects_string_correction(tmp_path):
    """A string-content correction is reported, and list-content tool_use is tracked."""
    correction = "no, that is wrong"  # matches CORRECTION_KEYWORDS 'no,' and 'wrong'
    records = [
        {"message": {"role": "user", "content": correction}},
        {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {"command": "git status"},
                    }
                ],
            }
        },
    ]
    session = _write_session(tmp_path, "session.jsonl", records)

    result = _run_file(SESSION_OPTIMIZER, session)

    assert result.returncode == 0, result.stderr
    # Correction from the string-content message is surfaced.
    assert "User corrections: 1" in result.stdout
    assert correction in result.stdout
    # List-content assistant tool_use still tracked in the usage summary.
    assert "Bash" in result.stdout


def _main():
    """Minimal pytest-free runner: execute each test with a temp dir."""
    import tempfile
    import traceback

    tests = [
        test_user_messages_prints_string_and_list_content,
        test_user_messages_filters_continuation_string,
        test_session_stats_counts_string_content,
        test_session_optimizer_detects_string_correction,
    ]
    failures = 0
    for test in tests:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                test(Path(tmp))
                print(f"PASS {test.__name__}")
            except Exception:  # noqa: BLE001 - simple standalone runner
                failures += 1
                print(f"FAIL {test.__name__}")
                traceback.print_exc()
    if failures:
        print(f"\n{failures} failed")
        sys.exit(1)
    print(f"\n{len(tests)} passed")


if __name__ == "__main__":
    _main()
