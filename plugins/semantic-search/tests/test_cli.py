"""Tests for cli.py."""

import json
import os
import subprocess

import pytest


PROJECT_DIR = "/Users/rc/Projects/workspace/claude-skills/plugins/semantic-search"


@pytest.fixture
def vault_and_db(tmp_path):
    """Create a temp vault with 2 markdown files and a db path."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Note One.md").write_text("# Note One\nThis is about Python programming.")
    (vault / "Note Two.md").write_text("# Note Two\nThis is about machine learning.")
    db_path = tmp_path / "lancedb"
    return str(vault), str(db_path)


def _env(vault_path: str, db_path: str) -> dict:
    env = os.environ.copy()
    env["SEMANTIC_SEARCH_VAULT_PATH"] = vault_path
    env["SEMANTIC_SEARCH_DB_PATH"] = db_path
    return env


def test_index_cmd(vault_and_db):
    vault_path, db_path = vault_and_db
    result = subprocess.run(
        ["uv", "run", "ss-index"],
        capture_output=True,
        text=True,
        env=_env(vault_path, db_path),
        cwd=PROJECT_DIR,
        check=False,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "Indexed 2 notes" in result.stdout


def test_search_cmd(vault_and_db):
    vault_path, db_path = vault_and_db
    env = _env(vault_path, db_path)

    # Index first
    subprocess.run(["uv", "run", "ss-index"], env=env, cwd=PROJECT_DIR, capture_output=True, check=False)

    # Search
    result = subprocess.run(
        ["uv", "run", "ss-search", "Python"],
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_DIR,
        check=False,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert isinstance(data, list)


def test_status_cmd(vault_and_db):
    vault_path, db_path = vault_and_db
    env = _env(vault_path, db_path)

    # Index first
    subprocess.run(["uv", "run", "ss-index"], env=env, cwd=PROJECT_DIR, capture_output=True, check=False)

    # Status
    result = subprocess.run(
        ["uv", "run", "ss-status"],
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_DIR,
        check=False,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "2 notes" in result.stdout


def test_search_no_query_fails(vault_and_db):
    vault_path, db_path = vault_and_db
    result = subprocess.run(
        ["uv", "run", "ss-search"],
        capture_output=True,
        text=True,
        env=_env(vault_path, db_path),
        cwd=PROJECT_DIR,
        check=False,
    )
    assert result.returncode != 0
