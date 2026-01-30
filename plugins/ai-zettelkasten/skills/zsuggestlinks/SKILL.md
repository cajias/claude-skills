---
name: zsuggestlinks
description: Suggest meaningful Zettelkasten links between notes based on semantic similarity and relationship type analysis
---

# /zsuggestlinks - Zettelkasten Link Suggestions

Analyze notes and suggest meaningful links following core Zettelkasten principles. Unlike simple similarity matching, this command classifies the *relationship type* between notes.

## Usage

```
/zsuggestlinks path/to/note.md     # Analyze single note
/zsuggestlinks --all               # Analyze all permanent notes
/zsuggestlinks --threshold 70      # Higher similarity requirement
```

## Zettelkasten Linking Principles

### 1. Links Connect Ideas, Not Documents

Links should create meaningful conceptual connections, not just group similar topics. A link should answer: "Why does knowing A help me understand B?"

### 2. Relationship Types Matter

Every link has a semantic relationship:

| Type | Meaning | Example |
|------|---------|---------|
| **SOLVES** | A addresses problem in B | Pattern → Anti-pattern |
| **ENABLES** | A is prerequisite for B | Setup → Feature |
| **ELABORATES** | B expands on A | Overview → Deep-dive |
| **CONTRADICTS** | B challenges A | Alternative approaches |
| **SUPPORTS** | B provides evidence for A | Fact → Pattern |
| **APPLIES** | B applies principle from A | Abstract → Concrete |
| **ABSTRACTS** | B generalizes from A | Specific → General |
| **SEQUENCE** | B logically follows A | Step 1 → Step 2 |

### 3. Bidirectional Awareness

If A links to B, B should reference A. Links create a web, not a tree.

### 4. Quality Over Quantity

Not every similar note should link. The connection must add insight.

## Implementation

Run the suggest-links command:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
export OBSIDIAN_VAULT=/Users/cajias/Documents/obsidian-vault-work
zk-suggest-links /path/to/note.md
'
```

## What It Does

1. Reads target note content and extracts core concept
2. Embeds note via Bedrock Titan
3. Queries S3 Vectors for semantically similar notes
4. Filters out already-linked notes
5. Classifies relationship type for each candidate
6. Returns suggestions with relationship explanations

## Classification Heuristics

The command uses these heuristics to determine relationship type:

- **Pattern → Fact**: APPLIES (pattern applies to concrete fact)
- **Fact → Pattern**: SUPPORTS (fact supports the pattern)
- **Problem/Anti-pattern in title**: SOLVES
- **"prerequisite" or "before" in content**: ENABLES
- **Very high similarity (>85%)**: ELABORATES

## When to Use

- After creating a new note
- During periodic knowledge base maintenance
- When a note feels isolated (few links)
- Before promoting fleeting → permanent

## Output Format

```
Aggressive Context Clearing Between Tasks
  → SOLVES [[context-window-performance-degradation]] (78%)
    This note addresses problem in 'context-window-performance-degradation'
  → ENABLES [[four-phase-development-cycle]] (72%)
    This note is prerequisite for 'four-phase-development-cycle'
```

## Follow-up

After reviewing suggestions:
1. Add accepted links to note's `## Related` section
2. Add backlinks to target notes
3. Use relationship type as the link category

