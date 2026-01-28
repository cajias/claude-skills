---
name: zsearch
description: |
  Semantic search across your knowledge base. Find relevant facts, decisions,
  patterns, and corrections using natural language queries.
version: 2.0.0
---

# /zsearch - Semantic Knowledge Search

Search your knowledge base using natural language.

## Usage

```
/zsearch <query>
/zsearch <query> --type fact|decision|pattern|correction
/zsearch <query> --project <name>
/zsearch <query> --recent 7d
/zsearch <query> --hub <hub-name>
```

## Implementation

When this skill is invoked:

1. **Parse query and filters**:

```python
query = parsed_args.query
filters = {}
if parsed_args.type:
    filters["knowledge_type"] = parsed_args.type
if parsed_args.project:
    filters["project"] = parsed_args.project
```

2. **Generate embedding and search**:

```python
from ai_zettelkasten.extractor import KnowledgeExtractor

extractor = KnowledgeExtractor(vault_path, bucket, index)
results = extractor.vectors.query(
    extractor.embeddings.embed(query),
    top_k=10,
    filter=filters
)
```

3. **Display results** ranked by similarity:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Search: "S3 Vectors setup"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. [0.92] S3 Vectors Embedding Dimensions
   Type: fact | Tags: aws, s3-vectors, bedrock
   "Bedrock Titan uses 1536 dimensions..."
   📄 permanent/s3-vectors-dimensions.md

2. [0.85] Chose S3 Vectors over Aurora
   Type: decision | Tags: architecture, aws
   "Decided on S3 Vectors for simplicity..."
   📄 permanent/chose-s3-vectors.md

3. [0.78] S3 Vectors Setup Pattern
   Type: pattern | Tags: aws, infrastructure
   "Always create index before bucket..."
   📄 permanent/s3-vectors-setup.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 results | Showing top matches (similarity > 0.7)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

4. **Offer actions**:

```
[1-3] Open note  [r] Refine search  [q] Quit
```

## Examples

```
/zsearch lambda cold starts
→ Finds notes about Lambda performance

/zsearch --type decision database choice
→ Finds decision notes about databases

/zsearch --project omega interceptor pattern
→ Finds project-specific notes
```
