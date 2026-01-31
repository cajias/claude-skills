"""Tests for knowledge extraction service."""

from unittest.mock import MagicMock, patch
from pathlib import Path

from ai_zettelkasten.extractor import KnowledgeExtractor, ExtractionItem
from ai_zettelkasten.obsidian import KnowledgeType


class TestExtractionItem:
    def test_from_dict(self):
        d = {
            "type": "fact",
            "title": "Test Fact",
            "content": "This is content",
            "tags": ["aws", "test"],
            "confidence": 0.9,
        }
        item = ExtractionItem.from_dict(d)
        assert item.knowledge_type == KnowledgeType.FACT
        assert item.title == "Test Fact"
        assert item.confidence == 0.9

    def test_from_dict_with_decision_type(self):
        d = {
            "type": "decision",
            "title": "Architecture Decision",
            "content": "Use Lambda over EC2",
            "tags": ["architecture"],
            "confidence": 0.95,
        }
        item = ExtractionItem.from_dict(d)
        assert item.knowledge_type == KnowledgeType.DECISION
        assert item.title == "Architecture Decision"

    def test_from_dict_with_pattern_type(self):
        d = {
            "type": "pattern",
            "title": "Retry Pattern",
            "content": "Use exponential backoff",
            "tags": ["patterns"],
            "confidence": 0.85,
        }
        item = ExtractionItem.from_dict(d)
        assert item.knowledge_type == KnowledgeType.PATTERN

    def test_from_dict_with_correction_type(self):
        d = {
            "type": "correction",
            "title": "Lambda Memory Fix",
            "content": "Actually use 256MB not 128MB",
            "tags": ["lambda"],
            "confidence": 0.9,
        }
        item = ExtractionItem.from_dict(d)
        assert item.knowledge_type == KnowledgeType.CORRECTION

    def test_from_dict_defaults(self):
        d = {}
        item = ExtractionItem.from_dict(d)
        assert item.knowledge_type == KnowledgeType.FACT
        assert item.title == "Untitled"
        assert item.content == ""
        assert item.tags == []
        assert item.confidence == 0.8

    def test_from_dict_with_source_session(self):
        d = {
            "type": "fact",
            "title": "Session Fact",
            "content": "Content",
            "tags": [],
            "confidence": 0.8,
            "source_session": "session-123",
        }
        item = ExtractionItem.from_dict(d)
        assert item.source_session == "session-123"


class TestKnowledgeExtractor:
    def test_process_item_creates_note(self, tmp_path):
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            item = ExtractionItem(
                knowledge_type=KnowledgeType.FACT,
                title="Test Fact",
                content="Test content",
                tags=["test"],
                confidence=0.85,
            )

            result = extractor.process_item(item)

            assert result["status"] == "stored"
            assert result["obsidian_path"] is not None

    def test_process_item_creates_note_file(self, tmp_path):
        """Verify the actual file is created in the vault."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            item = ExtractionItem(
                knowledge_type=KnowledgeType.FACT,
                title="My Test Note",
                content="This is test content",
                tags=["test"],
                confidence=0.85,
            )

            result = extractor.process_item(item)

            # Verify file exists
            note_path = Path(result["obsidian_path"])
            assert note_path.exists()

            # Verify content includes our text
            content = note_path.read_text()
            assert "My Test Note" in content
            assert "This is test content" in content

    def test_process_item_calls_embeddings(self, tmp_path):
        """Verify embeddings are generated with correct text."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_instance = MagicMock()
            mock_instance.embed.return_value = [0.1] * 1536
            mock_embed.return_value = mock_instance
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            item = ExtractionItem(
                knowledge_type=KnowledgeType.FACT,
                title="Embedding Test",
                content="Content for embedding",
                tags=[],
                confidence=0.8,
            )

            extractor.process_item(item)

            # Verify embed was called with title + content
            mock_instance.embed.assert_called_once()
            call_text = mock_instance.embed.call_args[0][0]
            assert "Embedding Test" in call_text
            assert "Content for embedding" in call_text

    def test_process_item_stores_vector(self, tmp_path):
        """Verify vector is stored with correct metadata."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_embed.return_value.embed.return_value = [0.5] * 1536
            mock_store_instance = MagicMock()
            mock_store_instance.put_vector.return_value = True
            mock_store.return_value = mock_store_instance

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test-bucket", index="test-index"
            )

            item = ExtractionItem(
                knowledge_type=KnowledgeType.DECISION,
                title="Store Test",
                content="Content to store",
                tags=["aws", "decision"],
                confidence=0.9,
            )

            extractor.process_item(item)

            # Verify put_vector was called
            mock_store_instance.put_vector.assert_called_once()
            call_args = mock_store_instance.put_vector.call_args

            # Check embedding
            embedding = call_args[0][1]
            assert len(embedding) == 1536

            # Check metadata
            metadata = call_args[0][2]
            assert metadata.knowledge_type == "decision"
            assert metadata.title == "Store Test"
            assert "aws" in metadata.tags

    def test_process_item_handles_embedding_error(self, tmp_path):
        """Verify partial status when embedding fails."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore"),
        ):
            mock_embed.return_value.embed.side_effect = Exception(
                "Embedding service down"
            )

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            item = ExtractionItem(
                knowledge_type=KnowledgeType.FACT,
                title="Error Test",
                content="Content",
                tags=[],
                confidence=0.8,
            )

            result = extractor.process_item(item)

            assert result["status"] == "partial"
            assert "Embedding failed" in result["error"]
            # Note should still be written to Obsidian
            assert result["obsidian_path"] is not None

    def test_process_item_handles_storage_error(self, tmp_path):
        """Verify partial status when vector storage fails."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = False

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            item = ExtractionItem(
                knowledge_type=KnowledgeType.FACT,
                title="Storage Fail Test",
                content="Content",
                tags=[],
                confidence=0.8,
            )

            result = extractor.process_item(item)

            assert result["status"] == "partial"
            assert "Vector storage failed" in result["error"]

    def test_process_items_batch(self, tmp_path):
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            items = [
                {
                    "type": "fact",
                    "title": "Fact 1",
                    "content": "C1",
                    "tags": [],
                    "confidence": 0.8,
                },
                {
                    "type": "decision",
                    "title": "Decision 1",
                    "content": "C2",
                    "tags": [],
                    "confidence": 0.9,
                },
            ]

            summary = extractor.process_items(items)

            assert summary["total"] == 2
            assert summary["stored"] == 2

    def test_process_items_batch_with_mixed_results(self, tmp_path):
        """Test batch processing with some failures."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            # First embed succeeds, second fails
            mock_embed.return_value.embed.side_effect = [
                [0.1] * 1536,
                Exception("Embedding failed"),
            ]
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            items = [
                {
                    "type": "fact",
                    "title": "Success Item",
                    "content": "C1",
                    "tags": [],
                    "confidence": 0.8,
                },
                {
                    "type": "fact",
                    "title": "Fail Item",
                    "content": "C2",
                    "tags": [],
                    "confidence": 0.8,
                },
            ]

            summary = extractor.process_items(items)

            assert summary["total"] == 2
            assert summary["stored"] == 1
            assert summary["partial"] == 1

    def test_process_items_returns_individual_results(self, tmp_path):
        """Verify individual results are included in summary."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            items = [
                {
                    "type": "pattern",
                    "title": "Pattern 1",
                    "content": "C1",
                    "tags": ["p1"],
                    "confidence": 0.8,
                },
            ]

            summary = extractor.process_items(items)

            assert "results" in summary
            assert len(summary["results"]) == 1
            assert summary["results"][0]["title"] == "Pattern 1"

    def test_find_related_notes(self, tmp_path):
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.query.return_value = [
                {
                    "key": "related-1",
                    "distance": 0.2,
                    "metadata": {"title": "Related Note"},
                }
            ]

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            related = extractor.find_related("Test query")

            assert len(related) == 1
            assert related[0]["key"] == "related-1"

    def test_find_related_calls_embeddings(self, tmp_path):
        """Verify query is embedded before searching."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_instance = MagicMock()
            mock_instance.embed.return_value = [0.2] * 1536
            mock_embed.return_value = mock_instance
            mock_store.return_value.query.return_value = []

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            extractor.find_related("Search for AWS Lambda")

            mock_instance.embed.assert_called_once_with("Search for AWS Lambda")

    def test_find_related_with_top_k(self, tmp_path):
        """Verify top_k parameter is passed to query."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store_instance = MagicMock()
            mock_store_instance.query.return_value = []
            mock_store.return_value = mock_store_instance

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            extractor.find_related("Query", top_k=20)

            mock_store_instance.query.assert_called_once()
            call_kwargs = mock_store_instance.query.call_args[1]
            assert call_kwargs.get("top_k") == 20

    def test_find_related_filters_by_threshold(self, tmp_path):
        """Verify results are filtered by similarity threshold."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.query.return_value = [
                {"key": "close", "distance": 0.1, "metadata": {"title": "Close Match"}},
                {"key": "far", "distance": 0.5, "metadata": {"title": "Far Match"}},
            ]

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            # Default threshold is 0.75, so distance must be < 0.25
            related = extractor.find_related("Query")

            assert len(related) == 1
            assert related[0]["key"] == "close"

    def test_find_related_custom_threshold(self, tmp_path):
        """Verify custom threshold works correctly."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.query.return_value = [
                {"key": "close", "distance": 0.1, "metadata": {"title": "Close Match"}},
                {
                    "key": "medium",
                    "distance": 0.4,
                    "metadata": {"title": "Medium Match"},
                },
            ]

            extractor = KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test"
            )

            # Threshold 0.5 means distance must be < 0.5
            related = extractor.find_related("Query", threshold=0.5)

            assert len(related) == 2

    def test_extractor_uses_custom_region(self, tmp_path):
        """Verify region is passed to both services."""
        with (
            patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed,
            patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store,
        ):
            KnowledgeExtractor(
                vault_path=tmp_path, bucket="test", index="test", region="eu-west-1"
            )

            mock_embed.assert_called_once_with("eu-west-1")
            mock_store.assert_called_once_with("test", "test", "eu-west-1")
