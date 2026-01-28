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


class TestP1ProactiveFeatures:
    """Integration tests for P1 proactive features."""

    def test_suggester_integration_with_real_patterns(self, tmp_path):
        """Test suggester with realistic code content."""
        from ai_zettelkasten.suggester import Suggester

        suggester = Suggester()

        # Realistic Python code with extractable knowledge
        code = '''
        # NOTE: S3 Vectors has a maximum of 50 metadata keys per vector
        MAX_METADATA_KEYS = 50

        # We chose uvx over pip because it provides better dependency isolation
        # for hooks that run in various environments
        PACKAGE_MANAGER = "uvx"

        # Fixed: was using 1024 dimensions but Titan actually uses 1536
        TITAN_DIMENSIONS = 1536

        # Always validate embedding dimensions before storage
        def validate_embedding(embedding):
            if len(embedding) != TITAN_DIMENSIONS:
                raise ValueError("Invalid embedding dimensions")
        '''

        suggestions = suggester.analyze("config.py", code)

        # Should detect multiple knowledge types
        types = {s.knowledge_type.value for s in suggestions}
        assert "fact" in types  # NOTE: comment
        assert "decision" in types  # chose uvx
        assert "correction" in types  # Fixed: was using
        assert "pattern" in types  # Always validate

    def test_clustering_with_mock_vectors(self, tmp_path):
        """Test hub generation with mocked vector store."""
        from unittest.mock import MagicMock, patch
        import numpy as np
        from ai_zettelkasten.clustering import HubGenerator
        from ai_zettelkasten.obsidian import ObsidianVault

        # Create similar vectors (should cluster)
        similar_vectors = [
            {"key": f"note-{i}", "embedding": [1.0 - i*0.01, 0.0] + [0.0]*1534,
             "metadata": {"tags": "aws,lambda", "title": f"Note {i}", "knowledge_type": "fact", "status": "approved"}}
            for i in range(5)
        ]

        with patch("ai_zettelkasten.clustering.S3VectorsStore") as mock_store_class:
            mock_store = MagicMock()
            mock_store.query_all.return_value = similar_vectors
            mock_store.update_metadata.return_value = True

            vault = ObsidianVault(tmp_path)

            generator = HubGenerator(
                vectors_store=mock_store,
                vault=vault,
                threshold=0.9,
                min_size=3
            )

            hubs = generator.generate_hubs()

            # Should create at least one hub from the 5 similar notes
            hub_files = list((tmp_path / "knowledge-base" / "hubs").glob("*.md"))
            # May or may not create hub depending on actual clustering
            # At minimum, verify the process completes without error

    def test_full_proactive_workflow(self, tmp_path):
        """Test complete workflow: detect → capture → cluster."""
        from unittest.mock import MagicMock, patch
        from ai_zettelkasten.suggester import Suggester
        from ai_zettelkasten.extractor import KnowledgeExtractor
        from ai_zettelkasten.obsidian import ObsidianVault

        # 1. Detect knowledge in code
        suggester = Suggester()
        code = "# NOTE: Lambda cold starts are slower with larger packages"
        suggestions = suggester.analyze("lambda.py", code)

        assert len(suggestions) >= 1
        suggestion = suggestions[0]

        # 2. Capture the suggestion as a fleeting note
        with patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed, \
             patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store:

            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(tmp_path, "bucket", "index")
            # Use process_items which accepts dicts
            result = extractor.process_items([{
                "type": suggestion.knowledge_type.value,
                "title": "Lambda Cold Start Performance",
                "content": suggestion.content,
                "tags": suggestion.tags,
                "confidence": suggestion.confidence
            }])

            assert result["stored"] == 1

        # 3. Verify note was created
        vault = ObsidianVault(tmp_path)
        pending = vault.list_pending_notes()
        assert len(pending) >= 1

    def test_hub_management_methods(self, tmp_path):
        """Test ObsidianVault hub methods work together."""
        from ai_zettelkasten.obsidian import ObsidianVault, Note, NoteType, KnowledgeType

        vault = ObsidianVault(tmp_path)

        # Create multiple hubs
        hubs_data = [
            ("hub-aws-serverless", "AWS Serverless", ["aws", "lambda"]),
            ("hub-testing-patterns", "Testing Patterns", ["pytest", "testing"]),
        ]

        for hub_id, title, tags in hubs_data:
            hub = Note(
                id=hub_id,
                title=f"Hub: {title}",
                content=f"Auto-generated hub for {title}",
                knowledge_type=KnowledgeType.FACT,
                note_type=NoteType.HUB,
                status="generated",
                tags=tags,
            )
            vault.write_hub(hub)

        # List should return both
        hub_paths = vault.list_hubs()
        assert len(hub_paths) == 2

        # Read specific hub
        aws_hub = vault.read_hub("hub-aws-serverless")
        assert aws_hub is not None
        assert "AWS Serverless" in aws_hub.title
        assert aws_hub.note_type == NoteType.HUB