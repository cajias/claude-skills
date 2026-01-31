"""Knowledge extraction service - orchestrates note creation and storage."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .obsidian import ObsidianVault, Note, KnowledgeType
from .embeddings import BedrockEmbeddings
from .s3vectors import S3VectorsStore, VectorMetadata


@dataclass
class ExtractionItem:
    """A single knowledge item to extract.

    Represents knowledge extracted from a Claude Code session that needs
    to be converted into a Zettelkasten note and stored for semantic search.

    Attributes:
        knowledge_type: Category of knowledge (fact, decision, pattern, correction)
        title: Short descriptive title for the note
        content: Full content/body of the knowledge item
        tags: List of tags for categorization
        confidence: Confidence score (0-1) for this extraction
        source_session: Optional ID of the Claude session that produced this
    """

    knowledge_type: KnowledgeType
    title: str
    content: str
    tags: list[str]
    confidence: float
    source_session: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "ExtractionItem":
        """Create from dictionary (JSON input).

        Args:
            d: Dictionary with extraction item data

        Returns:
            ExtractionItem instance

        Example:
            >>> item = ExtractionItem.from_dict({
            ...     "type": "fact",
            ...     "title": "Lambda timeout",
            ...     "content": "Default timeout is 3 seconds",
            ...     "tags": ["aws", "lambda"],
            ...     "confidence": 0.9
            ... })
        """
        type_str = d.get("type", "fact")
        return cls(
            knowledge_type=KnowledgeType(type_str),
            title=d.get("title", "Untitled"),
            content=d.get("content", ""),
            tags=d.get("tags", []),
            confidence=d.get("confidence", 0.8),
            source_session=d.get("source_session"),
        )


class KnowledgeExtractor:
    """Orchestrates knowledge extraction, storage, and retrieval.

    This is the main service that coordinates the flow of knowledge from
    Claude Code sessions into the Zettelkasten system:

    1. Creates notes in Obsidian vault
    2. Generates embeddings via Bedrock Titan
    3. Stores vectors in S3 Vectors for semantic search
    4. Provides semantic search to find related notes

    Usage:
        extractor = KnowledgeExtractor(
            vault_path=Path("~/obsidian-vault"),
            bucket="my-vectors-bucket",
            index="notes-index"
        )

        # Process a single item
        result = extractor.process_item(item)

        # Process batch from JSON
        summary = extractor.process_items([
            {"type": "fact", "title": "...", "content": "...", ...},
            {"type": "decision", "title": "...", "content": "...", ...},
        ])

        # Find related notes
        related = extractor.find_related("AWS Lambda cold starts")
    """

    def __init__(
        self, vault_path: Path, bucket: str, index: str, region: Optional[str] = None
    ):
        """Initialize the knowledge extractor.

        Args:
            vault_path: Path to the Obsidian vault root
            bucket: S3 Vectors bucket name
            index: S3 Vectors index name
            region: AWS region (defaults to us-east-1)
        """
        self.vault = ObsidianVault(vault_path)
        self.embeddings = BedrockEmbeddings(region)
        self.vectors = S3VectorsStore(bucket, index, region)

    def process_item(self, item: ExtractionItem) -> dict[str, Any]:
        """Process a single extraction item.

        Performs the full pipeline:
        1. Create Note object
        2. Write to Obsidian vault
        3. Generate embedding
        4. Store in S3 Vectors

        Args:
            item: The extraction item to process

        Returns:
            Dictionary with processing result:
            - title: Item title
            - type: Knowledge type
            - status: "stored", "partial", or "error"
            - obsidian_path: Path to created note (if successful)
            - vector_key: Vector key in S3 Vectors (if stored)
            - error: Error message (if any)
        """
        result = {
            "title": item.title,
            "type": item.knowledge_type.value,
            "status": "pending",
        }

        # Create note
        note = Note(
            title=item.title,
            content=item.content,
            knowledge_type=item.knowledge_type,
            tags=item.tags,
            confidence=item.confidence,
            source_session=item.source_session,
        )

        # Write to Obsidian
        try:
            path = self.vault.write_note(note)
            result["obsidian_path"] = str(path)
        except Exception as e:
            result["status"] = "error"
            result["error"] = f"Obsidian write failed: {e}"
            return result

        # Generate embedding
        try:
            text = f"{note.title}\n\n{note.content}"
            embedding = self.embeddings.embed(text)
        except Exception as e:
            result["status"] = "partial"
            result["error"] = f"Embedding failed: {e}"
            return result

        # Store in S3 Vectors
        try:
            metadata = VectorMetadata(
                note_type=note.note_type.value,
                knowledge_type=note.knowledge_type.value,
                status=note.status,
                title=note.title,
                tags=note.tags,
                obsidian_path=str(path),
                content_preview=note.content[:500],
            )

            success = self.vectors.put_vector(note.id, embedding, metadata)
            if success:
                result["status"] = "stored"
                result["vector_key"] = note.id
            else:
                result["status"] = "partial"
                result["error"] = "Vector storage failed"
        except Exception as e:
            result["status"] = "partial"
            result["error"] = f"Vector storage failed: {e}"

        return result

    def process_items(self, items: list[dict]) -> dict[str, Any]:
        """Process multiple extraction items.

        Args:
            items: List of dictionaries representing extraction items

        Returns:
            Summary dictionary with:
            - total: Total number of items processed
            - stored: Number successfully stored
            - partial: Number with partial success
            - errors: Number with errors
            - results: List of individual results
        """
        results = []
        for item_dict in items:
            item = ExtractionItem.from_dict(item_dict)
            result = self.process_item(item)
            results.append(result)

        return {
            "total": len(items),
            "stored": len([r for r in results if r["status"] == "stored"]),
            "partial": len([r for r in results if r["status"] == "partial"]),
            "errors": len([r for r in results if r["status"] == "error"]),
            "results": results,
        }

    def find_related(
        self, query: str, top_k: int = 5, threshold: float = 0.75
    ) -> list[dict]:
        """Find notes related to a query.

        Uses semantic search to find notes similar to the query text.

        Args:
            query: Natural language query
            top_k: Maximum number of results to return
            threshold: Similarity threshold (0-1). Higher = more similar.
                       Results with similarity below threshold are filtered out.

        Returns:
            List of matching vectors with metadata and distance scores.
            Distance is inverse of similarity (lower = more similar).
        """
        embedding = self.embeddings.embed(query)
        results = self.vectors.query(embedding, top_k=top_k)

        # Filter by similarity threshold (distance < 1-threshold)
        filtered = [r for r in results if r.get("distance", 1.0) < (1 - threshold)]

        return filtered
