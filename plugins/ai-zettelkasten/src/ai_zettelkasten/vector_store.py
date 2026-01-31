"""Protocol definitions for vector store and embeddings backends."""

from typing import Any, Protocol, runtime_checkable

from .s3vectors import VectorMetadata


@runtime_checkable
class VectorStore(Protocol):
    """Protocol that all vector store backends must implement."""

    def put_vector(
        self,
        key: str,
        embedding: list[float],
        metadata: VectorMetadata,
    ) -> bool:
        """Store a vector with metadata."""
        ...

    def batch_put_vectors(
        self,
        vectors: list[tuple[str, list[float], VectorMetadata]],
    ) -> bool:
        """Store multiple vectors in one operation."""
        ...

    def query(
        self,
        embedding: list[float],
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict]:
        """Query for similar vectors."""
        ...

    def get_vector(self, key: str) -> dict | None:
        """Get a vector by key."""
        ...

    def update_metadata(self, key: str, metadata: VectorMetadata) -> bool:
        """Update metadata for a vector."""
        ...

    def delete_vector(self, key: str) -> bool:
        """Delete a vector by key."""
        ...

    def query_all(
        self,
        metadata_filter: dict[str, Any] | None = None,
        include_embeddings: bool = False,
    ) -> list[dict]:
        """Query all vectors matching a filter."""
        ...


@runtime_checkable
class Embeddings(Protocol):
    """Protocol that all embedding providers must implement."""

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        ...

    def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        ...
