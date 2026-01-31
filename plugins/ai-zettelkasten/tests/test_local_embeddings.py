"""Tests for local sentence-transformers embeddings."""

import numpy as np
from unittest.mock import MagicMock, patch


class TestLocalEmbeddings:
    def _make_mock_model(self, dims=384):
        mock = MagicMock()
        mock.get_sentence_embedding_dimension.return_value = dims
        return mock

    def test_initialization_loads_model(self):
        mock_model = self._make_mock_model()
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            import ai_zettelkasten.local_embeddings as mod

            with patch(
                "sentence_transformers.SentenceTransformer", return_value=mock_model
            ):
                embeddings = mod.LocalEmbeddings()
                assert embeddings.dimensions == 384

    def test_embed_returns_list_of_floats(self):
        mock_model = self._make_mock_model()
        mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            import ai_zettelkasten.local_embeddings as mod

            with patch(
                "sentence_transformers.SentenceTransformer", return_value=mock_model
            ):
                embeddings = mod.LocalEmbeddings()
                result = embeddings.embed("test text")
                assert isinstance(result, list)
                assert len(result) == 384
                assert all(isinstance(x, float) for x in result)

    def test_embed_batch_returns_list_of_lists(self):
        mock_model = self._make_mock_model()
        mock_model.encode.return_value = np.random.rand(3, 384).astype(np.float32)
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            import ai_zettelkasten.local_embeddings as mod

            with patch(
                "sentence_transformers.SentenceTransformer", return_value=mock_model
            ):
                embeddings = mod.LocalEmbeddings()
                results = embeddings.embed_batch(["a", "b", "c"])
                assert len(results) == 3
                assert all(len(r) == 384 for r in results)

    def test_custom_model_name(self):
        mock_model = self._make_mock_model(768)
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            import ai_zettelkasten.local_embeddings as mod

            with patch(
                "sentence_transformers.SentenceTransformer", return_value=mock_model
            ) as mock_st:
                embeddings = mod.LocalEmbeddings(model_name="all-mpnet-base-v2")
                mock_st.assert_called_once_with("all-mpnet-base-v2")
                assert embeddings.dimensions == 768
