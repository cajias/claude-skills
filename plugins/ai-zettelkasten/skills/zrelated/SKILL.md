---
name: zrelated
description: Find semantically related notes for a given query or note ID to suggest links
---

# /zrelated - Find Related Notes

Discover semantically related notes to help build connections in your knowledge base.

## Usage

```text
/zrelated context management        # Search by query
/zrelated perm-fact-my-note-id      # Search by note ID
/zrelated "TDD patterns" --top 15   # Custom number of results
```

## Implementation

Run the related notes command with proper AWS credentials:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
uvx --from ${CLAUDE_PLUGIN_ROOT} zk-related "your query here"
'
```

## What It Does

1. Takes a query string or note ID as input
2. If note ID: retrieves existing embedding from S3 Vectors
3. If query: generates embedding via Bedrock Titan
4. Queries S3 Vectors for top-k most similar notes
5. Returns notes ranked by semantic similarity

## Use Cases

### 1. Find Notes to Link

When writing or reviewing a note, find related content to link:

```text
/zrelated "AWS Lambda optimization"
# Returns notes about Lambda, serverless, performance
```

### 2. Expand Note Context

Find notes that should reference a specific note:

```text
/zrelated perm-fact-context-management
# Returns notes that should link to this one
```

### 3. Research a Topic

Explore what you know about a subject:

```text
/zrelated "authentication patterns"
# Discovers all related knowledge across hubs
```

## Output Legend

- ★ = permanent note (validated knowledge)
- ○ = fleeting note (pending review)
- Percentage: Cosine similarity score (higher = more related)
- Tags: Note tags for quick categorization
- Preview: First 60 characters of content

## Tips

- Use note IDs (perm-_, fleet-_) for precise searches from a known note
- Use natural language queries for exploratory searches
- Higher --top values useful for broadly applicable topics
- Results can inform `## Related` section in notes
