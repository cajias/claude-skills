"""Tests for backend configuration and factory."""

import os
from unittest.mock import patch, MagicMock

import pytest

from ai_zettelkasten.config import create_vector_store, create_embeddings


class TestCreateVectorStore:
    def test_default_is_chromadb(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("ai_zettelkasten.config.ChromaDBStore") as mock_cls:
                mock_cls.return_value = MagicMock()
                create_vector_store()
                mock_cls.assert_called_once()

    def test_chromadb_backend(self):
        with patch.dict(os.environ, {"ZETTELKASTEN_BACKEND": "chromadb"}):
            with patch("ai_zettelkasten.config.ChromaDBStore") as mock_cls:
                mock_cls.return_value = MagicMock()
                create_vector_store()
                mock_cls.assert_called_once()

    def test_s3_backend(self):
        with patch.dict(os.environ, {"ZETTELKASTEN_BACKEND": "s3"}):
            with patch("ai_zettelkasten.config.S3VectorsStore") as mock_cls:
                mock_cls.return_value = MagicMock()
                create_vector_store()
                mock_cls.assert_called_once()

    def test_invalid_backend_raises(self):
        with patch.dict(os.environ, {"ZETTELKASTEN_BACKEND": "invalid"}):
            with pytest.raises(ValueError, match="Unknown backend"):
                create_vector_store()


class TestCreateEmbeddings:
    def test_default_is_ollama(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("ai_zettelkasten.config.OllamaEmbeddings") as mock_cls:
                mock_cls.return_value = MagicMock()
                create_embeddings()
                mock_cls.assert_called_once()

    def test_ollama_provider(self):
        with patch.dict(os.environ, {"ZETTELKASTEN_EMBEDDINGS": "ollama"}):
            with patch("ai_zettelkasten.config.OllamaEmbeddings") as mock_cls:
                mock_cls.return_value = MagicMock()
                create_embeddings()
                mock_cls.assert_called_once()

    def test_bedrock_provider(self):
        with patch.dict(os.environ, {"ZETTELKASTEN_EMBEDDINGS": "bedrock"}):
            with patch("ai_zettelkasten.config.BedrockEmbeddings") as mock_cls:
                mock_cls.return_value = MagicMock()
                create_embeddings()
                mock_cls.assert_called_once()

    def test_local_provider(self):
        with patch.dict(os.environ, {"ZETTELKASTEN_EMBEDDINGS": "local"}):
            with patch("ai_zettelkasten.config.LocalEmbeddings") as mock_cls:
                mock_cls.return_value = MagicMock()
                create_embeddings()
                mock_cls.assert_called_once()

    def test_invalid_provider_raises(self):
        with patch.dict(os.environ, {"ZETTELKASTEN_EMBEDDINGS": "invalid"}):
            with pytest.raises(ValueError, match="Unknown embeddings"):
                create_embeddings()
