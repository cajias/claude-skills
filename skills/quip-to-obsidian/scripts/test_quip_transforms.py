#!/usr/bin/env python3
"""Regression tests for the quip-to-obsidian transform scripts.

Standalone skill: no pyproject, no uv. Run with the system pytest:

    python3 -m pytest skills/quip-to-obsidian/scripts/test_quip_transforms.py -v

Each test drives the real script as a subprocess (python3 <script> <args>) over
a throwaway tmp_path directory, exactly as the skill invokes it in production.
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
FIX_TABLES = SCRIPTS_DIR / "fix-quip-tables.py"
FIX_IMAGES = SCRIPTS_DIR / "fix-obsidian-images.py"


def _count_blank_lines(text: str) -> int:
    """Count blank (empty / whitespace-only) lines, split the same way both
    before and after so the comparison is apples-to-apples."""
    return sum(1 for line in text.split("\n") if line.strip() == "")


def _run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
    )


def test_fix_tables_preserves_blank_lines(tmp_path):
    """The fix removes only empty *table* rows (||||) and must NOT eat genuine
    paragraph-separating blank lines (the pre-fix bug deleted every blank line)."""
    # Table block + one pipe-only empty row, then 3 genuine blank lines between
    # paragraphs. No trailing newline so the blank count is unambiguously 3.
    content = (
        "Para A.\n"
        "| H1 | H2 |\n"
        "|---|---|\n"
        "| x | y |\n"
        "||||\n"  # empty table row: must be removed
        "Para B.\n"
        "\n"
        "\n"
        "\n"
        "Para C."
    )
    md = tmp_path / "doc.md"
    md.write_text(content, encoding="utf-8")

    before = _count_blank_lines(content)
    assert before == 3, "fixture should start with exactly 3 blank lines"

    result = _run(FIX_TABLES, str(tmp_path))
    assert result.returncode == 0, result.stderr

    after_text = md.read_text(encoding="utf-8")
    after = _count_blank_lines(after_text)

    # Regression: blank-line count unchanged (3 before, 3 after).
    assert after == before == 3, f"blank lines changed: {before} -> {after}"
    # The pipe-only empty row is gone.
    assert "||||" not in after_text
    # Sanity: the genuine table header survived.
    assert "| H1 | H2 |" in after_text


def test_fix_tables_keeps_documented_row_number_strip(tmp_path):
    """Guard against over-correcting the previous fix: the documented behavior of
    stripping a leading row-number column (|1|Cell| -> |Cell|) must still work."""
    content = "| Col |\n|---|\n|1|Cell|"
    md = tmp_path / "numbered.md"
    md.write_text(content, encoding="utf-8")

    result = _run(FIX_TABLES, str(tmp_path))
    assert result.returncode == 0, result.stderr

    after_text = md.read_text(encoding="utf-8")
    assert "|Cell|" in after_text, "documented |1|Cell| -> |Cell| strip regressed"
    assert "|1|Cell|" not in after_text


def test_fix_images_leaves_github_urls(tmp_path):
    """Genuine Quip /blob/THREAD/BLOB refs convert to attachment paths with the
    correct THREAD_BLOB ordering; code-host /blob/ URLs (github, gitlab /-/blob/)
    are left byte-for-byte unchanged."""
    github_url = "https://github.com/org/repo/blob/main/src/app.py"
    gitlab_url = "https://gitlab.com/g/p/-/blob/main/f.py"
    content = (
        "See ![x][1]\n"
        "\n"
        "[1]: /blob/ABC123/xyz_1\n"
        "\n"
        f"Code: {github_url}\n"
        "\n"
        f"GL: {gitlab_url}\n"
    )
    md = tmp_path / "images.md"
    md.write_text(content, encoding="utf-8")

    result = _run(FIX_IMAGES, "--directory", str(tmp_path))
    assert result.returncode == 0, result.stderr

    after_text = md.read_text(encoding="utf-8")

    # Code-host URLs untouched.
    assert github_url in after_text, "GitHub /blob/ URL was wrongly rewritten"
    assert gitlab_url in after_text, "GitLab /-/blob/ URL was wrongly rewritten"

    # Quip ref converted with correct thread_blob ordering (THREAD then BLOB).
    assert "ABC123_xyz_1.png" in after_text, "Quip /blob/ ref did not convert"
    # The reversed (buggy) ordering would yield xyz_1_ABC123 -> contains _ABC123.
    assert "_ABC123" not in after_text, "thread/blob ordering is reversed"
