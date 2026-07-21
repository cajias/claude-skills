#!/usr/bin/env python3
"""Claudeception v4.0 - Signal Accumulator.

PostToolUse hook that accumulates signals during a session:
- Tool errors (exit code != 0)
- Retries (same tool called multiple times)
- Web searches (WebFetch tool calls)

These signals feed into the breakthrough score formula.
"""

import json
import sys
from pathlib import Path


# Import session state module
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from session_state import get_session_state, init_session, log, record_signal
except ImportError:
    # Fallback logging
    def log(msg) -> None:
        print(f"[signal-accumulator] {msg}", file=sys.stderr)

    def init_session(session_id, metadata=None) -> None:
        pass

    def record_signal(signal_type, data=None) -> None:
        pass

    def get_session_state() -> None:
        return None


def process_tool_use(data: dict) -> None:
    """Process a PostToolUse event and record relevant signals."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    tool_response = data.get("tool_response", data.get("tool_output", {}))
    session_id = data.get("session_id", "")

    log(f"Processing tool use: {tool_name}")

    # Ensure session is initialized (only if no state exists)
    if session_id:
        try:
            state = get_session_state()
            if state is None:
                # No session exists - create one
                init_session(session_id, {"source": "signal_accumulator"})
            elif state.session_id != session_id:
                # Different session - this shouldn't happen often, log it
                log(f"Session mismatch: state has {state.session_id}, got {session_id}")
                # Don't reinitialize - preserve existing signals until Stop hook clears it
        except Exception as e:
            # Only initialize if we truly have no state
            log(f"Error getting session state: {e}")
            state = get_session_state()
            if state is None:
                init_session(session_id, {"source": "signal_accumulator"})

    # Check for errors
    if isinstance(tool_response, dict):
        exit_code = tool_response.get("exit_code")
        error = tool_response.get("error")
        stderr = tool_response.get("stderr", "")
    else:
        # string result (no structured error fields)
        exit_code = None
        error = None
        stderr = ""

    if exit_code and exit_code != 0:
        record_signal("error", {"tool": tool_name, "exit_code": exit_code, "error": error or stderr[:200]})
        log(f"Recorded error signal: {tool_name} exit_code={exit_code}")

    if error:
        record_signal("error", {"tool": tool_name, "error": str(error)[:200]})
        log(f"Recorded error signal: {tool_name} error={str(error)[:100]}")

    # Check for web searches
    if tool_name in ["WebFetch", "WebSearch", "mcp__web__fetch"]:
        record_signal("web_search", {"tool": tool_name, "url": tool_input.get("url", "")[:200]})
        log(f"Recorded web_search signal: {tool_name}")

    # Track tool usage for retry detection
    # This is handled by session_state's exchange tracking

    log(f"Signal accumulation complete for {tool_name}")


def main() -> int:
    """Main entry point for PostToolUse hook."""
    log("Signal accumulator started")

    # Read input from stdin
    if sys.stdin.isatty():
        log("No stdin input")
        return 0

    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            log("Empty input")
            return 0

        data = json.loads(input_data)
        log(f"Received PostToolUse data: {list(data.keys())}")

        process_tool_use(data)

    except json.JSONDecodeError as e:
        log(f"JSON decode error: {e}")
        return 1
    except Exception as e:
        log(f"Error processing tool use: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
