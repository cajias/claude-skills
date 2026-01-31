"""Integration tests for ChromaDB backend (no AWS credentials needed)."""

import pytest

from ai_zettelkasten.chromadb_store import ChromaDBStore
from ai_zettelkasten.s3vectors import VectorMetadata


@pytest.fixture
def store(tmp_path):
    return ChromaDBStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")


def _meta(**kwargs):
    defaults = dict(
        note_type="fleeting",
        knowledge_type="fact",
        status="pending",
        title="Test Note",
        tags=["test"],
        obsidian_path="fleeting/test.md",
    )
    defaults.update(kwargs)
    return VectorMetadata(**defaults)


class TestChromaDBIntegration:
    def test_put_and_get(self, store):
        embedding = [0.1] * 384
        assert store.put_vector("note-1", embedding, _meta())
        result = store.get_vector("note-1")
        assert result is not None
        assert result["key"] == "note-1"
        assert result["metadata"]["title"] == "Test Note"

    def test_put_and_query_similar(self, store):
        store.put_vector("note-1", [1.0] + [0.0] * 383, _meta(title="First"))
        store.put_vector("note-2", [0.9] + [0.1] + [0.0] * 382, _meta(title="Second"))
        store.put_vector("note-3", [0.0] * 383 + [1.0], _meta(title="Third"))

        results = store.query([1.0] + [0.0] * 383, top_k=2)
        assert len(results) == 2
        assert results[0]["key"] == "note-1"

    def test_query_with_filter(self, store):
        store.put_vector("n1", [0.1] * 384, _meta(status="approved"))
        store.put_vector("n2", [0.2] * 384, _meta(status="pending"))

        results = store.query([0.1] * 384, metadata_filter={"status": "approved"})
        assert len(results) == 1
        assert results[0]["key"] == "n1"

    def test_update_metadata(self, store):
        store.put_vector("n1", [0.1] * 384, _meta(status="pending"))
        assert store.update_metadata("n1", _meta(status="approved"))
        result = store.get_vector("n1")
        assert result["metadata"]["status"] == "approved"

    def test_delete_vector(self, store):
        store.put_vector("n1", [0.1] * 384, _meta())
        assert store.delete_vector("n1")
        assert store.get_vector("n1") is None

    def test_batch_put(self, store):
        vectors = [
            ("k1", [0.1] * 384, _meta(title="A")),
            ("k2", [0.2] * 384, _meta(title="B")),
            ("k3", [0.3] * 384, _meta(title="C")),
        ]
        assert store.batch_put_vectors(vectors)
        assert store.get_vector("k1") is not None
        assert store.get_vector("k3") is not None

    def test_query_all(self, store):
        store.put_vector("n1", [0.1] * 384, _meta(status="approved"))
        store.put_vector("n2", [0.2] * 384, _meta(status="approved"))
        store.put_vector("n3", [0.3] * 384, _meta(status="pending"))

        results = store.query_all(metadata_filter={"status": "approved"})
        assert len(results) == 2

    def test_query_all_with_embeddings(self, store):
        store.put_vector("n1", [0.5] * 384, _meta())
        results = store.query_all(include_embeddings=True)
        assert len(results) == 1
        assert "embedding" in results[0]
        assert len(results[0]["embedding"]) == 384

    def test_get_nonexistent_returns_none(self, store):
        assert store.get_vector("nonexistent") is None
