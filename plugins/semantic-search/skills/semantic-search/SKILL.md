---
name: semantic-search
description: |
  Semantic search over Obsidian Zettelkasten notes. Use when the user asks
  "What do I know about X?", "Find notes about...", or wants to search their
  knowledge base by meaning rather than exact keywords.
version: 0.1.0
---

# Semantic Search

Search your Obsidian Zettelkasten using semantic similarity (vector embeddings).

## Commands

- `/index-notes` — Re-index all vault notes into LanceDB
- `/search-notes <query>` — Search notes by meaning

## How It Works

Notes are embedded with `all-MiniLM-L6-v2` (local, no API calls) and stored
in LanceDB (embedded, serverless, stored in vault `.lancedb/`).

## When to Use

- User asks "what do I know about X?"
- User wants to find related notes on a topic
- User asks to search their knowledge base

## Implementation

When this skill is invoked:

1. Run the search command with appropriate env vars:
   `uv run --project ${CLAUDE_PLUGIN_ROOT} ss-search "<query>"`
2. Parse JSON results
3. Read top 2-3 matching notes using Obsidian MCP tools
4. Summarize findings for the user

### Environment Variables

| Var                          | Default                      |
| ---------------------------- | ---------------------------- |
| `SEMANTIC_SEARCH_VAULT_PATH` | `~/Documents/Obsidian Vault` |
| `SEMANTIC_SEARCH_DB_PATH`    | `<vault>/.lancedb`           |
