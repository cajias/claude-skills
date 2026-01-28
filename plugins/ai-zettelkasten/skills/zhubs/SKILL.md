---
name: zhubs
description: |
  Browse and manage auto-generated hub notes. View semantic clusters of related
  knowledge, regenerate hubs, and explore topic-based organization.
version: 2.0.0
---

# /zhubs - Browse Knowledge Hubs

Browse and manage auto-generated hub notes that cluster related knowledge.

## Usage

```bash
/zhubs                    # List all hubs
/zhubs <hub-name>         # View specific hub
/zhubs --regenerate       # Force reclustering
```

## Implementation

When this skill is invoked:

### List Mode (no arguments)

1. **Fetch all hubs** from the vault:

```python
from ai_zettelkasten.obsidian import ObsidianVault
from pathlib import Path
import os

vault = ObsidianVault(Path(os.environ.get("OBSIDIAN_VAULT", "~/Documents/obsidian-vault-work")))
hubs = vault.list_hubs()
```

1. **Display hub list**:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Knowledge Hubs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. hub-aws-serverless (8 notes)
   Tags: aws, lambda, s3-vectors, bedrock
   Recent: S3 Vectors Metadata Limits (2h ago)

2. hub-testing-patterns (5 notes)
   Tags: pytest, tdd, mocking
   Recent: Mock Boto3 Clients (1d ago)

3. hub-claude-plugins (4 notes)
   Tags: claude-code, skills, hooks
   Recent: Hook Context Injection (3h ago)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1-3] View hub  [r] Regenerate  [q] Quit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### View Mode (with hub name)

1. **Read the hub note**:

```python
hub = vault.read_hub(hub_name)
```

1. **Display hub details**:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 Hub: AWS Serverless Patterns
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8 notes | Generated: 2026-01-28
Tags: aws, lambda, s3-vectors, bedrock

## Facts (4)
1. S3 Vectors Embedding Dimensions
2. Lambda Cold Start Times
3. Bedrock Model Limits
4. DynamoDB Capacity Units

## Decisions (2)
5. Chose S3 Vectors Over Aurora
6. Selected Titan for Embeddings

## Patterns (2)
7. Serverless Cost Optimization
8. Lambda Layer Patterns

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1-8] View note  [b] Back  [q] Quit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Regenerate Mode (--regenerate)

1. **Trigger hub regeneration**:

```python
from ai_zettelkasten.clustering import HubGenerator
from ai_zettelkasten.s3vectors import S3VectorsStore

vectors = S3VectorsStore(
    os.environ.get("ZETTELKASTEN_BUCKET", "zettelkasten-prod"),
    os.environ.get("ZETTELKASTEN_INDEX", "knowledge-index")
)

generator = HubGenerator(vectors, vault, threshold=0.75, min_size=3)
new_hubs = generator.generate_hubs()

print(f"Generated {len(new_hubs)} hubs from {n} permanent notes")
```

## Examples

```bash
/zhubs
→ Lists all 5 hubs with member counts and tags

/zhubs hub-aws-serverless
→ Shows detailed view of AWS Serverless hub with all member notes

/zhubs --regenerate
→ Reclusters all permanent notes and regenerates hubs
→ "Generated 5 hubs from 32 permanent notes"
```

## Notes

- Hubs are auto-generated when notes are promoted via `/zreview`
- Use `--regenerate` if hubs seem out of date
- Minimum 3 notes required to form a hub
- Similarity threshold is 0.75 (adjustable in config)
