---
name: zhubassign
description: Bulk assign unassigned permanent notes to their best-matching hubs using semantic similarity
---

# /zhubassign - Bulk Hub Assignment

Automatically assign unassigned permanent notes to their best-matching hubs based on semantic similarity.

## Usage

```text
/zhubassign                     # Default 50% threshold, interactive
/zhubassign --threshold 60      # Stricter threshold
/zhubassign --dry-run           # Preview without changes
/zhubassign --yes               # Skip confirmation
/zhubassign --update-vectors    # Also update S3 Vectors metadata
```

## Implementation

Run the hub assignment command with proper AWS credentials:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
export ZETTELKASTEN_ROLE_ARN=arn:aws:iam::806230523044:role/ZettelkastenPluginRole
export OBSIDIAN_VAULT="${OBSIDIAN_VAULT:-$HOME/Documents/Obsidian Vault}"
zk-hub-assign --threshold 50
'
```

## What It Does

1. **Load existing hubs** - Embeds each hub file to create semantic centroids
2. **Fetch all vectors** - Gets all note embeddings from S3 Vectors
3. **Find unassigned notes** - Identifies permanent notes without a `## Hub` section link
4. **Calculate best matches** - Uses cosine similarity to find best hub for each note
5. **Preview assignments** - Shows what will be assigned, grouped by hub
6. **Apply changes** - Updates markdown files with hub links
7. **Optionally sync vectors** - Updates S3 Vectors metadata with hub_ids

## Command Options

| Option             | Description                                              |
| ------------------ | -------------------------------------------------------- |
| `--threshold N`    | Minimum similarity (0-100) to assign a note. Default: 50 |
| `--dry-run`        | Show preview without making changes                      |
| `--yes`            | Skip confirmation prompt                                 |
| `--update-vectors` | Also update S3 Vectors metadata with hub assignments     |

## Output Format

### Assignment Preview

Notes are grouped by target hub, sorted by similarity:

```text
Claude Code Patterns Hub (12 notes)
  hub-claude-code-patterns
    [78%] orchestrator-pattern-benefits
    [75%] context-clearing-strategy
    [71%] verification-first-approach
    ... and 9 more
```

### Summary Table

Shows total notes per hub and average similarity.

### Results

After assignment, shows count of successfully assigned notes per hub.

## When to Use

- After running `/zhubreview` to see what needs assignment
- After bulk import of new notes
- During periodic knowledge base maintenance
- After creating new hubs

## Workflow Example

```text
1. /zhubreview              # Analyze gaps and unassigned notes
2. /zadd hub ...            # Create new hubs for gap clusters
3. /zhubassign --dry-run    # Preview assignments
4. /zhubassign --yes        # Apply assignments
5. /zhubcheck               # Validate assignments
6. /zsync                   # Sync changes to S3 Vectors
```

## Note Format

The command adds hub links to the `## Hub` section of each note:

```markdown
## Hub

[[hubs/hub-name|Hub Display Title]]
```

If the `## Hub` section doesn't exist, it's created at the end of the note.

## Similarity Threshold Guide

| Threshold | Use Case                                         |
| --------- | ------------------------------------------------ |
| 40%       | Aggressive assignment - may include weak matches |
| 50%       | Balanced (default) - good for general use        |
| 60%       | Conservative - only strong matches               |
| 70%+      | Very strict - only very clear matches            |

## See Also

- `/zhubreview` - Analyze hub coverage and find gaps
- `/zhubcheck` - Validate existing assignments
- `/zsync` - Sync changes to S3 Vectors
