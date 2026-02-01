"""Note loader for Obsidian vault."""

from pathlib import Path


def load_notes(vault_path: str) -> list[dict]:
    """Load all non-MOC markdown notes from vault_path.

    Returns list of dicts with keys: title, content, source.
    """
    root = Path(vault_path)
    notes = []

    for path in root.rglob("*.md"):
        # Skip hidden files/dirs
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue

        # Skip MOC files
        if path.name.startswith("MOC -") or path.name.startswith("MOC - "):
            continue

        notes.append(
            {
                "title": path.stem,
                "content": path.read_text(),
                "source": str(path.relative_to(root)),
            },
        )

    return notes
