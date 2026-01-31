"""ChromaDB vector store implementation."""

import logging
from typing import Any

import chromadb

from .s3vectors import VectorMetadata


logger = logging.getLogger(__name__)


class ChromaDBStore:
    """Local vector store using ChromaDB with persistent storage.

    Uses ChromaDB's PersistentClient for file-based storage.
    Implements the VectorStore protocol.
    """

    def __init__(
        self,
        persist_dir: str = "~/.chroma-data",
        collection_name: str = "zettelkasten",
    ) -> None:
        """Initialize ChromaDB store with persistent storage."""
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def put_vector(
        self,
        key: str,
        embedding: list[float],
        metadata: VectorMetadata,
    ) -> bool:
        """Store a vector with metadata."""
        try:
            self.collection.upsert(
                ids=[key],
                embeddings=[embedding],
                metadatas=[metadata.to_dict()],
            )
        except chromadb.errors.ChromaError:
            logger.exception("Failed to put vector %s", key)
            return False
        else:
            return True

    def batch_put_vectors(
        self,
        vectors: list[tuple[str, list[float], VectorMetadata]],
    ) -> bool:
        """Store multiple vectors in one operation."""
        try:
            ids = [v[0] for v in vectors]
            embeddings = [v[1] for v in vectors]
            metadatas = [v[2].to_dict() for v in vectors]
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except chromadb.errors.ChromaError:
            logger.exception("Failed to batch put vectors")
            return False
        else:
            return True

    def query(
        self,
        embedding: list[float],
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict]:
        """Query for similar vectors."""
        kwargs: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": top_k,
        }
        if metadata_filter:
            kwargs["where"] = {k: {"$eq": v} for k, v in metadata_filter.items()}

        result = self.collection.query(**kwargs)

        vectors = []
        for i, key in enumerate(result["ids"][0]):
            vectors.append(
                {
                    "key": key,
                    "distance": result["distances"][0][i]
                    if result.get("distances")
                    else None,
                    "metadata": result["metadatas"][0][i]
                    if result.get("metadatas")
                    else {},
                }
            )
        return vectors

    def get_vector(self, key: str) -> dict | None:
        """Get a vector by key."""
        try:
            result = self.collection.get(
                ids=[key],
                include=["embeddings", "metadatas"],
            )
            if not result["ids"]:
                return None
            return {
                "key": result["ids"][0],
                "metadata": result["metadatas"][0] if result.get("metadatas") else {},
                "data": {"float32": list(result["embeddings"][0])}
                if result.get("embeddings") is not None
                and len(result["embeddings"]) > 0
                else None,
            }
        except chromadb.errors.ChromaError:
            logger.exception("Failed to get vector %s", key)
            return None

    def update_metadata(self, key: str, metadata: VectorMetadata) -> bool:
        """Update metadata for a vector."""
        try:
            self.collection.update(ids=[key], metadatas=[metadata.to_dict()])
        except chromadb.errors.ChromaError:
            logger.exception("Failed to update metadata for %s", key)
            return False
        else:
            return True

    def delete_vector(self, key: str) -> bool:
        """Delete a vector by key."""
        try:
            self.collection.delete(ids=[key])
        except chromadb.errors.ChromaError:
            logger.exception("Failed to delete vector %s", key)
            return False
        else:
            return True

    def query_all(
        self,
        metadata_filter: dict[str, Any] | None = None,
        include_embeddings: bool = False,
    ) -> list[dict]:
        """Query all vectors matching a filter."""
        includes: list[str] = ["metadatas"]
        if include_embeddings:
            includes.append("embeddings")

        kwargs: dict[str, Any] = {"include": includes}
        if metadata_filter:
            kwargs["where"] = {k: {"$eq": v} for k, v in metadata_filter.items()}

        result = self.collection.get(**kwargs)

        vectors = []
        for i, key in enumerate(result["ids"]):
            entry: dict[str, Any] = {
                "key": key,
                "metadata": result["metadatas"][i] if result.get("metadatas") else {},
            }
            if include_embeddings and result.get("embeddings") is not None:
                entry["embedding"] = list(result["embeddings"][i])
            vectors.append(entry)
        return vectors
