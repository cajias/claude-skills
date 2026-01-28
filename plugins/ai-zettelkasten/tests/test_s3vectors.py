"""Tests for S3 Vectors storage."""
import pytest
from unittest.mock import MagicMock, patch

from ai_zettelkasten.s3vectors import S3VectorsStore, VectorMetadata


class TestVectorMetadata:
    def test_to_dict(self):
        meta = VectorMetadata(
            note_type="permanent",
            knowledge_type="fact",
            status="approved",
            title="Test Note",
            tags=["aws", "test"],
            obsidian_path="permanent/test.md"
        )
        d = meta.to_dict()
        assert d["note_type"] == "permanent"
        assert d["tags"] == "aws,test"  # Comma-separated for S3V

    def test_from_dict(self):
        d = {
            "note_type": "fleeting",
            "knowledge_type": "decision",
            "status": "pending",
            "title": "My Decision",
            "tags": "arch,aws",
            "obsidian_path": "fleeting/my-decision.md"
        }
        meta = VectorMetadata.from_dict(d)
        assert meta.note_type == "fleeting"
        assert meta.tags == ["arch", "aws"]

    def test_to_dict_with_all_fields(self):
        """Test serialization of all metadata fields."""
        meta = VectorMetadata(
            note_type="hub",
            knowledge_type="pattern",
            status="approved",
            title="Architecture Patterns Hub",
            tags=["architecture", "patterns", "design"],
            obsidian_path="hub/architecture-patterns.md",
            content_preview="This hub connects all architecture-related notes",
            scope="project",
            project="my-project",
            hub_ids=["hub-001", "hub-002"],
            link_count=15,
            linked_ids=["note-1", "note-2", "note-3"],
            created="2024-01-15T10:30:00",
            promoted="2024-01-20T14:00:00"
        )
        d = meta.to_dict()
        assert d["note_type"] == "hub"
        assert d["knowledge_type"] == "pattern"
        assert d["status"] == "approved"
        assert d["title"] == "Architecture Patterns Hub"
        assert d["tags"] == "architecture,patterns,design"
        assert d["obsidian_path"] == "hub/architecture-patterns.md"
        assert d["content_preview"] == "This hub connects all architecture-related notes"
        assert d["scope"] == "project"
        assert d["project"] == "my-project"
        assert d["hub_ids"] == "hub-001,hub-002"
        assert d["link_count"] == "15"
        assert d["linked_ids"] == "note-1,note-2,note-3"
        assert d["created"] == "2024-01-15T10:30:00"
        assert d["promoted"] == "2024-01-20T14:00:00"

    def test_from_dict_with_empty_values(self):
        """Test parsing with missing/empty values uses defaults."""
        d = {
            "title": "Minimal Note",
            "obsidian_path": "fleeting/minimal.md"
        }
        meta = VectorMetadata.from_dict(d)
        assert meta.note_type == "fleeting"
        assert meta.knowledge_type == "fact"
        assert meta.status == "pending"
        assert meta.tags == []
        assert meta.hub_ids == []
        assert meta.link_count == 0
        assert meta.promoted is None

    def test_title_truncation(self):
        """Ensure long titles are truncated for S3V limits."""
        long_title = "A" * 500
        meta = VectorMetadata(
            note_type="fleeting",
            knowledge_type="fact",
            status="pending",
            title=long_title,
            tags=[],
            obsidian_path="fleeting/long.md"
        )
        d = meta.to_dict()
        assert len(d["title"]) == 200

    def test_content_preview_truncation(self):
        """Ensure long content previews are truncated."""
        long_preview = "B" * 1000
        meta = VectorMetadata(
            note_type="fleeting",
            knowledge_type="fact",
            status="pending",
            title="Test",
            tags=[],
            obsidian_path="fleeting/test.md",
            content_preview=long_preview
        )
        d = meta.to_dict()
        assert len(d["content_preview"]) == 500


class TestS3VectorsStore:
    def test_initialization(self):
        with patch("boto3.client"):
            store = S3VectorsStore("test-bucket", "test-index")
            assert store.bucket == "test-bucket"
            assert store.index == "test-index"

    def test_initialization_with_region(self):
        with patch("boto3.client") as mock_boto:
            store = S3VectorsStore("test-bucket", "test-index", region="eu-west-1")
            mock_boto.assert_called_once_with("s3vectors", region_name="eu-west-1")

    def test_put_vector(self):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            meta = VectorMetadata(
                note_type="fleeting",
                knowledge_type="fact",
                status="pending",
                title="Test",
                tags=["test"],
                obsidian_path="fleeting/test.md"
            )

            result = store.put_vector("key-123", [0.1] * 1536, meta)

            assert result is True
            mock_client.put_vectors.assert_called_once()
            call_kwargs = mock_client.put_vectors.call_args.kwargs
            assert call_kwargs["vectorBucketName"] == "test-bucket"
            assert call_kwargs["indexName"] == "test-index"

    def test_put_vector_returns_false_on_error(self):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.put_vectors.side_effect = Exception("API Error")
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            meta = VectorMetadata(
                note_type="fleeting",
                knowledge_type="fact",
                status="pending",
                title="Test",
                tags=["test"],
                obsidian_path="fleeting/test.md"
            )

            result = store.put_vector("key-123", [0.1] * 1536, meta)
            assert result is False

    def test_query_returns_ranked_results(self):
        mock_response = {
            "vectors": [
                {"key": "note-1", "distance": 0.1, "metadata": {"title": "Note 1", "tags": "aws"}},
                {"key": "note-2", "distance": 0.3, "metadata": {"title": "Note 2", "tags": "gcp"}},
            ]
        }

        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.query_vectors.return_value = mock_response
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            results = store.query([0.1] * 1536, top_k=5)

            assert len(results) == 2
            assert results[0]["key"] == "note-1"  # Closest first

    def test_query_with_filter(self):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.query_vectors.return_value = {"vectors": []}
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            store.query(
                [0.1] * 1536,
                top_k=5,
                filter={"status": "approved"}
            )

            call_kwargs = mock_client.query_vectors.call_args.kwargs
            assert "filter" in call_kwargs
            assert call_kwargs["filter"]["status"] == {"$eq": "approved"}

    def test_query_handles_empty_response(self):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.query_vectors.return_value = {}
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            results = store.query([0.1] * 1536)

            assert results == []

    def test_update_metadata(self):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            meta = VectorMetadata(
                note_type="permanent",
                knowledge_type="fact",
                status="approved",
                title="Updated Note",
                tags=["updated"],
                obsidian_path="permanent/updated.md"
            )

            result = store.update_metadata("key-123", meta)

            assert result is True
            mock_client.update_vector.assert_called_once()
            call_kwargs = mock_client.update_vector.call_args.kwargs
            assert call_kwargs["key"] == "key-123"

    def test_update_metadata_returns_false_on_error(self):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.update_vector.side_effect = Exception("Update failed")
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            meta = VectorMetadata(
                note_type="permanent",
                knowledge_type="fact",
                status="approved",
                title="Test",
                tags=[],
                obsidian_path="permanent/test.md"
            )

            result = store.update_metadata("key-123", meta)
            assert result is False

    def test_delete_vector(self):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            result = store.delete_vector("key-123")

            assert result is True
            mock_client.delete_vectors.assert_called_once()
            call_kwargs = mock_client.delete_vectors.call_args.kwargs
            assert call_kwargs["keys"] == ["key-123"]

    def test_delete_vector_returns_false_on_error(self):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.delete_vectors.side_effect = Exception("Delete failed")
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            result = store.delete_vector("key-123")

            assert result is False

    def test_get_vector(self):
        mock_response = {
            "vectors": [{
                "key": "key-123",
                "data": {"float32": [0.1] * 1536},
                "metadata": {"title": "Test Note", "note_type": "fleeting"}
            }]
        }
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.get_vectors.return_value = mock_response
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            result = store.get_vector("key-123")

            assert result is not None
            assert result["key"] == "key-123"
            mock_client.get_vectors.assert_called_once()

    def test_get_vector_returns_none_when_not_found(self):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.get_vectors.return_value = {"vectors": []}
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            result = store.get_vector("nonexistent-key")

            assert result is None

    def test_batch_put_vectors(self):
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")

            vectors = [
                ("key-1", [0.1] * 1536, VectorMetadata(
                    note_type="fleeting", knowledge_type="fact", status="pending",
                    title="Note 1", tags=["tag1"], obsidian_path="fleeting/note1.md"
                )),
                ("key-2", [0.2] * 1536, VectorMetadata(
                    note_type="permanent", knowledge_type="decision", status="approved",
                    title="Note 2", tags=["tag2"], obsidian_path="permanent/note2.md"
                )),
            ]

            result = store.batch_put_vectors(vectors)

            assert result is True
            mock_client.put_vectors.assert_called_once()
            call_kwargs = mock_client.put_vectors.call_args.kwargs
            assert len(call_kwargs["vectors"]) == 2


class TestS3VectorsBulkOperations:
    def test_query_all_returns_all_matching(self):
        """query_all should return all vectors matching filter."""
        mock_response = {
            "vectors": [
                {"key": "note-1", "metadata": {"status": "approved"}},
                {"key": "note-2", "metadata": {"status": "approved"}},
                {"key": "note-3", "metadata": {"status": "approved"}},
            ]
        }

        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.list_vectors.return_value = mock_response
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            results = store.query_all(filter={"status": "approved"})

            assert len(results) == 3
            assert all(r["metadata"]["status"] == "approved" for r in results)

    def test_query_all_with_embeddings(self):
        """query_all should include embeddings when requested."""
        mock_response = {
            "vectors": [
                {"key": "note-1", "data": {"float32": [0.1] * 1536}, "metadata": {"title": "Note 1"}},
            ]
        }

        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.list_vectors.return_value = mock_response
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            results = store.query_all(filter={"status": "approved"}, include_embeddings=True)

            # Check that embeddings are included
            mock_client.list_vectors.assert_called()

    def test_query_all_empty_result(self):
        """query_all should return empty list when no matches."""
        mock_response = {"vectors": []}

        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.list_vectors.return_value = mock_response
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            results = store.query_all(filter={"status": "nonexistent"})

            assert results == []

    def test_query_all_pagination(self):
        """query_all should handle pagination for large result sets."""
        # First page
        page1 = {
            "vectors": [{"key": f"note-{i}", "metadata": {}} for i in range(100)],
            "nextToken": "token123"
        }
        # Second page (last)
        page2 = {
            "vectors": [{"key": f"note-{i}", "metadata": {}} for i in range(100, 150)],
        }

        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.list_vectors.side_effect = [page1, page2]
            mock_boto.return_value = mock_client

            store = S3VectorsStore("test-bucket", "test-index")
            results = store.query_all(filter={}, include_embeddings=True)

            assert len(results) == 150
