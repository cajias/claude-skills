---
name: zadd
description: |
  Manually add knowledge to the Zettelkasten. Use when you want to explicitly
  capture a fact, decision, pattern, or correction. Supports type flags and auto-tagging.
version: 2.0.0
---

# /zadd - Manually Add Knowledge

Manually add a piece of knowledge to the Zettelkasten.

## Usage

```
/zadd <content>
/zadd --type fact|decision|pattern|correction <content>
/zadd --tags "tag1,tag2" <content>
/zadd --project <name> <content>
```

## Implementation

When this skill is invoked:

1. **Parse arguments** from the command:
   - `--type` (default: auto-detect from content)
   - `--tags` (default: auto-generate)
   - `--project` (default: none, global scope)

2. **Auto-detect type** if not specified:
   - Contains "chose/decided/selected" → decision
   - Contains "always/never/pattern" → pattern
   - Contains "fixed/was wrong/actually" → correction
   - Default → fact

3. **Auto-generate tags** from content:
   - Extract technical terms (AWS, Python, etc.)
   - Extract domain concepts
   - Limit to 3-5 tags

4. **Create the note** using the extractor:

```python
from ai_zettelkasten.extractor import KnowledgeExtractor, ExtractionItem
from ai_zettelkasten.obsidian import KnowledgeType
from pathlib import Path
import os

extractor = KnowledgeExtractor(
    vault_path=Path(os.environ.get("OBSIDIAN_VAULT", "~/Documents/obsidian-vault-work")),
    bucket=os.environ.get("ZETTELKASTEN_BUCKET", "zettelkasten-prod"),
    index=os.environ.get("ZETTELKASTEN_INDEX", "knowledge-index")
)

item = ExtractionItem(
    knowledge_type=KnowledgeType.FACT,  # or detected type
    title=parsed_title,
    content=parsed_content,
    tags=parsed_tags,
    confidence=0.9  # High for manual adds
)

result = extractor.process_item(item)
```

5. **Find related notes** for linking suggestions:

```python
related = extractor.find_related(content, top_k=3)
```

6. **Report result**:

```
✅ Added to knowledge base:

Type: fact
Tags: aws, s3-vectors, limits
Path: knowledge-base/fleeting/s3-vectors-metadata-limits.md

📎 Related notes (link during /zreview):
  1. S3 Vectors Embedding Dimensions (0.82 similarity)
  2. S3 Vectors Setup Pattern (0.71 similarity)

Status: Pending review
```

## Examples

```
/zadd S3 Vectors has 50 metadata keys per vector
→ Type: fact, Tags: aws, s3-vectors, limits

/zadd --type decision Chose uvx over pip for hook dependencies
→ Type: decision, Tags: python, dependencies, hooks

/zadd --project omega The agent core uses interceptors for MCP
→ Type: fact, Tags: omega, mcp, architecture, Scope: project
```
