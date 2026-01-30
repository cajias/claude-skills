---
name: zfixids
description: Fix note ID prefixes to ensure permanent notes have 'perm-' and fleeting notes have 'flee-' prefixes
---

# /zfixids - Fix Note ID Prefixes

Ensure all notes have correct ID prefixes based on their location. This is critical for proper categorization in semantic search and hub analysis.

## Usage

```
/zfixids              # Fix all incorrect prefixes
/zfixids --dry-run    # Preview changes without applying
```

## Implementation

Run the fix command:

```bash
isengardcli run --account 806230523044 -- bash -c '
export OBSIDIAN_VAULT=/Users/cajias/Documents/obsidian-vault-work
zk-fix-ids --dry-run   # Preview first
zk-fix-ids             # Apply fixes
zk-sync                # Re-sync to S3 Vectors
'
```

## What It Does

1. Scans `knowledge-base/permanent/` for notes with `flee-` or `fleeting-` prefixes
2. Scans `knowledge-base/fleeting/` for notes with `perm-` prefixes
3. Updates frontmatter `id:` field with correct prefix
4. Reports all changes made

## Why This Matters

The ID prefix determines how notes are categorized in S3 Vectors:
- `perm-*` keys are treated as permanent (validated) knowledge
- `flee-*` keys are treated as fleeting (pending) knowledge

Hub analysis and cluster detection rely on these prefixes to:
- Filter for permanent notes only in reports
- Show correct markers (★ vs ○) in output
- Calculate hub coverage statistics

## When to Use

- After promoting fleeting notes to permanent
- Before running `zk-hub-review` for accurate analysis
- When hub analysis shows fewer notes than expected
- After bulk migration or import of notes

## Follow-up

After fixing IDs, run:
1. `zk-sync` - Update S3 Vectors with new IDs
2. `zk-hub-review` - Get accurate hub analysis

