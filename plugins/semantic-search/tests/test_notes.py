"""Tests for notes.py."""

import tempfile
from pathlib import Path

from semantic_search.notes import load_notes


def _write(path: Path, content: str = "some content"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_load_notes_from_directory():
    with tempfile.TemporaryDirectory() as tmp:
        _write(Path(tmp) / "First Note.md", "Hello")
        _write(Path(tmp) / "Second Note.md", "World")

        notes = load_notes(tmp)

        assert len(notes) == 2
        titles = {n["title"] for n in notes}
        assert titles == {"First Note", "Second Note"}
        for n in notes:
            assert set(n.keys()) == {"title", "content", "source"}
            assert n["content"] in ("Hello", "World")
            assert n["source"].endswith(".md")


def test_moc_files_excluded():
    with tempfile.TemporaryDirectory() as tmp:
        _write(Path(tmp) / "MOC - Health.md", "moc stuff")
        _write(Path(tmp) / "Regular Note.md", "real note")

        notes = load_notes(tmp)

        assert len(notes) == 1
        assert notes[0]["title"] == "Regular Note"


def test_empty_vault():
    with tempfile.TemporaryDirectory() as tmp:
        assert load_notes(tmp) == []


def test_nested_directories():
    with tempfile.TemporaryDirectory() as tmp:
        _write(Path(tmp) / "Zettelkasten" / "Deep Note.md", "deep")

        notes = load_notes(tmp)

        assert len(notes) == 1
        assert notes[0]["title"] == "Deep Note"
        assert notes[0]["source"] == str(Path("Zettelkasten") / "Deep Note.md")


def test_non_md_files_ignored():
    with tempfile.TemporaryDirectory() as tmp:
        _write(Path(tmp) / "note.md", "yes")
        _write(Path(tmp) / "readme.txt", "no")
        _write(Path(tmp) / "image.png", "no")

        notes = load_notes(tmp)

        assert len(notes) == 1
        assert notes[0]["title"] == "note"
