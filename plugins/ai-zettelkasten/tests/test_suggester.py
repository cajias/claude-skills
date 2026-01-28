"""Tests for proactive suggestion detection."""
import pytest
from ai_zettelkasten.suggester import Suggester, Suggestion
from ai_zettelkasten.obsidian import KnowledgeType


class TestSuggester:
    def test_detect_fact_from_comment(self):
        """Detect facts from NOTE: or IMPORTANT: comments."""
        suggester = Suggester()
        content = '''
        # NOTE: S3 Vectors has a 50 metadata key limit per vector
        METADATA_LIMIT = 50
        '''
        suggestions = suggester.analyze("config.py", content)
        assert len(suggestions) >= 1
        assert suggestions[0].knowledge_type == KnowledgeType.FACT
        assert "50" in suggestions[0].content or "metadata" in suggestions[0].content.lower()

    def test_detect_decision_from_chose(self):
        """Detect decisions from chose/decided/selected keywords."""
        suggester = Suggester()
        content = '''
        # We chose uvx over pip because it provides better dependency isolation
        PACKAGE_MANAGER = "uvx"
        '''
        suggestions = suggester.analyze("setup.py", content)
        assert len(suggestions) >= 1
        assert suggestions[0].knowledge_type == KnowledgeType.DECISION

    def test_detect_pattern_from_always(self):
        """Detect patterns from always/never/pattern keywords."""
        suggester = Suggester()
        content = '''
        # Always validate input before processing - prevents injection attacks
        def process(input: str):
            validate(input)
        '''
        suggestions = suggester.analyze("utils.py", content)
        assert len(suggestions) >= 1
        assert suggestions[0].knowledge_type == KnowledgeType.PATTERN

    def test_detect_correction_from_fixed(self):
        """Detect corrections from fixed/was wrong/actually keywords."""
        suggester = Suggester()
        content = '''
        # Fixed: was using 1024 dimensions but Titan actually uses 1536
        TITAN_DIMENSIONS = 1536
        '''
        suggestions = suggester.analyze("embeddings.py", content)
        assert len(suggestions) >= 1
        assert suggestions[0].knowledge_type == KnowledgeType.CORRECTION

    def test_extract_tags_from_content(self):
        """Extract relevant tags from suggestion content."""
        suggester = Suggester()
        content = '''
        # NOTE: AWS Lambda cold start times increase with package size
        '''
        suggestions = suggester.analyze("lambda.py", content)
        assert len(suggestions) >= 1
        tags = suggestions[0].tags
        assert any(t in tags for t in ["aws", "lambda"])

    def test_no_suggestions_for_plain_code(self):
        """Return empty list for code without extractable knowledge."""
        suggester = Suggester()
        content = '''
        def add(a, b):
            return a + b
        '''
        suggestions = suggester.analyze("math.py", content)
        assert len(suggestions) == 0

    def test_format_suggestion(self):
        """Format suggestion for CLI output."""
        suggester = Suggester()
        suggestion = Suggestion(
            content="S3 Vectors has 50 metadata key limit",
            knowledge_type=KnowledgeType.FACT,
            tags=["aws", "s3-vectors"],
            confidence=0.85,
            source_line=5
        )
        formatted = suggester.format_suggestion(suggestion)
        assert "Worth capturing" in formatted
        assert "fact" in formatted.lower()
        assert "[y]" in formatted

    def test_confidence_scoring(self):
        """Higher confidence for explicit markers like NOTE:."""
        suggester = Suggester()
        explicit = "# NOTE: This is important"
        implicit = "# This might be useful"

        s1 = suggester.analyze("a.py", explicit)
        s2 = suggester.analyze("b.py", implicit)

        if s1 and s2:
            assert s1[0].confidence > s2[0].confidence
