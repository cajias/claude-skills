# AI Zettelkasten v2.0

True Zettelkasten methodology for Claude Code - atomic notes, semantic search, automatic hubs.

## Features

- **Atomic Notes** - One idea per note, proper lifecycle (fleeting -> permanent)
- **Semantic Search** - Find knowledge by meaning, not keywords
- **Auto-Linking** - Suggested connections based on similarity
- **Hub Generation** - Auto-clustered topic notes
- **Proactive Capture** - Suggestions to save knowledge mid-conversation

## Quick Start

```bash
# Install plugin
claude plugin install ai-zettelkasten@personal-skills

# Set environment
export ZETTELKASTEN_BUCKET=your-bucket
export ZETTELKASTEN_INDEX=knowledge-index
export OBSIDIAN_VAULT=~/Documents/obsidian-vault-work
```

## Skills

| Skill | Description |
|-------|-------------|
| `/zadd` | Manually capture knowledge |
| `/zreview` | Review and approve extractions |
| `/zsearch` | Semantic search |
| `/zhubs` | Browse topic clusters (P1) |

## Architecture

```
knowledge-base/
├── fleeting/     # Pending review
├── permanent/    # Approved notes
├── hubs/         # Auto-generated clusters
└── projects/     # Project-scoped notes
```

## Knowledge Types

| Type | Description | Example |
|------|-------------|---------|
| **Fact** | Information discovered | "S3 Vectors uses 1536 dimensions" |
| **Decision** | Choice with rationale | "Chose uvx over pip for isolation" |
| **Pattern** | Reusable approach | "Always use Mermaid for diagrams" |
| **Correction** | Mistake fixed | "boto3 lacks s3vectors, use CLI" |

## Workflow

1. **Capture** - Knowledge extracted at session end or via `/zadd`
2. **Review** - Curate with `/zreview` (approve, edit, discard)
3. **Organize** - Auto-clustered into hubs
4. **Retrieve** - Find with `/zsearch` or topic detection

## Development

```bash
cd plugins/ai-zettelkasten
pip install -e ".[dev]"
pytest tests/ -v
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ZETTELKASTEN_BUCKET` | zettelkasten-prod | S3 Vectors bucket |
| `ZETTELKASTEN_INDEX` | knowledge-index | S3 Vectors index |
| `OBSIDIAN_VAULT` | ~/Documents/obsidian-vault-work | Vault path |

## License

MIT
