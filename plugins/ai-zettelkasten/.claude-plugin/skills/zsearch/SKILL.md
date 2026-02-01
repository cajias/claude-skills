---
name: ai-zettelkasten:zsearch
description: |
  Semantic search across your knowledge base. Use when asking "What do I know about X?"
  or searching for facts, decisions, patterns from past sessions. Searches S3 Vectors
  with Bedrock embeddings, falls back to Obsidian if not configured.
version: 0.2.0
---

# /zsearch - Semantic Knowledge Search

Search your knowledge base using natural language. Finds relevant facts, decisions, patterns, and corrections from past sessions.

## Usage

```text
/zsearch <query>
/zsearch <query> --type fact|decision|pattern|correction
/zsearch <query> --since 7d
```

## Examples

- `/zsearch How does S3 Vectors work?`
- `/zsearch AWS architecture decisions --type decision`
- `/zsearch Claude Code hooks --since 30d`

## Implementation

When this skill is invoked:

1. **Parse the query and filters** from the arguments

2. **Search S3 Vectors** using AWS CLI:

```bash
# Generate embedding for query
EMBEDDING=$(aws bedrock-runtime invoke-model \
  --model-id amazon.titan-embed-text-v1 \
  --body "{\"inputText\": \"$QUERY\"}" \
  --query 'embedding' --output json)

# Query S3 Vectors
aws s3vectors query-vectors \
  --vector-bucket-name zettelkasten-prod \
  --index-name knowledge-index \
  --top-k 10 \
  --query-vector "$EMBEDDING" \
  --filter '{"type": {"$eq": "'"$TYPE"'"}}' \
  --return-metadata \
  --return-distance
```

1. **Format and display results** ranked by relevance:

```text
📚 Search Results for: "How does S3 Vectors work?"

1. [0.24] S3 Vectors Configuration (fact)
   S3 Vectors uses 1536 dimensions with Bedrock Titan...
   Tags: aws, s3-vectors, embeddings

1. [0.39] Chose S3 Vectors over Aurora (decision)
   Decided on S3 Vectors for simplicity and cost...
   Tags: architecture, aws
```

1. **If S3 Vectors not configured**, fall back to Obsidian search:

```bash
# Search Obsidian extractions
mcp__obsidian__search_notes --query "$QUERY" --limit 10
```

## Configuration

Requires environment variables:

- `ZETTELKASTEN_BUCKET`: S3 Vectors bucket name
- `ZETTELKASTEN_INDEX`: Index name (default: knowledge-index)

Or falls back to Obsidian-only mode if not configured.
