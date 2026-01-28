"""S3 Vectors storage for semantic search."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import boto3


@dataclass
class VectorMetadata:
    """Metadata stored with each vector.

    Attributes:
        note_type: Type of note (fleeting, permanent, hub)
        knowledge_type: Type of knowledge (fact, decision, pattern, correction)
        status: Current status (pending, approved, archived)
        title: Note title
        tags: List of tags
        obsidian_path: Path to the note in Obsidian vault
        content_preview: Preview of note content
        scope: Scope of the note (global, project)
        project: Project name if scope is project
        hub_ids: IDs of hubs this note belongs to
        link_count: Number of links in/out
        linked_ids: IDs of linked notes
        created: Creation timestamp
        promoted: Timestamp when note was promoted to permanent
    """
    note_type: str  # fleeting, permanent, hub
    knowledge_type: str  # fact, decision, pattern, correction
    status: str  # pending, approved, archived
    title: str
    tags: list[str]
    obsidian_path: str
    content_preview: str = ""
    scope: str = "global"
    project: str = ""
    hub_ids: list[str] = field(default_factory=list)
    link_count: int = 0
    linked_ids: list[str] = field(default_factory=list)
    created: Optional[str] = None
    promoted: Optional[str] = None

    def to_dict(self) -> dict[str, str]:
        """Convert to S3 Vectors metadata format (string values).

        S3 Vectors requires all metadata values to be strings.
        Lists are converted to comma-separated strings.
        """
        return {
            "note_type": self.note_type,
            "knowledge_type": self.knowledge_type,
            "status": self.status,
            "title": self.title[:200],  # Truncate for limits
            "content_preview": self.content_preview[:500],
            "tags": ",".join(self.tags),
            "obsidian_path": self.obsidian_path,
            "scope": self.scope,
            "project": self.project,
            "hub_ids": ",".join(self.hub_ids),
            "link_count": str(self.link_count),
            "linked_ids": ",".join(self.linked_ids),
            "created": self.created or datetime.now().isoformat(),
            "promoted": self.promoted or "",
        }

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> "VectorMetadata":
        """Parse from S3 Vectors metadata format.

        Handles missing keys gracefully with sensible defaults.
        """
        return cls(
            note_type=d.get("note_type", "fleeting"),
            knowledge_type=d.get("knowledge_type", "fact"),
            status=d.get("status", "pending"),
            title=d.get("title", ""),
            tags=d.get("tags", "").split(",") if d.get("tags") else [],
            obsidian_path=d.get("obsidian_path", ""),
            content_preview=d.get("content_preview", ""),
            scope=d.get("scope", "global"),
            project=d.get("project", ""),
            hub_ids=d.get("hub_ids", "").split(",") if d.get("hub_ids") else [],
            link_count=int(d.get("link_count", 0)),
            linked_ids=d.get("linked_ids", "").split(",") if d.get("linked_ids") else [],
            created=d.get("created"),
            promoted=d.get("promoted") or None,
        )


class S3VectorsStore:
    """Interface to S3 Vectors for semantic storage and search.

    S3 Vectors provides serverless vector storage optimized for
    similarity search workloads. This class wraps the boto3 client
    to provide a Zettelkasten-specific interface.

    Usage:
        store = S3VectorsStore("my-bucket", "notes-index")

        # Store a note embedding
        meta = VectorMetadata(
            note_type="fleeting",
            knowledge_type="fact",
            status="pending",
            title="AWS Lambda Tips",
            tags=["aws", "lambda"],
            obsidian_path="fleeting/lambda-tips.md"
        )
        store.put_vector("note-123", embedding, meta)

        # Query for similar notes
        results = store.query(query_embedding, top_k=10)
    """

    def __init__(self, bucket: str, index: str, region: Optional[str] = None):
        """Initialize the S3 Vectors store.

        Args:
            bucket: S3 Vectors bucket name
            index: Index name within the bucket
            region: AWS region (defaults to us-east-1)
        """
        self.bucket = bucket
        self.index = index
        self.client = boto3.client(
            "s3vectors",
            region_name=region or "us-east-1"
        )

    def put_vector(
        self,
        key: str,
        embedding: list[float],
        metadata: VectorMetadata
    ) -> bool:
        """Store a vector with metadata.

        Args:
            key: Unique identifier for the vector
            embedding: Vector embedding (e.g., 1536 dimensions for Titan)
            metadata: Metadata to store with the vector

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.put_vectors(
                vectorBucketName=self.bucket,
                indexName=self.index,
                vectors=[{
                    "key": key,
                    "data": {"float32": embedding},
                    "metadata": metadata.to_dict()
                }]
            )
            return True
        except Exception as e:
            print(f"Error storing vector: {e}")
            return False

    def batch_put_vectors(
        self,
        vectors: list[tuple[str, list[float], VectorMetadata]]
    ) -> bool:
        """Store multiple vectors in a single API call.

        Args:
            vectors: List of (key, embedding, metadata) tuples

        Returns:
            True if successful, False otherwise
        """
        try:
            vector_data = [
                {
                    "key": key,
                    "data": {"float32": embedding},
                    "metadata": metadata.to_dict()
                }
                for key, embedding, metadata in vectors
            ]
            self.client.put_vectors(
                vectorBucketName=self.bucket,
                indexName=self.index,
                vectors=vector_data
            )
            return True
        except Exception as e:
            print(f"Error storing vectors: {e}")
            return False

    def query(
        self,
        embedding: list[float],
        top_k: int = 10,
        filter: Optional[dict[str, Any]] = None
    ) -> list[dict]:
        """Query for similar vectors.

        Args:
            embedding: Query vector
            top_k: Number of results to return
            filter: Optional metadata filter (e.g., {"status": "approved"})

        Returns:
            List of matching vectors with metadata and distance scores
        """
        kwargs = {
            "vectorBucketName": self.bucket,
            "indexName": self.index,
            "topK": top_k,
            "queryVector": {"float32": embedding},
            "returnMetadata": True,
            "returnDistance": True,
        }

        if filter:
            # Convert simple filter to S3V format
            s3v_filter = {}
            for key, value in filter.items():
                s3v_filter[key] = {"$eq": value}
            kwargs["filter"] = s3v_filter

        response = self.client.query_vectors(**kwargs)
        return response.get("vectors", [])

    def get_vector(self, key: str) -> Optional[dict]:
        """Get a vector by key.

        Args:
            key: Vector key to retrieve

        Returns:
            Vector data with metadata, or None if not found
        """
        try:
            response = self.client.get_vectors(
                vectorBucketName=self.bucket,
                indexName=self.index,
                keys=[key]
            )
            vectors = response.get("vectors", [])
            return vectors[0] if vectors else None
        except Exception as e:
            print(f"Error getting vector: {e}")
            return None

    def update_metadata(self, key: str, metadata: VectorMetadata) -> bool:
        """Update metadata for an existing vector.

        Args:
            key: Vector key to update
            metadata: New metadata to apply

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.update_vector(
                vectorBucketName=self.bucket,
                indexName=self.index,
                key=key,
                metadata=metadata.to_dict()
            )
            return True
        except Exception as e:
            print(f"Error updating metadata: {e}")
            return False

    def delete_vector(self, key: str) -> bool:
        """Delete a vector by key.

        Args:
            key: Vector key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_vectors(
                vectorBucketName=self.bucket,
                indexName=self.index,
                keys=[key]
            )
            return True
        except Exception as e:
            print(f"Error deleting vector: {e}")
            return False

    def query_all(
        self,
        filter: Optional[dict[str, Any]] = None,
        include_embeddings: bool = False
    ) -> list[dict]:
        """Query all vectors matching the filter.

        Uses pagination to fetch all results. For clustering, set include_embeddings=True
        to get the vector data for similarity computation.

        Args:
            filter: Optional metadata filter (e.g., {"status": "approved"})
            include_embeddings: Whether to include vector embeddings in results

        Returns:
            List of all matching vectors with metadata
        """
        all_vectors = []
        next_token = None

        # Build filter in S3V format
        s3v_filter = None
        if filter:
            s3v_filter = {}
            for key, value in filter.items():
                s3v_filter[key] = {"$eq": value}

        while True:
            kwargs = {
                "vectorBucketName": self.bucket,
                "indexName": self.index,
                "returnMetadata": True,
            }

            if s3v_filter:
                kwargs["filter"] = s3v_filter
            if next_token:
                kwargs["nextToken"] = next_token

            try:
                if include_embeddings:
                    # Use list_vectors to get embeddings
                    response = self.client.list_vectors(**kwargs)
                    vectors = response.get("vectors", [])
                    # Convert data format
                    for v in vectors:
                        if "data" in v and "float32" in v["data"]:
                            v["embedding"] = v["data"]["float32"]
                else:
                    # Use list_vectors for metadata only
                    response = self.client.list_vectors(**kwargs)
                    vectors = response.get("vectors", [])

                all_vectors.extend(vectors)

                # Check for more pages
                next_token = response.get("nextToken")
                if not next_token:
                    break

            except Exception as e:
                print(f"Error in query_all: {e}")
                break

        return all_vectors
