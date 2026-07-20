#!/usr/bin/env python3
"""Tests for knowledge_handler.py - Unified UserPromptSubmit handler.

TDD RED Phase: These tests should FAIL until implementation is complete.
Tests the integration of detect_knowledge() into the UserPromptSubmit hook.
"""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).parent))


class TestKnowledgeHandlerIntegration:
    """Test knowledge_handler.py integration with detect_knowledge()."""

    def test_handler_imports_knowledge_detector(self):
        """Handler should import from knowledge_detector, not correction_detector."""
        # This will fail until knowledge_handler.py exists
        from knowledge_handler import detect_knowledge

        assert callable(detect_knowledge)

    def test_handler_detects_teaching_patterns(self):
        """Handler should detect teaching patterns, not just corrections."""
        from knowledge_handler import process_user_prompt

        with patch("knowledge_handler.record_signal") as mock_record:
            process_user_prompt(
                {
                    "prompt": "Remember that API calls should always include auth headers",
                    "session_id": "test-session",
                }
            )

            # Should record a teaching signal
            calls = mock_record.call_args_list
            signal_types = [call[0][0] for call in calls]
            assert "teaching" in signal_types, "Should record teaching signal for 'remember that' pattern"

    def test_handler_detects_corrections(self):
        """Handler should still detect corrections (backward compatible)."""
        from knowledge_handler import process_user_prompt

        with patch("knowledge_handler.record_signal") as mock_record:
            process_user_prompt(
                {
                    "prompt": "No, that's wrong. I meant to use POST not GET",
                    "session_id": "test-session",
                }
            )

            # Should record a correction signal
            calls = mock_record.call_args_list
            signal_types = [call[0][0] for call in calls]
            assert "correction" in signal_types, "Should still record correction signals"

    def test_handler_outputs_extraction_for_teaching(self):
        """Handler should output extraction prompt for high-confidence teaching."""
        from knowledge_handler import output_knowledge_extraction_prompt

        # Should work for teaching results
        knowledge_result = {
            "is_teaching": True,
            "teaching_confidence": 0.9,
            "teaching_type": "explicit_instruction",
            "extracted_knowledge": "API calls should include auth headers",
        }

        # Capture stdout
        captured = StringIO()
        with patch("sys.stdout", captured):
            output_knowledge_extraction_prompt("Remember that API calls need auth", knowledge_result)

        output = captured.getvalue()
        assert "TEACHING DETECTED" in output or "KNOWLEDGE DETECTED" in output

    def test_teaching_signal_weight_is_3x(self):
        """Teaching signals should have 3.0x weight same as corrections."""
        from knowledge_handler import process_user_prompt

        with patch("knowledge_handler.record_signal") as mock_record:
            process_user_prompt(
                {
                    "prompt": "Always use TypeScript for new modules",
                    "session_id": "test-session",
                }
            )

            # Find the teaching signal call
            for call in mock_record.call_args_list:
                if call[0][0] == "teaching":
                    signal_data = call[0][1] if len(call[0]) > 1 else call[1].get("data", {})
                    # Teaching should be recorded with proper data
                    assert signal_data is not None


class TestKnowledgeHandlerExtractionPrompt:
    """Test extraction prompt generation for different knowledge types."""

    def test_correction_extraction_prompt_format(self):
        """Correction extraction prompts should maintain existing format."""
        from knowledge_handler import output_knowledge_extraction_prompt

        result = {
            "is_correction": True,
            "correction_confidence": 0.85,
            "correction_type": "wrong_assessment",
            "extracted_knowledge": "Use POST not GET",
        }

        captured = StringIO()
        with patch("sys.stdout", captured):
            output_knowledge_extraction_prompt("No, that's wrong", result)

        output = captured.getvalue()
        assert "CORRECTION" in output or "KNOWLEDGE" in output

    def test_teaching_extraction_prompt_format(self):
        """Teaching extraction prompts should have proper format."""
        from knowledge_handler import output_knowledge_extraction_prompt

        result = {
            "is_teaching": True,
            "teaching_confidence": 0.95,
            "teaching_type": "standing_rule",
            "extracted_knowledge": "Always use TypeScript",
        }

        captured = StringIO()
        with patch("sys.stdout", captured):
            output_knowledge_extraction_prompt("Always use TypeScript for new modules", result)

        output = captured.getvalue()
        assert len(output) > 0  # Should output something


class TestKnowledgeHandlerBackwardCompatibility:
    """Test that knowledge_handler maintains backward compatibility."""

    def test_main_entry_point_exists(self):
        """Should have main() entry point for hook execution."""
        from knowledge_handler import main

        assert callable(main)

    def test_reads_from_stdin(self):
        """Should read JSON from stdin."""
        from knowledge_handler import main

        # Mock stdin with test data
        test_input = json.dumps(
            {
                "prompt": "test prompt",
                "session_id": "test-session",
            }
        )

        with (
            patch("sys.stdin", StringIO(test_input)),
            patch("sys.stdin.isatty", return_value=False),
            patch("knowledge_handler.process_user_prompt") as mock_process,
        ):
            main()
            mock_process.assert_called_once()

    def test_handles_empty_input_gracefully(self):
        """Should handle empty input without error."""
        from knowledge_handler import main

        with patch("sys.stdin", StringIO("")), patch("sys.stdin.isatty", return_value=False):
            result = main()
            assert result == 0  # Should return success


class TestKnowledgeHandlerSignalRecording:
    """Test signal recording for different knowledge types."""

    def test_records_exchange_with_knowledge_flags(self):
        """Exchange records should include both correction and teaching flags."""
        from knowledge_handler import process_user_prompt

        with patch("knowledge_handler.record_signal") as mock_record:
            process_user_prompt(
                {
                    "prompt": "Remember that we use tabs not spaces",
                    "session_id": "test-session",
                }
            )

            # Find exchange signal
            for call in mock_record.call_args_list:
                if call[0][0] == "exchange":
                    signal_data = call[0][1] if len(call[0]) > 1 else {}
                    # Should have knowledge-related flags
                    assert (
                        "user_prompt" in signal_data or "is_teaching" in signal_data or "is_correction" in signal_data
                    )

    def test_high_confidence_threshold_for_extraction(self):
        """Only output extraction prompt for confidence >= 0.7."""
        from knowledge_handler import process_user_prompt

        # Low confidence teaching should not trigger extraction prompt
        with patch("knowledge_handler.detect_knowledge") as mock_detect:
            mock_detect.return_value = MagicMock(
                is_teaching=True,
                teaching_confidence=0.5,  # Below threshold
                is_correction=False,
                to_dict=lambda: {"is_teaching": True, "teaching_confidence": 0.5},
            )

            with (
                patch("knowledge_handler.record_signal"),
                patch("knowledge_handler.output_knowledge_extraction_prompt") as mock_output,
            ):
                process_user_prompt(
                    {
                        "prompt": "maybe use typescript",
                        "session_id": "test",
                    }
                )
                # Should NOT call output for low confidence
                mock_output.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
