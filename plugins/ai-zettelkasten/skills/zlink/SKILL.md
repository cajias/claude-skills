---
name: zlink
description: |
  Automatically find and create Zettelkasten-compliant links between notes.
  Uses semantic similarity + LLM validation to ensure meaningful connections
  with proper relationship types (ELABORATES, SUPPORTS, etc.).
version: 1.0.0
---

# /zlink - Automatic Zettelkasten Linking

Find and create meaningful links between notes following Zettelkasten principles. Unlike simple similarity matching, this command validates connections with an LLM and classifies relationship types.

## Usage

```bash
/zlink                          # Interactive - suggest links for all notes
/zlink path/to/note.md          # Suggest links for specific note
/zlink --apply                  # Apply suggested links automatically
/zlink --fix                    # Repair broken links
/zlink --audit                  # Show link health report
```

## How It Works

### 1. Semantic Discovery

Uses S3 Vectors embeddings to find semantically similar notes:

```python
# Embed note content
note_emb = embeddings.embed(f"{title}\n\n{content[:1500]}")

# Query for similar notes
results = vectors.query(note_emb, top_k=10)
```

### 2. LLM Validation

Each candidate is validated by Claude Haiku to ensure meaningful connection:

```python
from ai_zettelkasten.validator import LinkValidator

validator = LinkValidator(min_confidence=0.7)
result = validator.validate(
    source_title="My Note",
    source_content=source_preview,
    target_title="Candidate Note",
    target_content=target_preview,
)

if result.should_link:
    relationship = result.relationship  # e.g., "ELABORATES"
    confidence = result.confidence      # e.g., 0.85
```

### 3. Bidirectional Linking

Links are created in both directions with inverse relationships:

| Forward | Inverse |
|---------|---------|
| ENABLES | SEQUENCE |
| ELABORATES | ABSTRACTS |
| SUPPORTS | APPLIES |
| CONTRADICTS | CONTRADICTS |

### 4. Link Application

Links are added to the `## Related` section:

```markdown
## Related

- ELABORATES: [[context-window-management|Context Window Management]]
- SUPPORTS: [[claude-code-productivity|Claude Code Productivity Patterns]]
```

## Implementation

Run the enhanced suggest-links command:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
export OBSIDIAN_VAULT=/Users/cajias/Documents/obsidian-vault-work
zk-suggest-links path/to/note.md --apply --bidirectional --yes
'
```

## Flags Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--threshold` | 65 | Minimum similarity % for candidates |
| `--top` | 5 | Max suggestions per note |
| `--apply` | false | Actually write links to files |
| `--bidirectional` | true | Create backlinks in target notes |
| `--no-validate` | false | Skip LLM validation (faster, less accurate) |
| `--min-confidence` | 70 | Minimum LLM confidence to accept link |
| `--fix` | false | Repair broken links mode |
| `--audit` | false | Link health report mode |
| `--yes` | false | Skip confirmation prompts |

## Relationship Types

Every link includes its relationship type for context:

| Type | Meaning | Example |
|------|---------|---------|
| **SOLVES** | A addresses problem in B | Pattern → Anti-pattern |
| **ENABLES** | A is prerequisite for B | Setup → Feature |
| **ELABORATES** | A expands on B | Overview → Deep-dive |
| **CONTRADICTS** | A challenges B | Alternative approaches |
| **SUPPORTS** | A provides evidence for B | Fact → Pattern |
| **APPLIES** | A applies principle from B | Abstract → Concrete |
| **ABSTRACTS** | A generalizes from B | Specific → General |
| **SEQUENCE** | A logically follows B | Step 1 → Step 2 |

## When to Use

- **After promotion**: Run on newly promoted permanent notes
- **Maintenance**: Periodic link health checks
- **Isolated notes**: When notes have few connections
- **Broken links**: To repair links to deleted/renamed notes

## Output Example

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ZETTELKASTEN LINK SUGGESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Context Window Management Pattern
  → ELABORATES [[token-budget-optimization]] (85%, validated)
    This note expands on 'Token Budget Optimization'
  → SOLVES [[context-overflow-errors]] (78%, validated)
    This note addresses problem in 'Context Overflow Errors'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total suggestions: 2 (LLM validated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run with --apply to add these links to your notes
```

## Workflow Integration

```bash
/ztriage       # 1. Assess fleeting notes
/zenrich       # 2. Enrich atomic notes
/zfix-links    # 3. Fix broken links
/zpromote      # 4. Promote to permanent
/zlink --apply # 5. Create semantic links ← NEW
```
