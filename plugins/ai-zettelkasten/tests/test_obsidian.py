"""Tests for Obsidian note management."""

from ai_zettelkasten.obsidian import ObsidianVault, Note, NoteType, KnowledgeType


class TestNote:
    def test_note_creation_with_defaults(self):
        note = Note(
            title="Test Note",
            content="This is test content",
            knowledge_type=KnowledgeType.FACT,
        )
        assert note.title == "Test Note"
        assert note.note_type == NoteType.FLEETING
        assert note.status == "pending"
        assert note.tags == []

    def test_note_to_markdown(self):
        note = Note(
            title="S3 Vectors Dimensions",
            content="Bedrock Titan uses 1536 dimensions.",
            knowledge_type=KnowledgeType.FACT,
            tags=["aws", "s3-vectors"],
        )
        md = note.to_markdown()
        assert "# S3 Vectors Dimensions" in md
        assert "type: fleeting" in md
        assert "knowledge_type: fact" in md
        assert "tags:" in md
        assert "Bedrock Titan uses 1536 dimensions." in md

    def test_note_from_markdown(self):
        md = """---
id: test-123
type: fleeting
knowledge_type: fact
status: pending
tags:
  - aws
  - s3-vectors
---

# S3 Vectors Dimensions

Bedrock Titan uses 1536 dimensions.
"""
        note = Note.from_markdown(md)
        assert note.id == "test-123"
        assert note.note_type == NoteType.FLEETING
        assert note.knowledge_type == KnowledgeType.FACT
        assert note.tags == ["aws", "s3-vectors"]


class TestObsidianVault:
    def test_vault_initialization(self, tmp_path):
        vault = ObsidianVault(tmp_path)
        assert vault.root == tmp_path
        assert (tmp_path / "knowledge-base" / "fleeting").exists()
        assert (tmp_path / "knowledge-base" / "permanent").exists()
        assert (tmp_path / "knowledge-base" / "hubs").exists()

    def test_write_fleeting_note(self, tmp_path):
        vault = ObsidianVault(tmp_path)
        note = Note(
            title="Test Fact",
            content="Some content",
            knowledge_type=KnowledgeType.FACT,
        )
        path = vault.write_note(note)
        assert path.exists()
        assert "fleeting" in str(path)

    def test_read_note(self, tmp_path):
        vault = ObsidianVault(tmp_path)
        note = Note(
            title="Test Read",
            content="Read me",
            knowledge_type=KnowledgeType.DECISION,
        )
        path = vault.write_note(note)

        read_note = vault.read_note(path)
        assert read_note.title == "Test Read"
        assert read_note.content == "Read me"

    def test_list_pending_notes(self, tmp_path):
        vault = ObsidianVault(tmp_path)

        # Create 3 fleeting notes
        for i in range(3):
            note = Note(
                title=f"Note {i}",
                content=f"Content {i}",
                knowledge_type=KnowledgeType.FACT,
            )
            vault.write_note(note)

        pending = vault.list_pending_notes()
        assert len(pending) == 3

    def test_promote_note(self, tmp_path):
        vault = ObsidianVault(tmp_path)
        note = Note(
            title="Promotable Note",
            content="Will be promoted",
            knowledge_type=KnowledgeType.PATTERN,
        )
        fleeting_path = vault.write_note(note)

        permanent_path = vault.promote_note(fleeting_path)
        assert "permanent" in str(permanent_path)
        assert not fleeting_path.exists()

        promoted = vault.read_note(permanent_path)
        assert promoted.note_type == NoteType.PERMANENT
        assert promoted.status == "approved"


class TestHubManagement:
    def test_write_hub_note(self, tmp_path):
        """Write a hub note to the hubs folder."""
        from ai_zettelkasten.obsidian import (
            ObsidianVault,
            Note,
            NoteType,
            KnowledgeType,
        )

        vault = ObsidianVault(tmp_path)
        hub = Note(
            id="hub-aws-lambda",
            title="Hub: AWS Lambda",
            content="Auto-generated hub for AWS Lambda notes.",
            knowledge_type=KnowledgeType.FACT,
            note_type=NoteType.HUB,
            status="generated",
            tags=["aws", "lambda"],
        )

        path = vault.write_hub(hub)

        assert path.exists()
        assert "hubs" in str(path)
        assert path.name == "hub-aws-lambda.md"

    def test_list_hubs(self, tmp_path):
        """List all hub notes in the vault."""
        from ai_zettelkasten.obsidian import (
            ObsidianVault,
            Note,
            NoteType,
            KnowledgeType,
        )

        vault = ObsidianVault(tmp_path)

        # Create two hub notes
        for i in range(2):
            hub = Note(
                id=f"hub-test-{i}",
                title=f"Hub: Test {i}",
                content=f"Test hub {i}",
                knowledge_type=KnowledgeType.FACT,
                note_type=NoteType.HUB,
                status="generated",
                tags=["test"],
            )
            vault.write_hub(hub)

        hubs = vault.list_hubs()

        assert len(hubs) == 2

    def test_read_hub(self, tmp_path):
        """Read a hub note by ID."""
        from ai_zettelkasten.obsidian import (
            ObsidianVault,
            Note,
            NoteType,
            KnowledgeType,
        )

        vault = ObsidianVault(tmp_path)
        hub = Note(
            id="hub-read-test",
            title="Hub: Read Test",
            content="Testing hub reading",
            knowledge_type=KnowledgeType.FACT,
            note_type=NoteType.HUB,
            status="generated",
            tags=["testing"],
        )
        vault.write_hub(hub)

        read_hub = vault.read_hub("hub-read-test")

        assert read_hub is not None
        assert read_hub.title == "Hub: Read Test"
        assert read_hub.note_type == NoteType.HUB

    def test_read_hub_not_found(self, tmp_path):
        """Return None when hub doesn't exist."""
        from ai_zettelkasten.obsidian import ObsidianVault

        vault = ObsidianVault(tmp_path)
        result = vault.read_hub("nonexistent-hub")

        assert result is None
