---
name: zorphans
description: Find notes that don't fit well into any semantic cluster (isolated notes)
---

# /zorphans - Find Orphan Notes

Discover notes that are semantically isolated and don't have strong connections to other notes in the knowledge base.

## Usage

```text
/zorphans                    # Default 50% max similarity threshold
/zorphans --threshold 40     # Find more isolated notes
/zorphans --threshold 60     # Only find truly disconnected notes
```

## Implementation

Run the orphan detection command with proper AWS credentials:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
uvx --from /Users/cajias/.claude/my-claude-skills/plugins/ai-zettelkasten zk-orphans --threshold 50
'
```

## What It Does

1. Fetches all vectors with embeddings from S3 Vectors
2. For each note, queries the top 6 most similar notes
3. Calculates max and average similarity scores (excluding self)
4. Reports notes where max similarity is below threshold

## When to Use

- Identify knowledge gaps in specific areas
- Find notes that may need more context or links
- Discover topics that could become new hub seeds
- Clean up disconnected or outdated knowledge

## Interpreting Results

| Similarity | Meaning                                               |
| ---------- | ----------------------------------------------------- |
| < 30%      | Completely isolated - unique topic or needs deletion  |
| 30-40%     | Very weak connections - consider expanding or linking |
| 40-50%     | Loosely connected - may need more related notes       |
| > 50%      | Well connected - probably not an orphan               |

## Output Legend

- ★ = permanent note (validated knowledge)
- ○ = fleeting note (pending review)
- Max similarity: Highest similarity to any other note
- Avg similarity: Average similarity to nearest neighbors
