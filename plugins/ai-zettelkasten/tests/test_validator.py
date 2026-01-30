"""Tests for the link validator module."""
import json
import pytest
from unittest.mock import MagicMock, patch

from ai_zettelkasten.validator import LinkValidator, ValidationResult, VALIDATION_PROMPT


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_creation(self):
        result = ValidationResult(
            should_link=True,
            relationship="ELABORATES",
            confidence=0.85,
            reason="These notes share the same concept"
        )
        assert result.should_link is True
        assert result.relationship == "ELABORATES"
        assert result.confidence == 0.85
        assert result.reason == "These notes share the same concept"

    def test_false_link(self):
        result = ValidationResult(
            should_link=False,
            relationship="UNKNOWN",
            confidence=0.0,
            reason="No meaningful connection"
        )
        assert result.should_link is False


class TestLinkValidator:
    """Tests for LinkValidator class."""

    @patch("ai_zettelkasten.validator.boto3")
    def test_initialization(self, mock_boto):
        mock_client = MagicMock()
        mock_boto.client.return_value = mock_client

        validator = LinkValidator(min_confidence=0.8, region="eu-west-1")

        assert validator.min_confidence == 0.8
        mock_boto.client.assert_called_once_with("bedrock-runtime", region_name="eu-west-1")

    @patch("ai_zettelkasten.validator.boto3")
    def test_validate_returns_valid_result(self, mock_boto):
        mock_client = MagicMock()
        mock_boto.client.return_value = mock_client

        # Mock successful LLM response
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "content": [{"text": json.dumps({
                "should_link": True,
                "relationship": "ELABORATES",
                "confidence": 0.85,
                "reason": "Source expands on target concept"
            })}]
        }).encode()
        mock_client.invoke_model.return_value = mock_response

        validator = LinkValidator(min_confidence=0.7)
        result = validator.validate(
            source_title="Test Source",
            source_content="Source content here",
            target_title="Test Target",
            target_content="Target content here"
        )

        assert result.should_link is True
        assert result.relationship == "ELABORATES"
        assert result.confidence == 0.85
        assert "expands" in result.reason

    @patch("ai_zettelkasten.validator.boto3")
    def test_validate_rejects_low_confidence(self, mock_boto):
        mock_client = MagicMock()
        mock_boto.client.return_value = mock_client

        # Mock response with low confidence
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "content": [{"text": json.dumps({
                "should_link": True,
                "relationship": "ELABORATES",
                "confidence": 0.5,  # Below threshold
                "reason": "Weak connection"
            })}]
        }).encode()
        mock_client.invoke_model.return_value = mock_response

        validator = LinkValidator(min_confidence=0.7)
        result = validator.validate(
            source_title="Test Source",
            source_content="Source content",
            target_title="Test Target",
            target_content="Target content"
        )

        assert result.should_link is False  # Rejected due to low confidence

    @patch("ai_zettelkasten.validator.boto3")
    def test_validate_handles_json_error(self, mock_boto):
        mock_client = MagicMock()
        mock_boto.client.return_value = mock_client

        # Mock invalid JSON response
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "content": [{"text": "This is not valid JSON"}]
        }).encode()
        mock_client.invoke_model.return_value = mock_response

        validator = LinkValidator()
        result = validator.validate(
            source_title="Test Source",
            source_content="Source content",
            target_title="Test Target",
            target_content="Target content"
        )

        assert result.should_link is False
        assert result.relationship == "UNKNOWN"
        assert "Invalid response format" in result.reason

    @patch("ai_zettelkasten.validator.boto3")
    def test_validate_handles_api_error(self, mock_boto):
        mock_client = MagicMock()
        mock_boto.client.return_value = mock_client

        # Mock API error
        mock_client.invoke_model.side_effect = Exception("API Error")

        validator = LinkValidator()
        result = validator.validate(
            source_title="Test Source",
            source_content="Source content",
            target_title="Test Target",
            target_content="Target content"
        )

        assert result.should_link is False
        assert result.relationship == "UNKNOWN"
        assert "Validation error" in result.reason

    @patch("ai_zettelkasten.validator.boto3")
    def test_validate_batch(self, mock_boto):
        mock_client = MagicMock()
        mock_boto.client.return_value = mock_client

        # Mock response for batch
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "content": [{"text": json.dumps({
                "should_link": True,
                "relationship": "SUPPORTS",
                "confidence": 0.9,
                "reason": "Strong support"
            })}]
        }).encode()
        mock_client.invoke_model.return_value = mock_response

        validator = LinkValidator()
        candidates = [
            {"title": "Candidate 1", "content": "Content 1"},
            {"title": "Candidate 2", "content": "Content 2"},
        ]

        results = validator.validate_batch(
            source_title="Source",
            source_content="Source content",
            candidates=candidates
        )

        assert len(results) == 2
        assert all(r[1].should_link for r in results)

    @patch("ai_zettelkasten.validator.boto3")
    def test_validate_strips_markdown_code_blocks(self, mock_boto):
        mock_client = MagicMock()
        mock_boto.client.return_value = mock_client

        # Mock response wrapped in markdown code block
        json_content = json.dumps({
            "should_link": True,
            "relationship": "APPLIES",
            "confidence": 0.88,
            "reason": "Applies the pattern"
        })
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "content": [{"text": f"```json\n{json_content}\n```"}]
        }).encode()
        mock_client.invoke_model.return_value = mock_response

        validator = LinkValidator()
        result = validator.validate(
            source_title="Test",
            source_content="Content",
            target_title="Target",
            target_content="Target content"
        )

        assert result.should_link is True
        assert result.relationship == "APPLIES"


class TestValidationPrompt:
    """Tests for the validation prompt template."""

    def test_prompt_contains_relationship_types(self):
        assert "SOLVES" in VALIDATION_PROMPT
        assert "ENABLES" in VALIDATION_PROMPT
        assert "ELABORATES" in VALIDATION_PROMPT
        assert "CONTRADICTS" in VALIDATION_PROMPT
        assert "SUPPORTS" in VALIDATION_PROMPT
        assert "APPLIES" in VALIDATION_PROMPT
        assert "ABSTRACTS" in VALIDATION_PROMPT
        assert "SEQUENCE" in VALIDATION_PROMPT

    def test_prompt_has_placeholders(self):
        assert "{source_title}" in VALIDATION_PROMPT
        assert "{source_content_preview}" in VALIDATION_PROMPT
        assert "{target_title}" in VALIDATION_PROMPT
        assert "{target_content_preview}" in VALIDATION_PROMPT

    def test_prompt_formatting(self):
        formatted = VALIDATION_PROMPT.format(
            source_title="Test Source",
            source_content_preview="Source content preview",
            target_title="Test Target",
            target_content_preview="Target content preview"
        )
        assert "Test Source" in formatted
        assert "Test Target" in formatted
