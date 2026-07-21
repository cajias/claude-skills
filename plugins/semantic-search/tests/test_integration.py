"""Integration tests: index real-ish notes, search, verify results."""

import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def vault_and_db(tmp_path):
    """Create a temp vault with sample notes and a temp db path."""
    vault = tmp_path / "vault"
    vault.mkdir()
    db = tmp_path / "lancedb"

    # Regular notes
    (vault / "Zettelkasten").mkdir()
    (vault / "Zettelkasten" / "Sauna Protocols for Longevity.md").write_text(
        "Cold plunge after sauna improves cardiovascular health and recovery.",
    )
    (vault / "Zettelkasten" / "Vitamin D and Immune Function.md").write_text(
        "Vitamin D supplementation supports immune system function and bone health.",
    )
    (vault / "Zettelkasten" / "Python Async Patterns.md").write_text(
        "Use asyncio.gather for concurrent coroutines in Python applications.",
    )
    (vault / "Inbox").mkdir()
    (vault / "Inbox" / "Quick Idea.md").write_text(
        "Explore the connection between sleep and memory consolidation.",
    )

    # MOC files (should be skipped)
    (vault / "Zettelkasten" / "MOC - Health.md").write_text(
        "# Health\n- [[Sauna Protocols]]\n- [[Vitamin D]]",
    )
    (vault / "Zettelkasten" / "MOC - Index.md").write_text(
        "# Index\n- [[MOC - Health]]",
    )

    # Non-md file (should be skipped)
    (vault / "Zettelkasten" / "image.png").write_bytes(b"\x89PNG")

    env = {
        **os.environ,
        "SEMANTIC_SEARCH_VAULT_PATH": str(vault),
        "SEMANTIC_SEARCH_DB_PATH": str(db),
    }
    return vault, db, env


def _run_cmd(cmd, env):
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(Path.cwd()),
        check=False,
    )


def test_index_then_search(vault_and_db):
    _vault, _db, env = vault_and_db

    # Index
    r = _run_cmd(["uv", "run", "ss-index"], env)
    assert r.returncode == 0
    assert "Indexed 4 notes" in r.stdout

    # Search for health-related content
    r = _run_cmd(["uv", "run", "ss-search", "immune system vitamins"], env)
    assert r.returncode == 0
    results = json.loads(r.stdout)
    assert len(results) > 0
    # Vitamin D note should be the top result
    assert results[0]["title"] == "Vitamin D and Immune Function"


def test_index_then_status(vault_and_db):
    _, _, env = vault_and_db

    r = _run_cmd(["uv", "run", "ss-index"], env)
    assert r.returncode == 0

    r = _run_cmd(["uv", "run", "ss-status"], env)
    assert r.returncode == 0
    assert "4 notes indexed" in r.stdout


def test_reindex_is_idempotent(vault_and_db):
    _, _, env = vault_and_db

    # First index
    r = _run_cmd(["uv", "run", "ss-index"], env)
    assert r.returncode == 0
    assert "Indexed 4 notes" in r.stdout

    # Second index must replace, not append
    r = _run_cmd(["uv", "run", "ss-index"], env)
    assert r.returncode == 0
    assert "Indexed 4 notes" in r.stdout

    # Status still reports 4, not 8
    r = _run_cmd(["uv", "run", "ss-status"], env)
    assert r.returncode == 0
    assert "4 notes indexed" in r.stdout


def test_search_with_limit(vault_and_db):
    _, _, env = vault_and_db

    _run_cmd(["uv", "run", "ss-index"], env)

    r = _run_cmd(["uv", "run", "ss-search", "health", "--limit", "2"], env)
    assert r.returncode == 0
    results = json.loads(r.stdout)
    assert len(results) == 2


def test_search_no_query_fails(vault_and_db):
    _, _, env = vault_and_db

    r = _run_cmd(["uv", "run", "ss-search"], env)
    assert r.returncode != 0


def test_search_limit_missing_or_bad_value(vault_and_db):
    _, _, env = vault_and_db

    # Index first so the happy-path assertion has data to return.
    # The guard fires during arg-parse (before DB access), but keep it realistic.
    _run_cmd(["uv", "run", "ss-index"], env)

    # --limit with no value must exit cleanly with usage, not an IndexError traceback.
    r = _run_cmd(["uv", "run", "ss-search", "health", "--limit"], env)
    assert r.returncode == 1
    assert "Usage" in r.stderr
    assert "Traceback" not in r.stderr

    # --limit with a non-numeric value must exit cleanly with usage, not a ValueError traceback.
    r = _run_cmd(["uv", "run", "ss-search", "health", "--limit", "abc"], env)
    assert r.returncode == 1
    assert "Usage" in r.stderr
    assert "Traceback" not in r.stderr

    # Happy path: a valid --limit still works, so the guard did not break valid usage.
    r = _run_cmd(["uv", "run", "ss-search", "health", "--limit", "2"], env)
    assert r.returncode == 0


def test_mocs_not_indexed(vault_and_db):
    _, _, env = vault_and_db

    _run_cmd(["uv", "run", "ss-index"], env)

    # Search for MOC content — should not find MOC files
    r = _run_cmd(["uv", "run", "ss-search", "Index Health MOC"], env)
    results = json.loads(r.stdout)
    titles = [result["title"] for result in results]
    assert "MOC - Health" not in titles
    assert "MOC - Index" not in titles
