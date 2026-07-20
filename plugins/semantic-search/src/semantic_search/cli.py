"""CLI entry points for semantic search."""

import json
import os
import sys
from pathlib import Path

from semantic_search.db import add_documents, get_table, search
from semantic_search.notes import load_notes


DEFAULT_VAULT = str(Path.home() / "Documents" / "Obsidian Vault")


def _vault_path() -> str:
    return os.environ.get("SEMANTIC_SEARCH_VAULT_PATH", DEFAULT_VAULT)


def _db_path() -> str:
    return os.environ.get("SEMANTIC_SEARCH_DB_PATH", str(Path(_vault_path()) / ".lancedb"))


def index_cmd() -> None:
    """Index all notes from vault into LanceDB."""
    vault_path = _vault_path()
    db_path = _db_path()

    notes = load_notes(vault_path)
    table = get_table(db_path)
    count = add_documents(table, notes)
    print(f"Indexed {count} notes")


def search_cmd() -> None:
    """Search notes by semantic similarity."""
    db_path = _db_path()

    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print("Usage: ss-search <query> [--limit N]", file=sys.stderr)
        sys.exit(1)

    query = args[0]
    limit = 5
    if "--limit" in args:
        idx = args.index("--limit")
        limit = int(args[idx + 1])

    table = get_table(db_path)
    results = search(table, query, limit=limit)
    print(json.dumps(results, indent=2))


def status_cmd() -> None:
    """Show index status."""
    db_path = _db_path()

    table = get_table(db_path)
    count = table.count_rows()
    print(f"{count} notes indexed")
