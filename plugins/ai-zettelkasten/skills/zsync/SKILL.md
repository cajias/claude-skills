---
name: zsync
description: Sync unindexed Obsidian notes to S3 Vectors for semantic search
---

# /zsync - Sync Knowledge Base to S3 Vectors

Manually sync notes from Obsidian to S3 Vectors. Use when auto-indexing wasn't available (e.g., missing AWS credentials) or to ensure all notes are searchable.

## Usage

```
/zsync
```

## Implementation

Run the sync command with proper AWS credentials:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
export ZETTELKASTEN_ROLE_ARN=arn:aws:iam::806230523044:role/ZettelkastenPluginRole
export OBSIDIAN_VAULT=/Users/cajias/Documents/obsidian-vault-work
uvx --from /Users/cajias/.claude/my-claude-skills/plugins/ai-zettelkasten zk-sync
'
```

## What It Does

1. Scans `knowledge-base/fleeting/` and `knowledge-base/permanent/` folders
2. Compares against existing vectors in S3 Vectors
3. Indexes any notes not yet in S3 Vectors
4. Reports sync results

## When to Use

- After writing notes directly to Obsidian (bypassing zk-extract)
- When PostToolCall hook couldn't index (no AWS credentials)
- To ensure search finds all notes
