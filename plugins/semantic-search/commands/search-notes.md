---
name: search-notes
description: Search Zettelkasten notes by meaning using semantic similarity
args:
  - name: query
    description: What to search for
    required: true
---

# /search-notes

Search your knowledge base using semantic similarity.

## Steps

1. Run the search:

   ```bash
   uv run --project /Users/rc/Projects/workspace/claude-skills/plugins/semantic-search ss-search "$QUERY" --limit 5
   ```

2. Parse the JSON output
3. For the top 2-3 results, read the full note using `mcp__obsidian__read_note`
4. Summarize the relevant findings for the user, linking back to note titles
