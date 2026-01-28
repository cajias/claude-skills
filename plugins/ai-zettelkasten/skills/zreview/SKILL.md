---
name: zreview
description: |
  Review and curate extracted knowledge. Approve, edit, or discard items
  from the review queue before they become permanent. Human-in-the-loop
  curation for quality control.
version: 2.0.0
---

# /zreview - Review Extracted Knowledge

Review and curate recently extracted knowledge. Approve, edit, or discard items before they're considered permanent.

## Usage

```bash
/zreview              # Review all pending
/zreview --today      # Today's extractions only
/zreview --type fact  # Filter by type
```

## Implementation

When this skill is invoked:

1. **Fetch pending notes** from the vault:

```python
from ai_zettelkasten.obsidian import ObsidianVault
from pathlib import Path
import os

vault = ObsidianVault(Path(os.environ.get("OBSIDIAN_VAULT")))
pending = vault.list_pending_notes()
```

1. **For each note**, display review interface:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Review Queue (1/5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**S3 Vectors Embedding Dimensions**
Type: fact | Confidence: 0.85
Tags: aws, s3-vectors, bedrock

> Bedrock Titan uses 1536 dimensions for embeddings.
> The S3 Vectors index must be created with dimension=1536.

📎 Suggested Links (similarity > 0.7):
  1. [[titan-embedding-models]] (0.82)
  2. [[s3-vectors-setup]] (0.74)

🏷️ Suggested Hub: hub-aws-serverless

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[a]pprove  [e]dit  [d]iscard  [s]kip  [l]ink  [q]uit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

1. **Handle actions**:

**[a]pprove:**

```python
# Promote note to permanent
permanent_path = vault.promote_note(fleeting_path)

# Create approved links
for link in approved_links:
    # Add bidirectional links
    pass

# Update S3 Vectors metadata
vectors.update_metadata(note.id, updated_metadata)

print(f"✅ Promoted to {permanent_path}")
```

**[e]dit:**

```python
# Open note content for editing
edited_content = get_user_edit(note.content)
edited_tags = get_user_edit(note.tags)

# Update note and re-save
note.content = edited_content
note.tags = edited_tags
vault.write_note(note)

# Re-embed with new content
new_embedding = embeddings.embed(f"{note.title}\n{note.content}")
vectors.update_vector(note.id, new_embedding, metadata)
```

**[d]iscard:**

```python
# Move to archive
archive_path = vault.root / "knowledge-base" / "fleeting" / ".archive"
archive_path.mkdir(exist_ok=True)
shutil.move(fleeting_path, archive_path / fleeting_path.name)

# Remove from S3 Vectors
vectors.delete_vector(note.id)

print("🗑️ Moved to archive")
```

**[l]ink:**

```python
# Show all notes for manual linking
all_notes = vault.list_all_notes()
# User selects which to link
selected = user_select_notes(all_notes)
# Add to note's links
note.links.extend(selected)
```

1. **After all reviews**, show summary:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Review Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Approved: 3
📝 Edited: 1
🗑️ Discarded: 1
⏭️ Skipped: 0

New permanent notes:
  • permanent/s3-vectors-dimensions.md
  • permanent/chose-uvx-for-hooks.md
  • permanent/mermaid-diagrams-pattern.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
