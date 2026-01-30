---
name: zpromote
description: |
  Promote curated notes from fleeting to permanent in the Zettelkasten.
  Updates metadata (type, zk_status), moves files, and maintains link integrity.
  Batch promotion with validation.
version: 1.0.0
---

# /zpromote - Promote Notes to Permanent

Move curated fleeting notes to permanent status with proper metadata updates.

## Usage

```bash
/zpromote                     # Interactive promotion
/zpromote --all               # Promote all enriched fleeting notes
/zpromote --pattern "flee-*"  # Promote notes matching pattern
/zpromote --file note.md      # Promote specific note
```

## Prerequisites

Notes should be promoted only after:
1. Enriched with proper structure (`/zenrich`)
2. Broken links fixed (`/zfix-links`)
3. Optionally reviewed (`/zreview`)

## Implementation

1. **Validate note is ready for promotion**:

```python
def is_ready_for_promotion(note_path):
    content = note_path.read_text()

    checks = {
        "has_problem_solved": "## Problem Solved" in content,
        "has_pattern": "## The Pattern" in content,
        "has_why": "## Why This Works" in content,
        "has_related": "## Related" in content,
        "no_broken_links": not has_broken_links(content),
    }

    return all(checks.values()), checks
```

2. **Update frontmatter metadata**:

```python
import re

def update_frontmatter(content):
    # Update type: fleeting → permanent
    content = re.sub(
        r'^type:\s*fleeting',
        'type: permanent',
        content,
        flags=re.MULTILINE
    )

    # Update zk_status: pending → ingested
    content = re.sub(
        r'^zk_status:\s*pending',
        'zk_status: ingested',
        content,
        flags=re.MULTILINE
    )

    return content
```

3. **Move file to permanent directory**:

```python
import shutil
from pathlib import Path

def promote_note(fleeting_path, vault_path):
    permanent_path = vault_path / "knowledge-base" / "permanent"

    # Read and update content
    content = fleeting_path.read_text()
    updated_content = update_frontmatter(content)

    # Write to permanent location
    target_path = permanent_path / fleeting_path.name
    target_path.write_text(updated_content)

    # Remove from fleeting
    fleeting_path.unlink()

    return target_path
```

4. **Batch promotion with progress**:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📤 Promotion Progress
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Promoting: 162 notes

✓ flee-20260129-a3b4c5.md → permanent/
✓ flee-20260129-a7b8c9.md → permanent/
✓ flee-20260129-a9b0c1.md → permanent/
...

Progress: ████████████████████ 162/162

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

5. **Handle validation failures**:

```python
def promote_with_validation(notes, vault_path):
    promoted = []
    failed = []

    for note in notes:
        ready, checks = is_ready_for_promotion(note)

        if ready:
            target = promote_note(note, vault_path)
            promoted.append(target)
        else:
            failed.append((note, checks))

    return promoted, failed
```

6. **Display summary**:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Promotion Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Promoted: 162 notes
Failed: 0 notes

Vault Status:
  • Permanent: 341 notes (+162)
  • Fleeting: 0 notes (-162)

Metadata Updated:
  • type: permanent
  • zk_status: ingested

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Workflow Integration

Typical curation workflow:

```bash
/ztriage       # 1. Assess fleeting notes
/zenrich       # 2. Enrich atomic notes
/zfix-links    # 3. Fix broken links
/zreview       # 4. (Optional) Manual review
/zpromote      # 5. Promote to permanent
/zlink         # 6. Create semantic links (automatic)
```

## Automatic Linking on Promotion

After promotion, automatically suggest and apply semantic links:

```python
def post_promotion_linking(promoted_paths, vault_path):
    """Add semantic links to newly promoted notes."""
    from ai_zettelkasten.cli import suggest_links_main
    import sys

    for path in promoted_paths:
        # Call link suggestion with bidirectional linking
        sys.argv = [
            'zk-suggest-links',
            str(path),
            '--apply',
            '--bidirectional',
            '--yes'
        ]
        suggest_links_main()
```

Or via CLI after promotion:

```bash
# After promoting notes, create links
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
export OBSIDIAN_VAULT=/Users/cajias/Documents/obsidian-vault-work
zk-suggest-links path/to/promoted-note.md --apply --bidirectional --yes
'
```

## Notes

- Promotion is idempotent - already-promoted notes are skipped
- Original file IDs (flee-*) are preserved for traceability
- S3 Vectors index is automatically updated via PostToolUse hook
- Backlinks in other notes automatically resolve to new location
