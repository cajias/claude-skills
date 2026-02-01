---
name: zdupes
description: Find duplicate or highly similar notes in the knowledge base using semantic search
---

# /zdupes - Find Duplicate Notes

Scan S3 Vectors for semantically similar notes that might be duplicates or candidates for consolidation.

## Usage

```text
/zdupes                    # Default 85% threshold
/zdupes --threshold 90     # Custom threshold
```

## Implementation

Run the duplicate detection command with proper AWS credentials:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
uvx --from /Users/cajias/.claude/my-claude-skills/plugins/ai-zettelkasten zk-dupes --threshold 85
'
```

## What It Does

1. Fetches all vectors from S3 Vectors
2. For each vector, queries for similar vectors
3. Reports pairs above the similarity threshold
4. Groups results by similarity level (99%+, 95-99%, 90-95%, 85-90%)

## When to Use

- After bulk imports to find accidental duplicates
- Periodically to consolidate similar knowledge
- When knowledge base feels bloated
- Before major reorganization

## Interpreting Results

| Similarity | Meaning                                           |
| ---------- | ------------------------------------------------- |
| 99%+       | Near-exact duplicates - consolidate or delete one |
| 95-99%     | Very similar - review for redundancy              |
| 90-95%     | Related topics - consider linking                 |
| 85-90%     | Thematically connected - may belong in same hub   |
