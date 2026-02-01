---
name: zenrich
description: |
  Enrich atomic Zettelkasten notes with proper structure. Expands single-paragraph
  notes into full ZK format with Problem Solved, The Pattern, Why This Works,
  and Related sections. Batch processing with parallel subagents.
version: 1.0.0
---

# /zenrich - Enrich Atomic Notes

Expand atomic (single-paragraph) notes into properly structured Zettelkasten notes.

## Usage

```bash
/zenrich                     # Enrich all atomic notes in fleeting
/zenrich --batch 20          # Process in batches of 20
/zenrich --file note.md      # Enrich specific note
/zenrich --pattern "flee-*"  # Enrich notes matching pattern
```

## Target Structure

Every enriched note should have:

```markdown
# [Original Title]

## Problem Solved

What issue or challenge does this pattern/concept address?

## The Pattern

Expanded content with:

- Implementation details
- Code examples (if applicable)
- Guidelines and best practices
- Tables or diagrams where helpful

## Why This Works

The underlying principle that makes this effective.

## Related

- [[existing-note-1]]
- [[existing-note-2]]
- [[existing-note-3]]
```

## Implementation

1. **Identify atomic notes** (notes lacking full structure):

```python
def is_atomic(note_path):
    content = note_path.read_text()
    lines = [l for l in content.split("\n") if l.strip() and not l.startswith("---")]

    has_sections = "## Problem Solved" in content
    line_count = len(lines)

    return not has_sections and line_count < 15
```

1. **For batch processing**, group notes and use parallel subagents:

```python
# Group into batches of ~25
batches = [notes[i:i+25] for i in range(0, len(notes), 25)]

# Launch parallel agents
for batch in batches:
    launch_subagent(
        task=f"Enrich these {len(batch)} notes",
        files=batch,
        structure=TARGET_STRUCTURE
    )
```

1. **Enrichment prompt for subagent**:

```markdown
Enrich each atomic note with proper ZK structure:

1. Keep original title (# heading)
1. Add ## Problem Solved - what issue does this address?
1. Add ## The Pattern - expand with implementation details, examples, guidelines
1. Add ## Why This Works - explain the underlying principle
1. Add ## Related - suggest 2-3 related concepts as [[wiki-links]]

IMPORTANT: Related links must reference EXISTING notes in the knowledge base.
Use semantic similarity to find relevant existing notes.

Keep frontmatter unchanged. Edit existing files, don't create new ones.
```

1. **Validate enrichment** after completion:

```python
def validate_enriched(note_path):
    content = note_path.read_text()

    required_sections = [
        "## Problem Solved",
        "## The Pattern",
        "## Why This Works",
        "## Related"
    ]

    return all(section in content for section in required_sections)
```

1. **Display progress**:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Enrichment Progress
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Batch 1/6: ████████████████████ 27/27 ✓
Batch 2/6: ████████████████░░░░ 22/27 ...
Batch 3/6: ░░░░░░░░░░░░░░░░░░░░ pending
...

Enriched: 49/162
Remaining: 113

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Notes

- Enrichment preserves original frontmatter (id, tags, source, etc.)
- Related links should only reference existing notes to avoid broken links
- Use semantic similarity to find relevant existing notes for Related section
- After enrichment, notes are ready for `/zreview` or `/zpromote`
