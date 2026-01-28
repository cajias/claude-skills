"""Integration tests for AI Zettelkasten."""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_zettelkasten.extractor import KnowledgeExtractor
from ai_zettelkasten.obsidian import ObsidianVault, Note, NoteType, KnowledgeType


class TestEndToEnd:
    """End-to-end workflow tests."""

    def test_extract_review_search_workflow(self, tmp_path):
        """Test complete workflow: extract -> review -> search."""
        with patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed, \
             patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store:

            # Setup mocks
            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = True
            mock_store.return_value.query.return_value = [
                {"key": "test-key", "distance": 0.2, "metadata": {"title": "Test"}}
            ]

            # Initialize
            extractor = KnowledgeExtractor(tmp_path, "bucket", "index")
            vault = ObsidianVault(tmp_path)

            # 1. Extract items
            items = [
                {"type": "fact", "title": "Test Fact", "content": "Content", "tags": ["test"], "confidence": 0.9}
            ]
            summary = extractor.process_items(items)
            assert summary["stored"] == 1

            # 2. Verify fleeting note created
            pending = vault.list_pending_notes()
            assert len(pending) == 1

            # 3. Promote to permanent
            permanent_path = vault.promote_note(pending[0])
            assert "permanent" in str(permanent_path)

            # 4. Search finds the note
            related = extractor.find_related("test query")
            assert len(related) == 1

    def test_multiple_knowledge_types(self, tmp_path):
        """Test extraction of all knowledge types."""
        with patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed, \
             patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store:

            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(tmp_path, "bucket", "index")

            items = [
                {"type": "fact", "title": "Fact", "content": "A fact", "tags": [], "confidence": 0.8},
                {"type": "decision", "title": "Decision", "content": "A decision", "tags": [], "confidence": 0.9},
                {"type": "pattern", "title": "Pattern", "content": "A pattern", "tags": [], "confidence": 0.85},
                {"type": "correction", "title": "Correction", "content": "A correction", "tags": [], "confidence": 0.95},
            ]

            summary = extractor.process_items(items)

            assert summary["total"] == 4
            assert summary["stored"] == 4

    def test_vault_folder_structure(self, tmp_path):
        """Test that vault creates correct folder structure."""
        vault = ObsidianVault(tmp_path)

        assert (tmp_path / "knowledge-base" / "fleeting").exists()
        assert (tmp_path / "knowledge-base" / "permanent").exists()
        assert (tmp_path / "knowledge-base" / "hubs").exists()
        assert (tmp_path / "knowledge-base" / "projects").exists()

    def test_note_promotion_updates_metadata(self, tmp_path):
        """Test that promoting a note updates its type and status."""
        vault = ObsidianVault(tmp_path)

        # Create fleeting note
        note = Note(
            title="Test Note",
            content="Test content",
            knowledge_type=KnowledgeType.FACT,
        )
        fleeting_path = vault.write_note(note)

        # Read and verify it's fleeting
        fleeting_note = vault.read_note(fleeting_path)
        assert fleeting_note.note_type == NoteType.FLEETING
        assert fleeting_note.status == "pending"

        # Promote
        permanent_path = vault.promote_note(fleeting_path)

        # Read and verify it's permanent
        promoted_note = vault.read_note(permanent_path)
        assert promoted_note.note_type == NoteType.PERMANENT
        assert promoted_note.status == "approved"
        assert promoted_note.promoted is not None

    def test_extract_with_tags_and_source_session(self, tmp_path):
        """Test extraction preserves tags and source session."""
        with patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed, \
             patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store:

            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(tmp_path, "bucket", "index")
            vault = ObsidianVault(tmp_path)

            items = [
                {
                    "type": "decision",
                    "title": "Use Lambda",
                    "content": "Decided to use Lambda over EC2",
                    "tags": ["aws", "architecture", "lambda"],
                    "confidence": 0.95,
                    "source_session": "session-abc123"
                }
            ]

            summary = extractor.process_items(items)
            assert summary["stored"] == 1

            # Verify the note has correct tags and source
            pending = vault.list_pending_notes()
            note = vault.read_note(pending[0])
            assert "aws" in note.tags
            assert "architecture" in note.tags
            assert note.source_session == "session-abc123"

    def test_search_filtering_by_distance(self, tmp_path):
        """Test that search filters results by similarity threshold."""
        with patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed, \
             patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store:

            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.query.return_value = [
                {"key": "close", "distance": 0.1, "metadata": {"title": "Close Match"}},
                {"key": "medium", "distance": 0.3, "metadata": {"title": "Medium Match"}},
                {"key": "far", "distance": 0.6, "metadata": {"title": "Far Match"}},
            ]

            extractor = KnowledgeExtractor(tmp_path, "bucket", "index")

            # Default threshold 0.75 -> distance < 0.25
            related = extractor.find_related("query")
            assert len(related) == 1
            assert related[0]["key"] == "close"

            # Lower threshold 0.5 -> distance < 0.5
            related = extractor.find_related("query", threshold=0.5)
            assert len(related) == 2

    def test_partial_failure_workflow(self, tmp_path):
        """Test workflow continues when some items fail."""
        with patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed, \
             patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store:

            # First item succeeds, second fails embedding
            mock_embed.return_value.embed.side_effect = [
                [0.1] * 1536,
                Exception("Embedding service unavailable"),
                [0.1] * 1536,
            ]
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(tmp_path, "bucket", "index")
            vault = ObsidianVault(tmp_path)

            items = [
                {"type": "fact", "title": "Success 1", "content": "C1", "tags": [], "confidence": 0.8},
                {"type": "fact", "title": "Fail Item", "content": "C2", "tags": [], "confidence": 0.8},
                {"type": "fact", "title": "Success 2", "content": "C3", "tags": [], "confidence": 0.8},
            ]

            summary = extractor.process_items(items)

            # All items should create notes (3 pending)
            pending = vault.list_pending_notes()
            assert len(pending) == 3

            # But only 2 fully stored
            assert summary["stored"] == 2
            assert summary["partial"] == 1

    def test_note_roundtrip_preserves_data(self, tmp_path):
        """Test that writing and reading a note preserves all data."""
        vault = ObsidianVault(tmp_path)

        original = Note(
            title="Complete Note",
            content="Full content with details",
            knowledge_type=KnowledgeType.PATTERN,
            tags=["pattern", "testing"],
            links=["Other Note"],
            hubs=["Testing Hub"],
            scope="project",
            project="test-project",
            confidence=0.92,
            source_session="session-xyz",
        )

        path = vault.write_note(original)
        restored = vault.read_note(path)

        assert restored.title == original.title
        assert restored.content == original.content
        assert restored.knowledge_type == original.knowledge_type
        assert restored.tags == original.tags
        assert restored.links == original.links
        assert restored.hubs == original.hubs
        assert restored.scope == original.scope
        assert restored.project == original.project
        assert restored.confidence == original.confidence
        assert restored.source_session == original.source_session

    def test_duplicate_title_handling(self, tmp_path):
        """Test that duplicate titles create separate files."""
        with patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed, \
             patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store:

            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(tmp_path, "bucket", "index")
            vault = ObsidianVault(tmp_path)

            # Create items with same title
            items = [
                {"type": "fact", "title": "Same Title", "content": "First content", "tags": [], "confidence": 0.8},
                {"type": "fact", "title": "Same Title", "content": "Second content", "tags": [], "confidence": 0.8},
                {"type": "fact", "title": "Same Title", "content": "Third content", "tags": [], "confidence": 0.8},
            ]

            summary = extractor.process_items(items)

            # All should be stored
            assert summary["stored"] == 3

            # Should have 3 separate files
            pending = vault.list_pending_notes()
            assert len(pending) == 3

            # All files should have different paths
            paths = [str(p) for p in pending]
            assert len(set(paths)) == 3
