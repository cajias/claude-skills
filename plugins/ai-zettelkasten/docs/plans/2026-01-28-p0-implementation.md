# AI Zettelkasten v2.0 P0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the core Zettelkasten workflow with atomic notes, review queue, semantic search, and proper folder structure.

**Architecture:** Python library modules (s3vectors, embeddings, obsidian) with uvx-compatible hooks and Claude Code skills. Obsidian stores human-readable notes, S3 Vectors enables semantic search.

**Tech Stack:** Python 3.11+, boto3, rich, pyyaml, uvx for dependency isolation

---

## Prerequisites

- AWS credentials configured with access to Bedrock and S3 Vectors
- Obsidian vault at `~/Documents/obsidian-vault-work/`
- S3 Vectors bucket `zettelkasten-prod` with index `knowledge-index` deployed

---

## Task 1: Project Structure Setup

**Files:**
- Create: `plugins/ai-zettelkasten/pyproject.toml`
- Create: `plugins/ai-zettelkasten/src/ai_zettelkasten/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "ai-zettelkasten"
version = "2.0.0"
description = "Claude Code plugin for Zettelkasten knowledge management"
requires-python = ">=3.11"
dependencies = [
    "boto3>=1.35.0",
    "rich>=13.0.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[project.scripts]
zk-extract = "ai_zettelkasten.cli:extract_main"
zk-suggest = "ai_zettelkasten.cli:suggest_main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ai_zettelkasten"]
```

**Step 2: Create package init**

```python
"""AI Zettelkasten - Knowledge management for Claude Code."""

__version__ = "2.0.0"
```

**Step 3: Create directory structure**

Run:
```bash
mkdir -p src/ai_zettelkasten tests
touch src/ai_zettelkasten/__init__.py
```

**Step 4: Commit**

```bash
git add pyproject.toml src/
git commit -m "feat: initialize ai-zettelkasten v2 project structure"
```

---

## Task 2: Obsidian Module - Note Management

**Files:**
- Create: `plugins/ai-zettelkasten/src/ai_zettelkasten/obsidian.py`
- Create: `plugins/ai-zettelkasten/tests/test_obsidian.py`

**Step 1: Write failing tests**

```python
"""Tests for Obsidian note management."""
import pytest
from pathlib import Path
import tempfile
import yaml

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
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/ai-zettelkasten && python -m pytest tests/test_obsidian.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'ai_zettelkasten.obsidian'"

**Step 3: Write implementation**

```python
"""Obsidian vault management for AI Zettelkasten."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import hashlib
import re
import yaml


class NoteType(Enum):
    """Structural note types."""
    FLEETING = "fleeting"
    PERMANENT = "permanent"
    HUB = "hub"


class KnowledgeType(Enum):
    """Knowledge categories."""
    FACT = "fact"
    DECISION = "decision"
    PATTERN = "pattern"
    CORRECTION = "correction"


@dataclass
class Note:
    """Represents a Zettelkasten note."""
    title: str
    content: str
    knowledge_type: KnowledgeType
    id: Optional[str] = None
    note_type: NoteType = NoteType.FLEETING
    status: str = "pending"
    tags: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    hubs: list[str] = field(default_factory=list)
    scope: str = "global"
    project: Optional[str] = None
    confidence: float = 0.8
    source_session: Optional[str] = None
    created: Optional[datetime] = None
    promoted: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = self._generate_id()
        if self.created is None:
            self.created = datetime.now()

    def _generate_id(self) -> str:
        """Generate unique ID based on type, date, and content hash."""
        prefix = self.note_type.value[:4]
        date = datetime.now().strftime("%Y%m%d")
        content_hash = hashlib.sha256(
            f"{self.title}{self.content}".encode()
        ).hexdigest()[:6]
        return f"{prefix}-{date}-{content_hash}"

    def to_markdown(self) -> str:
        """Convert note to Obsidian markdown with frontmatter."""
        frontmatter = {
            "id": self.id,
            "type": self.note_type.value,
            "knowledge_type": self.knowledge_type.value,
            "status": self.status,
            "tags": self.tags,
            "scope": self.scope,
            "confidence": self.confidence,
            "created": self.created.isoformat() if self.created else None,
        }

        if self.links:
            frontmatter["links"] = [f"[[{link}]]" for link in self.links]
        if self.hubs:
            frontmatter["hubs"] = [f"[[{hub}]]" for hub in self.hubs]
        if self.project:
            frontmatter["project"] = self.project
        if self.source_session:
            frontmatter["source_session"] = self.source_session
        if self.promoted:
            frontmatter["promoted"] = self.promoted.isoformat()

        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

        return f"""---
{yaml_str.strip()}
---

# {self.title}

{self.content}
"""

    @classmethod
    def from_markdown(cls, markdown: str) -> "Note":
        """Parse markdown with frontmatter into Note."""
        # Split frontmatter and content
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", markdown, re.DOTALL)
        if not match:
            raise ValueError("Invalid markdown format: missing frontmatter")

        frontmatter_str, body = match.groups()
        frontmatter = yaml.safe_load(frontmatter_str)

        # Extract title from body
        title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = title_match.group(1) if title_match else "Untitled"

        # Extract content (everything after title)
        content = body
        if title_match:
            content = body[title_match.end():].strip()

        # Parse links and hubs (remove [[ ]] wrappers)
        links = []
        if "links" in frontmatter:
            links = [re.sub(r"\[\[(.*?)\]\]", r"\1", link) for link in frontmatter.get("links", [])]

        hubs = []
        if "hubs" in frontmatter:
            hubs = [re.sub(r"\[\[(.*?)\]\]", r"\1", hub) for hub in frontmatter.get("hubs", [])]

        return cls(
            id=frontmatter.get("id"),
            title=title,
            content=content,
            note_type=NoteType(frontmatter.get("type", "fleeting")),
            knowledge_type=KnowledgeType(frontmatter.get("knowledge_type", "fact")),
            status=frontmatter.get("status", "pending"),
            tags=frontmatter.get("tags", []),
            links=links,
            hubs=hubs,
            scope=frontmatter.get("scope", "global"),
            project=frontmatter.get("project"),
            confidence=frontmatter.get("confidence", 0.8),
            source_session=frontmatter.get("source_session"),
            created=datetime.fromisoformat(frontmatter["created"]) if frontmatter.get("created") else None,
            promoted=datetime.fromisoformat(frontmatter["promoted"]) if frontmatter.get("promoted") else None,
        )


class ObsidianVault:
    """Manages the Obsidian vault structure for Zettelkasten."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self._ensure_structure()

    def _ensure_structure(self):
        """Create the knowledge-base folder structure."""
        kb = self.root / "knowledge-base"
        (kb / "fleeting").mkdir(parents=True, exist_ok=True)
        (kb / "permanent").mkdir(parents=True, exist_ok=True)
        (kb / "hubs").mkdir(parents=True, exist_ok=True)
        (kb / "projects").mkdir(parents=True, exist_ok=True)

    def _get_folder(self, note_type: NoteType) -> Path:
        """Get the folder path for a note type."""
        return self.root / "knowledge-base" / note_type.value

    def write_note(self, note: Note) -> Path:
        """Write a note to the appropriate folder."""
        folder = self._get_folder(note.note_type)

        # Create filename from title (slugified)
        slug = re.sub(r"[^a-z0-9]+", "-", note.title.lower()).strip("-")
        filename = f"{slug}.md"
        path = folder / filename

        # Handle duplicates
        counter = 1
        while path.exists():
            path = folder / f"{slug}-{counter}.md"
            counter += 1

        path.write_text(note.to_markdown())
        return path

    def read_note(self, path: Path) -> Note:
        """Read a note from a file path."""
        markdown = path.read_text()
        return Note.from_markdown(markdown)

    def list_pending_notes(self) -> list[Path]:
        """List all notes with pending status in fleeting folder."""
        fleeting = self._get_folder(NoteType.FLEETING)
        pending = []

        for path in fleeting.glob("*.md"):
            try:
                note = self.read_note(path)
                if note.status == "pending":
                    pending.append(path)
            except Exception:
                continue

        return pending

    def promote_note(self, path: Path) -> Path:
        """Promote a fleeting note to permanent."""
        note = self.read_note(path)

        # Update note properties
        note.note_type = NoteType.PERMANENT
        note.status = "approved"
        note.promoted = datetime.now()

        # Write to permanent folder
        new_path = self.write_note(note)

        # Remove original fleeting note
        path.unlink()

        return new_path
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/ai-zettelkasten && python -m pytest tests/test_obsidian.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/ai_zettelkasten/obsidian.py tests/test_obsidian.py
git commit -m "feat: add obsidian module for note management"
```

---

## Task 3: Embeddings Module - Bedrock Titan

**Files:**
- Create: `plugins/ai-zettelkasten/src/ai_zettelkasten/embeddings.py`
- Create: `plugins/ai-zettelkasten/tests/test_embeddings.py`

**Step 1: Write failing tests**

```python
"""Tests for Bedrock Titan embeddings."""
import pytest
from unittest.mock import MagicMock, patch
import json

from ai_zettelkasten.embeddings import BedrockEmbeddings, TITAN_DIMENSIONS


class TestBedrockEmbeddings:
    def test_initialization(self):
        with patch("boto3.client"):
            embeddings = BedrockEmbeddings()
            assert embeddings.model_id == "amazon.titan-embed-text-v1"
            assert embeddings.dimensions == TITAN_DIMENSIONS

    def test_embed_text_returns_correct_dimensions(self):
        mock_response = {
            "body": MagicMock(
                read=MagicMock(return_value=json.dumps({
                    "embedding": [0.1] * TITAN_DIMENSIONS
                }).encode())
            )
        }

        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.invoke_model.return_value = mock_response
            mock_boto.return_value = mock_client

            embeddings = BedrockEmbeddings()
            result = embeddings.embed("Test text")

            assert len(result) == TITAN_DIMENSIONS
            assert all(isinstance(x, float) for x in result)

    def test_embed_truncates_long_text(self):
        long_text = "x" * 10000  # Longer than max

        mock_response = {
            "body": MagicMock(
                read=MagicMock(return_value=json.dumps({
                    "embedding": [0.1] * TITAN_DIMENSIONS
                }).encode())
            )
        }

        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.invoke_model.return_value = mock_response
            mock_boto.return_value = mock_client

            embeddings = BedrockEmbeddings()
            result = embeddings.embed(long_text)

            # Verify text was truncated in the call
            call_args = mock_client.invoke_model.call_args
            body = json.loads(call_args.kwargs["body"])
            assert len(body["inputText"]) <= 8000

    def test_embed_batch(self):
        mock_response = {
            "body": MagicMock(
                read=MagicMock(return_value=json.dumps({
                    "embedding": [0.1] * TITAN_DIMENSIONS
                }).encode())
            )
        }

        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.invoke_model.return_value = mock_response
            mock_boto.return_value = mock_client

            embeddings = BedrockEmbeddings()
            results = embeddings.embed_batch(["Text 1", "Text 2", "Text 3"])

            assert len(results) == 3
            assert all(len(r) == TITAN_DIMENSIONS for r in results)
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/ai-zettelkasten && python -m pytest tests/test_embeddings.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write implementation**

```python
"""Bedrock Titan embeddings for semantic search."""
import json
from typing import Optional
import boto3

# Titan embedding model configuration
TITAN_MODEL_ID = "amazon.titan-embed-text-v1"
TITAN_DIMENSIONS = 1536
TITAN_MAX_INPUT = 8000  # Character limit


class BedrockEmbeddings:
    """Generate embeddings using Bedrock Titan."""

    def __init__(self, region: Optional[str] = None):
        self.model_id = TITAN_MODEL_ID
        self.dimensions = TITAN_DIMENSIONS
        self.max_input = TITAN_MAX_INPUT
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region or "us-east-1"
        )

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        # Truncate if necessary
        truncated = text[:self.max_input]

        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({"inputText": truncated})
        )

        result = json.loads(response["body"].read())
        return result["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed(text) for text in texts]
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/ai-zettelkasten && python -m pytest tests/test_embeddings.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/ai_zettelkasten/embeddings.py tests/test_embeddings.py
git commit -m "feat: add embeddings module for Bedrock Titan"
```

---

## Task 4: S3 Vectors Module

**Files:**
- Create: `plugins/ai-zettelkasten/src/ai_zettelkasten/s3vectors.py`
- Create: `plugins/ai-zettelkasten/tests/test_s3vectors.py`

**Step 1: Write failing tests**

```python
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


class TestS3VectorsStore:
    def test_initialization(self):
        with patch("boto3.client"):
            store = S3VectorsStore("test-bucket", "test-index")
            assert store.bucket == "test-bucket"
            assert store.index == "test-index"

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

            store.put_vector("key-123", [0.1] * 1536, meta)

            mock_client.put_vectors.assert_called_once()
            call_kwargs = mock_client.put_vectors.call_args.kwargs
            assert call_kwargs["vectorBucketName"] == "test-bucket"
            assert call_kwargs["indexName"] == "test-index"

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
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/ai-zettelkasten && python -m pytest tests/test_s3vectors.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write implementation**

```python
"""S3 Vectors storage for semantic search."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import boto3


@dataclass
class VectorMetadata:
    """Metadata stored with each vector."""
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
        """Convert to S3 Vectors metadata format (string values)."""
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
        """Parse from S3 Vectors metadata format."""
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
    """Interface to S3 Vectors for semantic storage and search."""

    def __init__(self, bucket: str, index: str, region: Optional[str] = None):
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
        """Store a vector with metadata."""
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

    def query(
        self,
        embedding: list[float],
        top_k: int = 10,
        filter: Optional[dict[str, Any]] = None
    ) -> list[dict]:
        """Query for similar vectors."""
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

    def update_metadata(self, key: str, metadata: VectorMetadata) -> bool:
        """Update metadata for an existing vector."""
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
        """Delete a vector by key."""
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
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/ai-zettelkasten && python -m pytest tests/test_s3vectors.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/ai_zettelkasten/s3vectors.py tests/test_s3vectors.py
git commit -m "feat: add s3vectors module for semantic storage"
```

---

## Task 5: Knowledge Extractor Service

**Files:**
- Create: `plugins/ai-zettelkasten/src/ai_zettelkasten/extractor.py`
- Create: `plugins/ai-zettelkasten/tests/test_extractor.py`

**Step 1: Write failing tests**

```python
"""Tests for knowledge extraction service."""
import pytest
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
            "confidence": 0.9
        }
        item = ExtractionItem.from_dict(d)
        assert item.knowledge_type == KnowledgeType.FACT
        assert item.title == "Test Fact"
        assert item.confidence == 0.9


class TestKnowledgeExtractor:
    def test_process_item_creates_note(self, tmp_path):
        with patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed, \
             patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store:

            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(
                vault_path=tmp_path,
                bucket="test",
                index="test"
            )

            item = ExtractionItem(
                knowledge_type=KnowledgeType.FACT,
                title="Test Fact",
                content="Test content",
                tags=["test"],
                confidence=0.85
            )

            result = extractor.process_item(item)

            assert result["status"] == "stored"
            assert result["obsidian_path"] is not None

    def test_process_items_batch(self, tmp_path):
        with patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed, \
             patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store:

            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.put_vector.return_value = True

            extractor = KnowledgeExtractor(
                vault_path=tmp_path,
                bucket="test",
                index="test"
            )

            items = [
                {"type": "fact", "title": "Fact 1", "content": "C1", "tags": [], "confidence": 0.8},
                {"type": "decision", "title": "Decision 1", "content": "C2", "tags": [], "confidence": 0.9},
            ]

            summary = extractor.process_items(items)

            assert summary["total"] == 2
            assert summary["stored"] == 2

    def test_find_related_notes(self, tmp_path):
        with patch("ai_zettelkasten.extractor.BedrockEmbeddings") as mock_embed, \
             patch("ai_zettelkasten.extractor.S3VectorsStore") as mock_store:

            mock_embed.return_value.embed.return_value = [0.1] * 1536
            mock_store.return_value.query.return_value = [
                {"key": "related-1", "distance": 0.2, "metadata": {"title": "Related Note"}}
            ]

            extractor = KnowledgeExtractor(
                vault_path=tmp_path,
                bucket="test",
                index="test"
            )

            related = extractor.find_related("Test query")

            assert len(related) == 1
            assert related[0]["key"] == "related-1"
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/ai-zettelkasten && python -m pytest tests/test_extractor.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write implementation**

```python
"""Knowledge extraction service - orchestrates note creation and storage."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .obsidian import ObsidianVault, Note, NoteType, KnowledgeType
from .embeddings import BedrockEmbeddings
from .s3vectors import S3VectorsStore, VectorMetadata


@dataclass
class ExtractionItem:
    """A single knowledge item to extract."""
    knowledge_type: KnowledgeType
    title: str
    content: str
    tags: list[str]
    confidence: float
    source_session: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "ExtractionItem":
        """Create from dictionary (JSON input)."""
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
    """Orchestrates knowledge extraction, storage, and retrieval."""

    def __init__(
        self,
        vault_path: Path,
        bucket: str,
        index: str,
        region: Optional[str] = None
    ):
        self.vault = ObsidianVault(vault_path)
        self.embeddings = BedrockEmbeddings(region)
        self.vectors = S3VectorsStore(bucket, index, region)

    def process_item(self, item: ExtractionItem) -> dict[str, Any]:
        """Process a single extraction item."""
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
                confidence=note.confidence,
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
        """Process multiple extraction items."""
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
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.75
    ) -> list[dict]:
        """Find notes related to a query."""
        embedding = self.embeddings.embed(query)
        results = self.vectors.query(embedding, top_k=top_k)

        # Filter by similarity threshold (distance < 1-threshold)
        filtered = [
            r for r in results
            if r.get("distance", 1.0) < (1 - threshold)
        ]

        return filtered
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/ai-zettelkasten && python -m pytest tests/test_extractor.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/ai_zettelkasten/extractor.py tests/test_extractor.py
git commit -m "feat: add knowledge extractor service"
```

---

## Task 6: CLI Entry Points

**Files:**
- Create: `plugins/ai-zettelkasten/src/ai_zettelkasten/cli.py`
- Modify: `plugins/ai-zettelkasten/hooks/extract-knowledge.py` (rewrite)

**Step 1: Write CLI module**

```python
"""CLI entry points for AI Zettelkasten."""
import json
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .extractor import KnowledgeExtractor


console = Console()

# Configuration from environment
BUCKET = os.environ.get("ZETTELKASTEN_BUCKET", "zettelkasten-prod")
INDEX = os.environ.get("ZETTELKASTEN_INDEX", "knowledge-index")
VAULT = Path(os.environ.get("OBSIDIAN_VAULT", os.path.expanduser("~/Documents/obsidian-vault-work")))


def extract_main():
    """Entry point for extraction hook."""
    # Check for stdin input
    if sys.stdin.isatty():
        console.print("[yellow]No input provided. Run with JSON on stdin.[/yellow]")
        return 0

    # Read and parse input
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            console.print("[yellow]Empty input.[/yellow]")
            return 0

        data = json.loads(input_data)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        return 1

    items = data.get("items", [])
    if not items:
        console.print("[dim]No items to extract.[/dim]")
        return 0

    # Process items
    extractor = KnowledgeExtractor(VAULT, BUCKET, INDEX)
    summary = extractor.process_items(items)

    # Display results
    console.print()
    table = Table(title="Extraction Results")
    table.add_column("Title", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")

    for result in summary["results"]:
        status_style = "green" if result["status"] == "stored" else "yellow"
        table.add_row(
            result["title"][:40],
            result["type"],
            f"[{status_style}]{result['status']}[/{status_style}]"
        )

    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] {summary['stored']} stored, {summary['partial']} partial, {summary['errors']} errors")

    return 0 if summary["errors"] == 0 else 1


def suggest_main():
    """Entry point for proactive suggestion hook."""
    # Placeholder for P1 implementation
    console.print("[dim]Proactive suggestions not yet implemented.[/dim]")
    return 0


if __name__ == "__main__":
    sys.exit(extract_main())
```

**Step 2: Update hooks/extract-knowledge.py**

```python
#!/usr/bin/env python3
"""AI Zettelkasten extraction hook - delegates to CLI."""
import subprocess
import sys

def main():
    # Use uvx to run with proper dependencies
    result = subprocess.run(
        ["uvx", "--from", "ai-zettelkasten", "zk-extract"],
        stdin=sys.stdin,
        capture_output=False
    )
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
```

**Step 3: Commit**

```bash
git add src/ai_zettelkasten/cli.py hooks/extract-knowledge.py
git commit -m "feat: add CLI entry points for hooks"
```

---

## Task 7: Skills - /zadd

**Files:**
- Modify: `plugins/ai-zettelkasten/skills/zadd/SKILL.md`

**Step 1: Write updated skill**

```markdown
---
name: ai-zettelkasten:zadd
description: |
  Manually add knowledge to the Zettelkasten. Use when you want to explicitly
  capture a fact, decision, pattern, or correction. Supports type flags and auto-tagging.
version: 2.0.0
---

# /zadd - Manually Add Knowledge

Manually add a piece of knowledge to the Zettelkasten.

## Usage

```
/zadd <content>
/zadd --type fact|decision|pattern|correction <content>
/zadd --tags "tag1,tag2" <content>
/zadd --project <name> <content>
```

## Implementation

When this skill is invoked:

1. **Parse arguments** from the command:
   - `--type` (default: auto-detect from content)
   - `--tags` (default: auto-generate)
   - `--project` (default: none, global scope)

2. **Auto-detect type** if not specified:
   - Contains "chose/decided/selected" → decision
   - Contains "always/never/pattern" → pattern
   - Contains "fixed/was wrong/actually" → correction
   - Default → fact

3. **Auto-generate tags** from content:
   - Extract technical terms (AWS, Python, etc.)
   - Extract domain concepts
   - Limit to 3-5 tags

4. **Create the note** using the extractor:

```python
from ai_zettelkasten.extractor import KnowledgeExtractor, ExtractionItem
from ai_zettelkasten.obsidian import KnowledgeType
from pathlib import Path
import os

extractor = KnowledgeExtractor(
    vault_path=Path(os.environ.get("OBSIDIAN_VAULT", "~/Documents/obsidian-vault-work")),
    bucket=os.environ.get("ZETTELKASTEN_BUCKET", "zettelkasten-prod"),
    index=os.environ.get("ZETTELKASTEN_INDEX", "knowledge-index")
)

item = ExtractionItem(
    knowledge_type=KnowledgeType.FACT,  # or detected type
    title=parsed_title,
    content=parsed_content,
    tags=parsed_tags,
    confidence=0.9  # High for manual adds
)

result = extractor.process_item(item)
```

5. **Find related notes** for linking suggestions:

```python
related = extractor.find_related(content, top_k=3)
```

6. **Report result**:

```
✅ Added to knowledge base:

Type: fact
Tags: aws, s3-vectors, limits
Path: knowledge-base/fleeting/s3-vectors-metadata-limits.md

📎 Related notes (link during /zreview):
  1. S3 Vectors Embedding Dimensions (0.82 similarity)
  2. S3 Vectors Setup Pattern (0.71 similarity)

Status: Pending review
```

## Examples

```
/zadd S3 Vectors has 50 metadata keys per vector
→ Type: fact, Tags: aws, s3-vectors, limits

/zadd --type decision Chose uvx over pip for hook dependencies
→ Type: decision, Tags: python, dependencies, hooks

/zadd --project omega The agent core uses interceptors for MCP
→ Type: fact, Tags: omega, mcp, architecture, Scope: project
```
```

**Step 2: Commit**

```bash
git add skills/zadd/SKILL.md
git commit -m "feat: update /zadd skill for v2"
```

---

## Task 8: Skills - /zreview

**Files:**
- Modify: `plugins/ai-zettelkasten/skills/zreview/SKILL.md`

**Step 1: Write updated skill**

```markdown
---
name: ai-zettelkasten:zreview
description: |
  Review and curate extracted knowledge. Approve, edit, or discard items
  from the review queue before they become permanent. Human-in-the-loop
  curation for quality control.
version: 2.0.0
---

# /zreview - Review Extracted Knowledge

Review and curate recently extracted knowledge. Approve, edit, or discard items before they're considered permanent.

## Usage

```
/zreview              # Review all pending
/zreview --today      # Today's extractions only
/zreview --type fact  # Filter by type
```

## Implementation

When this skill is invoked:

1. **Fetch pending notes** from the vault:

```python
from ai_zettelkasten.obsidian import ObsidianVault
from pathlib import Path
import os

vault = ObsidianVault(Path(os.environ.get("OBSIDIAN_VAULT")))
pending = vault.list_pending_notes()
```

2. **For each note**, display review interface:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Review Queue (1/5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**S3 Vectors Embedding Dimensions**
Type: fact | Confidence: 0.85
Tags: aws, s3-vectors, bedrock

> Bedrock Titan uses 1536 dimensions for embeddings.
> The S3 Vectors index must be created with dimension=1536.

📎 Suggested Links (similarity > 0.7):
  1. [[titan-embedding-models]] (0.82)
  2. [[s3-vectors-setup]] (0.74)

🏷️ Suggested Hub: hub-aws-serverless

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[a]pprove  [e]dit  [d]iscard  [s]kip  [l]ink  [q]uit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

3. **Handle actions**:

**[a]pprove:**
```python
# Promote note to permanent
permanent_path = vault.promote_note(fleeting_path)

# Create approved links
for link in approved_links:
    # Add bidirectional links
    pass

# Update S3 Vectors metadata
vectors.update_metadata(note.id, updated_metadata)

print(f"✅ Promoted to {permanent_path}")
```

**[e]dit:**
```python
# Open note content for editing
edited_content = get_user_edit(note.content)
edited_tags = get_user_edit(note.tags)

# Update note and re-save
note.content = edited_content
note.tags = edited_tags
vault.write_note(note)

# Re-embed with new content
new_embedding = embeddings.embed(f"{note.title}\n{note.content}")
vectors.update_vector(note.id, new_embedding, metadata)
```

**[d]iscard:**
```python
# Move to archive
archive_path = vault.root / "knowledge-base" / "fleeting" / ".archive"
archive_path.mkdir(exist_ok=True)
shutil.move(fleeting_path, archive_path / fleeting_path.name)

# Remove from S3 Vectors
vectors.delete_vector(note.id)

print("🗑️ Moved to archive")
```

**[l]ink:**
```python
# Show all notes for manual linking
all_notes = vault.list_all_notes()
# User selects which to link
selected = user_select_notes(all_notes)
# Add to note's links
note.links.extend(selected)
```

4. **After all reviews**, show summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Review Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Approved: 3
📝 Edited: 1
🗑️ Discarded: 1
⏭️ Skipped: 0

New permanent notes:
  • permanent/s3-vectors-dimensions.md
  • permanent/chose-uvx-for-hooks.md
  • permanent/mermaid-diagrams-pattern.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
```

**Step 2: Commit**

```bash
git add skills/zreview/SKILL.md
git commit -m "feat: update /zreview skill for v2"
```

---

## Task 9: Skills - /zsearch

**Files:**
- Modify: `plugins/ai-zettelkasten/skills/zsearch/SKILL.md`

**Step 1: Write updated skill**

```markdown
---
name: ai-zettelkasten:zsearch
description: |
  Semantic search across your knowledge base. Find relevant facts, decisions,
  patterns, and corrections using natural language queries.
version: 2.0.0
---

# /zsearch - Semantic Knowledge Search

Search your knowledge base using natural language.

## Usage

```
/zsearch <query>
/zsearch <query> --type fact|decision|pattern|correction
/zsearch <query> --project <name>
/zsearch <query> --recent 7d
/zsearch <query> --hub <hub-name>
```

## Implementation

When this skill is invoked:

1. **Parse query and filters**:

```python
query = parsed_args.query
filters = {}
if parsed_args.type:
    filters["knowledge_type"] = parsed_args.type
if parsed_args.project:
    filters["project"] = parsed_args.project
```

2. **Generate embedding and search**:

```python
from ai_zettelkasten.extractor import KnowledgeExtractor

extractor = KnowledgeExtractor(vault_path, bucket, index)
results = extractor.vectors.query(
    extractor.embeddings.embed(query),
    top_k=10,
    filter=filters
)
```

3. **Display results** ranked by similarity:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Search: "S3 Vectors setup"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. [0.92] S3 Vectors Embedding Dimensions
   Type: fact | Tags: aws, s3-vectors, bedrock
   "Bedrock Titan uses 1536 dimensions..."
   📄 permanent/s3-vectors-dimensions.md

2. [0.85] Chose S3 Vectors over Aurora
   Type: decision | Tags: architecture, aws
   "Decided on S3 Vectors for simplicity..."
   📄 permanent/chose-s3-vectors.md

3. [0.78] S3 Vectors Setup Pattern
   Type: pattern | Tags: aws, infrastructure
   "Always create index before bucket..."
   📄 permanent/s3-vectors-setup.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 results | Showing top matches (similarity > 0.7)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

4. **Offer actions**:

```
[1-3] Open note  [r] Refine search  [q] Quit
```

## Examples

```
/zsearch lambda cold starts
→ Finds notes about Lambda performance

/zsearch --type decision database choice
→ Finds decision notes about databases

/zsearch --project omega interceptor pattern
→ Finds project-specific notes
```
```

**Step 2: Commit**

```bash
git add skills/zsearch/SKILL.md
git commit -m "feat: update /zsearch skill for v2"
```

---

## Task 10: Update Plugin Configuration

**Files:**
- Modify: `plugins/ai-zettelkasten/.claude-plugin/plugin.json`

**Step 1: Write updated plugin.json**

```json
{
  "name": "ai-zettelkasten",
  "version": "2.0.0",
  "description": "True Zettelkasten for Claude Code - atomic notes, semantic search, and automatic hubs",
  "author": {
    "name": "cajias"
  },
  "license": "MIT",
  "keywords": [
    "zettelkasten",
    "knowledge-management",
    "obsidian",
    "s3-vectors",
    "semantic-search",
    "memory"
  ],
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uvx --from ai-zettelkasten zk-extract"
          }
        ]
      }
    ]
  }
}
```

**Step 2: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: update plugin config for v2"
```

---

## Task 11: Integration Test

**Files:**
- Create: `plugins/ai-zettelkasten/tests/test_integration.py`

**Step 1: Write integration test**

```python
"""Integration tests for AI Zettelkasten."""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_zettelkasten.extractor import KnowledgeExtractor
from ai_zettelkasten.obsidian import ObsidianVault, NoteType


class TestEndToEnd:
    """End-to-end workflow tests."""

    def test_extract_review_search_workflow(self, tmp_path):
        """Test complete workflow: extract → review → search."""
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
```

**Step 2: Run tests**

Run: `cd plugins/ai-zettelkasten && python -m pytest tests/ -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for complete workflow"
```

---

## Task 12: Final Cleanup and Documentation

**Files:**
- Modify: `plugins/ai-zettelkasten/README.md`

**Step 1: Update README**

```markdown
# AI Zettelkasten v2.0

True Zettelkasten methodology for Claude Code - atomic notes, semantic search, automatic hubs.

## Features

- **Atomic Notes** - One idea per note, proper lifecycle (fleeting → permanent)
- **Semantic Search** - Find knowledge by meaning, not keywords
- **Auto-Linking** - Suggested connections based on similarity
- **Hub Generation** - Auto-clustered topic notes
- **Proactive Capture** - Suggestions to save knowledge mid-conversation

## Quick Start

```bash
# Install plugin
claude plugin install ai-zettelkasten@personal-skills

# Set environment
export ZETTELKASTEN_BUCKET=your-bucket
export ZETTELKASTEN_INDEX=knowledge-index
export OBSIDIAN_VAULT=~/Documents/obsidian-vault-work
```

## Skills

| Skill | Description |
|-------|-------------|
| `/zadd` | Manually capture knowledge |
| `/zreview` | Review and approve extractions |
| `/zsearch` | Semantic search |
| `/zhubs` | Browse topic clusters (P1) |

## Architecture

```
knowledge-base/
├── fleeting/     # Pending review
├── permanent/    # Approved notes
├── hubs/         # Auto-generated clusters
└── projects/     # Project-scoped notes
```

## Development

```bash
cd plugins/ai-zettelkasten
pip install -e ".[dev]"
pytest tests/ -v
```
```

**Step 2: Final commit**

```bash
git add README.md
git commit -m "docs: update README for v2"
```

**Step 3: Push branch**

```bash
git push -u origin feature/ai-zettelkasten-v2
```

---

## Summary

| Task | Component | Status |
|------|-----------|--------|
| 1 | Project structure | Pending |
| 2 | Obsidian module | Pending |
| 3 | Embeddings module | Pending |
| 4 | S3 Vectors module | Pending |
| 5 | Extractor service | Pending |
| 6 | CLI entry points | Pending |
| 7 | /zadd skill | Pending |
| 8 | /zreview skill | Pending |
| 9 | /zsearch skill | Pending |
| 10 | Plugin config | Pending |
| 11 | Integration tests | Pending |
| 12 | Documentation | Pending |

**Total: 12 tasks for P0 implementation**
