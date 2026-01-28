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
