"""Tests for ChromaDB vector store implementation."""

from unittest.mock import MagicMock, patch

import chromadb

from ai_zettelkasten.s3vectors import VectorMetadata


def _make_metadata(**kwargs):
    defaults = dict(
        note_type="fleeting",
        knowledge_type="fact",
        status="pending",
        title="Test",
        tags=["test"],
        obsidian_path="fleeting/test.md",
    )
    defaults.update(kwargs)
    return VectorMetadata(**defaults)


class TestChromaDBStore:
    def _make_store(self, mock_collection=None):
        with patch("ai_zettelkasten.chromadb_store.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_coll = mock_collection or MagicMock()
            mock_client.get_or_create_collection.return_value = mock_coll
            mock_chromadb.PersistentClient.return_value = mock_client

            from ai_zettelkasten.chromadb_store import ChromaDBStore

            store = ChromaDBStore(persist_dir="/tmp/test-chroma")
            return store, mock_coll

    def test_initialization(self):
        store, _ = self._make_store()
        assert store is not None

    def test_put_vector(self):
        store, mock_coll = self._make_store()
        meta = _make_metadata()
        result = store.put_vector("key-1", [0.1] * 384, meta)
        assert result is True
        mock_coll.upsert.assert_called_once()
        kwargs = mock_coll.upsert.call_args.kwargs
        assert kwargs["ids"] == ["key-1"]
        assert kwargs["embeddings"] == [[0.1] * 384]

    def test_put_vector_returns_false_on_error(self):
        store, mock_coll = self._make_store()
        mock_coll.upsert.side_effect = chromadb.errors.ChromaError("fail")
        result = store.put_vector("key-1", [0.1] * 384, _make_metadata())
        assert result is False

    def test_batch_put_vectors(self):
        store, mock_coll = self._make_store()
        vectors = [
            ("k1", [0.1] * 384, _make_metadata(title="Note 1")),
            ("k2", [0.2] * 384, _make_metadata(title="Note 2")),
        ]
        result = store.batch_put_vectors(vectors)
        assert result is True
        kwargs = mock_coll.upsert.call_args.kwargs
        assert len(kwargs["ids"]) == 2

    def test_query(self):
        mock_coll = MagicMock()
        mock_coll.query.return_value = {
            "ids": [["k1", "k2"]],
            "distances": [[0.1, 0.3]],
            "metadatas": [[{"title": "N1"}, {"title": "N2"}]],
        }
        store, _ = self._make_store(mock_coll)
        results = store.query([0.1] * 384, top_k=5)
        assert len(results) == 2
        assert results[0]["key"] == "k1"
        assert results[0]["distance"] == 0.1

    def test_query_with_filter(self):
        mock_coll = MagicMock()
        mock_coll.query.return_value = {
            "ids": [[]],
            "distances": [[]],
            "metadatas": [[]],
        }
        store, _ = self._make_store(mock_coll)
        store.query([0.1] * 384, metadata_filter={"status": "approved"})
        kwargs = mock_coll.query.call_args.kwargs
        assert kwargs["where"] == {"status": {"$eq": "approved"}}

    def test_get_vector(self):
        mock_coll = MagicMock()
        mock_coll.get.return_value = {
            "ids": ["k1"],
            "embeddings": [[0.1] * 384],
            "metadatas": [{"title": "Test"}],
        }
        store, _ = self._make_store(mock_coll)
        result = store.get_vector("k1")
        assert result is not None
        assert result["key"] == "k1"

    def test_get_vector_not_found(self):
        mock_coll = MagicMock()
        mock_coll.get.return_value = {"ids": [], "embeddings": [], "metadatas": []}
        store, _ = self._make_store(mock_coll)
        result = store.get_vector("missing")
        assert result is None

    def test_update_metadata(self):
        store, mock_coll = self._make_store()
        meta = _make_metadata(status="approved")
        result = store.update_metadata("k1", meta)
        assert result is True
        mock_coll.update.assert_called_once()

    def test_delete_vector(self):
        store, mock_coll = self._make_store()
        result = store.delete_vector("k1")
        assert result is True
        mock_coll.delete.assert_called_once_with(ids=["k1"])

    def test_query_all(self):
        mock_coll = MagicMock()
        mock_coll.get.return_value = {
            "ids": ["k1", "k2"],
            "metadatas": [
                {"title": "N1", "status": "approved"},
                {"title": "N2", "status": "approved"},
            ],
            "embeddings": None,
        }
        store, _ = self._make_store(mock_coll)
        results = store.query_all(metadata_filter={"status": "approved"})
        assert len(results) == 2

    def test_query_all_with_embeddings(self):
        mock_coll = MagicMock()
        mock_coll.get.return_value = {
            "ids": ["k1"],
            "metadatas": [{"title": "N1"}],
            "embeddings": [[0.1] * 384],
        }
        store, _ = self._make_store(mock_coll)
        results = store.query_all(include_embeddings=True)
        assert len(results) == 1
        assert "embedding" in results[0]
