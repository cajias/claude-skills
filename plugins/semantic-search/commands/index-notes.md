---
name: index-notes
description: Re-index all Obsidian vault notes into the semantic search database
---

# /index-notes

Re-index all Zettelkasten notes for semantic search.

## Steps

1. Run the indexer:

   ```bash
   uv run --project ${CLAUDE_PLUGIN_ROOT} ss-index
   ```

2. Report how many notes were indexed
3. Confirm the index is ready for search
