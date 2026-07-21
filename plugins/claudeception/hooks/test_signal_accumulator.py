#!/usr/bin/env python3
"""Tests for signal_accumulator.py - PostToolUse signal accumulation hook.

Covers the tool_response fix in process_tool_use():
- reads the PostToolUse "tool_response" key (was mistakenly "tool_output"),
- falls back to the legacy "tool_output" key when "tool_response" is absent,
- guards against a non-dict (string) response before calling .get(),
- records an "error" signal on a nonzero exit_code or an error field.
"""

from unittest.mock import patch

import pytest
import signal_accumulator


def _error_signal_calls(mock_record) -> list:
    """Return record_signal calls whose signal_type is 'error'."""
    return [c for c in mock_record.call_args_list if c[0] and c[0][0] == "error"]


class TestProcessToolUseErrors:
    """process_tool_use() error-signal recording via the tool_response key."""

    def test_reads_tool_response_key(self):
        """A nonzero exit_code under 'tool_response' records an error signal."""
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "grep x missing"},
            "session_id": "s1",
            "tool_response": {"exit_code": 2, "stderr": "grep: missing"},
        }

        with (
            patch("signal_accumulator.record_signal") as mock_record,
            patch("signal_accumulator.get_session_state", return_value=None),
            patch("signal_accumulator.init_session"),
        ):
            signal_accumulator.process_tool_use(data)

        errors = _error_signal_calls(mock_record)
        assert errors, "Expected an 'error' signal from a nonzero exit_code"
        assert errors[0][0][1]["exit_code"] == 2
        assert errors[0][0][1]["tool"] == "Bash"

    def test_tool_response_string_does_not_crash(self):
        """A string tool_response must not raise and records no error signal."""
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi"},
            "tool_response": "some string result",
        }

        with patch("signal_accumulator.record_signal") as mock_record:
            # Must not raise AttributeError on the string .get() path.
            signal_accumulator.process_tool_use(data)

        assert _error_signal_calls(mock_record) == []

    def test_legacy_tool_output_fallback(self):
        """The legacy 'tool_output' key still produces an error signal."""
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "false"},
            "tool_output": {"exit_code": 1, "error": "boom"},
        }

        with patch("signal_accumulator.record_signal") as mock_record:
            signal_accumulator.process_tool_use(data)

        assert _error_signal_calls(mock_record), "Expected fallback to legacy tool_output key"

    def test_no_error_on_success(self):
        """A zero exit_code records no error signal."""
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "true"},
            "tool_response": {"exit_code": 0},
        }

        with patch("signal_accumulator.record_signal") as mock_record:
            signal_accumulator.process_tool_use(data)

        assert _error_signal_calls(mock_record) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
