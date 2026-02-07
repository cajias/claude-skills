---
name: zcluster
description: Find semantic clusters in the knowledge base to validate hub organization
---

# /zcluster - Find Semantic Clusters

Analyze S3 Vectors to discover natural semantic clusters in your knowledge base. Useful for validating hub organization
or discovering new hub candidates.

## Usage

```text
/zcluster                              # Use default seed patterns
/zcluster --seeds "api,auth,cache"     # Custom seed patterns
```

## Implementation

Run the clustering command with proper AWS credentials:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
uvx --from ${CLAUDE_PLUGIN_ROOT} zk-cluster
'
```

## What It Does

1. Fetches all vectors from S3 Vectors
2. For each seed pattern, finds the most representative note
3. Queries for semantically similar notes (cluster members)
4. Displays clusters with similarity scores

## Default Seed Patterns

- context → CONTEXT MANAGEMENT
- tdd → TDD & TESTING
- phase → SDLC PHASES
- workflow → WORKFLOWS
- infrastructure → INFRASTRUCTURE
- knowledge → KNOWLEDGE MANAGEMENT
- lint → CODE QUALITY
- security → SECURITY

## When to Use

- Validate that hubs match natural semantic groupings
- Discover notes that should be linked but aren't
- Find orphan notes that don't fit any cluster
- Plan hub reorganization based on actual content relationships

## Output Legend

- ★ = permanent note (validated knowledge)
- ○ = fleeting note (pending review)
