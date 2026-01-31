"""Tests for Bedrock Titan embeddings."""

from unittest.mock import MagicMock, patch
import json

from ai_zettelkasten.embeddings import BedrockEmbeddings, TITAN_DIMENSIONS

PATCH_SESSION = "ai_zettelkasten.embeddings._get_assumed_role_session"


def _mock_session(mock_client):
    """Create a mock boto3 Session that returns the given client."""
    mock_sess = MagicMock()
    mock_sess.client.return_value = mock_client
    return mock_sess


class TestBedrockEmbeddings:
    def test_initialization(self):
        with patch(PATCH_SESSION) as mock_get_session:
            mock_get_session.return_value = _mock_session(MagicMock())
            embeddings = BedrockEmbeddings()
            assert embeddings.model_id == "amazon.titan-embed-text-v1"
            assert embeddings.dimensions == TITAN_DIMENSIONS

    def test_embed_text_returns_correct_dimensions(self):
        mock_response = {
            "body": MagicMock(
                read=MagicMock(
                    return_value=json.dumps(
                        {"embedding": [0.1] * TITAN_DIMENSIONS}
                    ).encode()
                )
            )
        }
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = mock_response
        with patch(PATCH_SESSION) as mock_get_session:
            mock_get_session.return_value = _mock_session(mock_client)

            embeddings = BedrockEmbeddings()
            result = embeddings.embed("Test text")

            assert len(result) == TITAN_DIMENSIONS
            assert all(isinstance(x, float) for x in result)

    def test_embed_truncates_long_text(self):
        long_text = "x" * 10000  # Longer than max

        mock_response = {
            "body": MagicMock(
                read=MagicMock(
                    return_value=json.dumps(
                        {"embedding": [0.1] * TITAN_DIMENSIONS}
                    ).encode()
                )
            )
        }
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = mock_response
        with patch(PATCH_SESSION) as mock_get_session:
            mock_get_session.return_value = _mock_session(mock_client)

            embeddings = BedrockEmbeddings()
            embeddings.embed(long_text)

            # Verify text was truncated in the call
            call_args = mock_client.invoke_model.call_args
            body = json.loads(call_args.kwargs["body"])
            assert len(body["inputText"]) <= 8000

    def test_embed_batch(self):
        mock_response = {
            "body": MagicMock(
                read=MagicMock(
                    return_value=json.dumps(
                        {"embedding": [0.1] * TITAN_DIMENSIONS}
                    ).encode()
                )
            )
        }
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = mock_response
        with patch(PATCH_SESSION) as mock_get_session:
            mock_get_session.return_value = _mock_session(mock_client)

            embeddings = BedrockEmbeddings()
            results = embeddings.embed_batch(["Text 1", "Text 2", "Text 3"])

            assert len(results) == 3
            assert all(len(r) == TITAN_DIMENSIONS for r in results)
