"""Tests for Ollama embeddings provider."""

from unittest.mock import MagicMock, patch

from ai_zettelkasten.ollama_embeddings import OllamaEmbeddings


class TestOllamaEmbeddings:
    def test_initialization_defaults(self):
        embeddings = OllamaEmbeddings()
        assert embeddings.model_name == "nomic-embed-text"
        assert embeddings.dimensions == 768

    def test_custom_model_and_dimensions(self):
        embeddings = OllamaEmbeddings(model_name="mxbai-embed-large", dimensions=1024)
        assert embeddings.model_name == "mxbai-embed-large"
        assert embeddings.dimensions == 1024

    def test_embed_calls_ollama(self):
        with patch("ai_zettelkasten.ollama_embeddings.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embedding": [0.1] * 768}
            mock_response.raise_for_status = MagicMock()
            mock_httpx.post.return_value = mock_response

            embeddings = OllamaEmbeddings()
            result = embeddings.embed("test text")

            assert len(result) == 768
            mock_httpx.post.assert_called_once()
            call_kwargs = mock_httpx.post.call_args
            assert "nomic-embed-text" in str(call_kwargs)

    def test_embed_batch(self):
        with patch("ai_zettelkasten.ollama_embeddings.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embedding": [0.1] * 768}
            mock_response.raise_for_status = MagicMock()
            mock_httpx.post.return_value = mock_response

            embeddings = OllamaEmbeddings()
            results = embeddings.embed_batch(["a", "b", "c"])

            assert len(results) == 3
            assert mock_httpx.post.call_count == 3

    def test_custom_base_url(self):
        embeddings = OllamaEmbeddings(base_url="http://remote:11434")
        assert embeddings.base_url == "http://remote:11434"
