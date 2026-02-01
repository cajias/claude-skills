# semantic-search plugin

Semantic search over Obsidian Zettelkasten notes using LanceDB + sentence-transformers.

## Development

```bash
cd /Users/rc/Projects/workspace/claude-skills/plugins/semantic-search
uv sync
uv run pytest -v         # run tests
uv run ruff check src/ tests/  # lint
```

## CLI Commands

- `ss-index` — Index vault notes into LanceDB
- `ss-search <query>` — Search by meaning, returns JSON
- `ss-status` — Show index count

## Environment Variables

- `SEMANTIC_SEARCH_VAULT_PATH` — Vault root (default: `/Users/rc/Documents/Obsidian Vault`)
- `SEMANTIC_SEARCH_DB_PATH` — LanceDB dir (default: `/Users/rc/Documents/Obsidian Vault/.lancedb`)
