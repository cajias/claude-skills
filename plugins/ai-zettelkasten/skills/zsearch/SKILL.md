---
name: zsearch
description: Semantic search across your knowledge base using natural language queries.
---

# /zsearch - Semantic Knowledge Search

Search your knowledge base using natural language.

## Usage

```bash
/zsearch <query>
/zsearch <query> --type fact|decision|pattern|correction
/zsearch <query> --top 10
```

## Implementation

Run the search command with AWS credentials:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
export ZETTELKASTEN_ROLE_ARN=arn:aws:iam::806230523044:role/ZettelkastenPluginRole
uvx --from /Users/cajias/.claude/my-claude-skills/plugins/ai-zettelkasten zk-search "QUERY" [OPTIONS]
'
```

Replace `QUERY` with the user's search terms and `[OPTIONS]` with any flags.

## Options

| Flag | Description |
|------|-------------|
| `--type`, `-t` | Filter by knowledge type (fact, decision, pattern, correction) |
| `--top`, `-n` | Number of results (default: 5) |

## Examples

```bash
# Basic search
zk-search "lambda cold starts"

# Filter by type
zk-search "database choice" --type decision

# Get more results
zk-search "AWS patterns" --top 10
```
