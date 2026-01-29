#!/usr/bin/env python3
"""
Tests for knowledge_detector.py - Unified correction + teaching detection.

TDD RED Phase: These tests should FAIL until implementation is complete.
"""

import pytest
import sys
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).parent))


class TestTeachingPatternDetection:
    """Test detection of teaching patterns in user messages."""

    def test_detect_remember_that_pattern(self):
        """Should detect 'remember that...' as explicit instruction."""
        from knowledge_detector import detect_teaching

        result = detect_teaching("Remember that API calls should always include auth headers")

        assert result.is_teaching is True
        assert result.confidence >= 0.9
        assert result.teaching_type == "explicit_instruction"
        assert "API calls" in result.extracted_knowledge or "auth headers" in result.extracted_knowledge

    def test_detect_always_do_pattern(self):
        """Should detect 'always do X' as standing rule."""
        from knowledge_detector import detect_teaching

        result = detect_teaching("Always use TypeScript for new modules")

        assert result.is_teaching is True
        assert result.confidence >= 0.85
        assert result.teaching_type == "standing_rule"
        assert "TypeScript" in result.extracted_knowledge

    def test_detect_never_do_pattern(self):
        """Should detect 'never do X' as prohibition."""
        from knowledge_detector import detect_teaching

        result = detect_teaching("Never commit secrets to the repository")

        assert result.is_teaching is True
        assert result.confidence >= 0.85
        assert result.teaching_type == "prohibition"
        assert "secrets" in result.extracted_knowledge or "repository" in result.extracted_knowledge

    def test_detect_prefer_pattern(self):
        """Should detect 'I prefer X over Y' as preference."""
        from knowledge_detector import detect_teaching

        result = detect_teaching("I prefer functional components over class components")

        assert result.is_teaching is True
        assert result.confidence >= 0.80
        assert result.teaching_type == "preference"
        assert "functional" in result.extracted_knowledge

    def test_detect_for_future_reference(self):
        """Should detect 'for future reference' as memory request."""
        from knowledge_detector import detect_teaching

        result = detect_teaching("For future reference, the deploy key is in 1Password")

        assert result.is_teaching is True
        assert result.confidence >= 0.85
        assert result.teaching_type == "memory_request"

    def test_no_teaching_in_normal_message(self):
        """Should NOT detect teaching in normal conversation."""
        from knowledge_detector import detect_teaching

        result = detect_teaching("Can you help me fix this bug?")

        assert result.is_teaching is False
        assert result.confidence < 0.5

    def test_detect_the_pattern_is(self):
        """Should detect 'the pattern is...' as pattern teaching."""
        from knowledge_detector import detect_teaching

        result = detect_teaching("The pattern here is to use dependency injection for testing")

        assert result.is_teaching is True
        assert result.teaching_type == "pattern_teaching"

    def test_detect_like_when_you(self):
        """Should detect 'I like when you...' as preference."""
        from knowledge_detector import detect_teaching

        result = detect_teaching("I like it when you explain your reasoning step by step")

        assert result.is_teaching is True
        assert result.teaching_type == "preference"


class TestResponseKnowledgeSynthesis:
    """Test detection of knowledge synthesis in Claude responses."""

    def test_detect_key_insight_in_response(self):
        """Should detect 'key insight:' in response."""
        from knowledge_detector import detect_response_knowledge

        response = """
        After investigating, here's what I found:

        Key insight: The connection pool exhaustion happens because
        Lambda doesn't reuse connections across cold starts.
        """

        result = detect_response_knowledge(response)

        assert result.has_knowledge is True
        assert result.confidence >= 0.75
        assert "connection pool" in result.extracted_knowledge.lower() or "Lambda" in result.extracted_knowledge

    def test_detect_insight_block_format(self):
        """Should detect ★ Insight blocks."""
        from knowledge_detector import detect_response_knowledge

        response = """
        `★ Insight ─────────────────────────────────────`
        The real issue is that MCP servers cache their state
        and don't refresh when the config changes.
        `─────────────────────────────────────────────────`
        """

        result = detect_response_knowledge(response)

        assert result.has_knowledge is True
        assert result.confidence >= 0.80

    def test_detect_important_note_in_response(self):
        """Should detect 'IMPORTANT:' or 'NOTE:' patterns."""
        from knowledge_detector import detect_response_knowledge

        response = """
        The fix is straightforward:

        IMPORTANT: This only works if you restart the service after config changes.
        """

        result = detect_response_knowledge(response)

        assert result.has_knowledge is True
        assert "restart" in result.extracted_knowledge.lower() or "service" in result.extracted_knowledge.lower()

    def test_no_knowledge_in_simple_response(self):
        """Should NOT detect knowledge in simple responses."""
        from knowledge_detector import detect_response_knowledge

        response = "Done! I've updated the file as requested."

        result = detect_response_knowledge(response)

        assert result.has_knowledge is False


class TestUnifiedKnowledgeDetection:
    """Test the unified detect_knowledge function."""

    def test_correction_still_detected(self):
        """Corrections should still be detected in unified function."""
        from knowledge_detector import detect_knowledge

        result = detect_knowledge(
            user_message="No, that's wrong. I meant to use POST not GET",
            assistant_response=""
        )

        assert result.is_correction is True
        assert result.correction_confidence >= 0.7

    def test_teaching_detected_separately(self):
        """Teaching should be detected separately from corrections."""
        from knowledge_detector import detect_knowledge

        result = detect_knowledge(
            user_message="Remember that we always use snake_case for database columns",
            assistant_response=""
        )

        assert result.is_teaching is True
        assert result.teaching_confidence >= 0.9
        assert result.is_correction is False

    def test_combined_knowledge_result(self):
        """Should combine all knowledge signals."""
        from knowledge_detector import detect_knowledge

        result = detect_knowledge(
            user_message="Actually, I prefer tabs over spaces",
            assistant_response="Key insight: The formatter config needs to be updated."
        )

        # User message has teaching (preference)
        # Response has knowledge synthesis
        assert result.is_teaching is True or result.has_response_knowledge is True
        assert result.total_confidence > 0

    def test_knowledge_result_to_dict(self):
        """KnowledgeResult should be serializable."""
        from knowledge_detector import detect_knowledge

        result = detect_knowledge(
            user_message="Remember that X",
            assistant_response=""
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert 'is_teaching' in result_dict
        assert 'is_correction' in result_dict


class TestClassificationPrompt:
    """Test classification prompt generation."""

    def test_generate_classification_options(self):
        """Should generate proper classification options."""
        from knowledge_detector import generate_classification_prompt, detect_knowledge

        result = detect_knowledge(
            user_message="Remember that our API uses JWT tokens",
            assistant_response=""
        )

        prompt = generate_classification_prompt(result)

        assert 'questions' in prompt
        assert len(prompt['questions']) > 0
        assert 'options' in prompt['questions'][0]

        # Should have user-level, project-level, skip options
        labels = [opt['label'] for opt in prompt['questions'][0]['options']]
        assert any('user' in label.lower() for label in labels)
        assert any('project' in label.lower() for label in labels)

    def test_user_project_default_heuristics(self):
        """Should provide heuristic defaults for classification."""
        from knowledge_detector import suggest_classification, detect_knowledge

        # Tool-related should suggest user-level
        result1 = detect_knowledge(
            user_message="Remember that Docker needs to restart after config changes",
            assistant_response=""
        )
        suggestion1 = suggest_classification(result1)
        assert suggestion1 in ['user', 'project', 'skip']

        # Project-specific path should suggest project-level
        result2 = detect_knowledge(
            user_message="Remember that /src/config uses JSON format",
            assistant_response=""
        )
        suggestion2 = suggest_classification(result2)
        assert suggestion2 in ['user', 'project', 'skip']


class TestIntegrationWithExistingCorrection:
    """Test that existing correction detection still works."""

    def test_correction_detector_patterns_preserved(self):
        """All existing correction patterns should still work."""
        from knowledge_detector import detect_knowledge

        correction_phrases = [
            "No, that's wrong",
            "Actually, I meant something else",
            "You misunderstood, I wanted X",
            "Wrong, it should be Y",
            "That's incorrect"
        ]

        for phrase in correction_phrases:
            result = detect_knowledge(user_message=phrase, assistant_response="")
            assert result.is_correction is True, f"Failed to detect correction in: {phrase}"

    def test_typo_tolerance_preserved(self):
        """Typo tolerance from correction_detector should be preserved."""
        from knowledge_detector import detect_knowledge

        result = detect_knowledge(
            user_message="thats worng, I meant X",  # typos
            assistant_response=""
        )

        assert result.is_correction is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
