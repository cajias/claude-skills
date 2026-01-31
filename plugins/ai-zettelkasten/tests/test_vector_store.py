"""Tests for VectorStore and Embeddings protocols."""

from ai_zettelkasten.vector_store import Embeddings, VectorStore


class _ConformingStore:
    def put_vector(self, key, embedding, metadata):
        return True

    def batch_put_vectors(self, vectors):
        return True

    def query(self, embedding, top_k=10, metadata_filter=None):
        return []

    def get_vector(self, key):
        return None

    def update_metadata(self, key, metadata):
        return True

    def delete_vector(self, key):
        return True

    def query_all(self, metadata_filter=None, include_embeddings=False):
        return []


class _NonConformingStore:
    def put_vector(self, key):
        return True


class _ConformingEmbeddings:
    @property
    def dimensions(self):
        return 384

    def embed(self, text):
        return [0.0] * 384

    def embed_batch(self, texts):
        return [[0.0] * 384 for _ in texts]


class TestVectorStoreProtocol:
    def test_conforming_class_is_instance(self):
        assert isinstance(_ConformingStore(), VectorStore)

    def test_non_conforming_class_is_not_instance(self):
        assert not isinstance(_NonConformingStore(), VectorStore)


class TestEmbeddingsProtocol:
    def test_conforming_class_is_instance(self):
        assert isinstance(_ConformingEmbeddings(), Embeddings)

    def test_non_conforming_class_is_not_instance(self):
        assert not isinstance(object(), Embeddings)
