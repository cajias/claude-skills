---
name: zhubcheck
description: Validate hub assignments against semantic clusters to find misassigned notes
---

# /zhubcheck - Validate Hub Assignments

Compare semantic clusters with hub assignments to find notes that may be in the wrong hub.

## Usage

```text
/zhubcheck                    # Default 60% threshold
/zhubcheck --threshold 70     # Stricter threshold
```

## Implementation

Run the hub validation command with proper AWS credentials:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
export ZETTELKASTEN_ROLE_ARN=arn:aws:iam::806230523044:role/ZettelkastenPluginRole
export OBSIDIAN_VAULT="${OBSIDIAN_VAULT:-$HOME/Documents/Obsidian Vault}"
uvx --from ${CLAUDE_PLUGIN_ROOT} zk-hub-check
'
```

## What It Does

1. Embeds each hub file to create hub centroids
2. For each permanent note, reads its assigned hub from content
3. Calculates semantic similarity to the assigned hub
4. Finds the best matching hub based on embeddings
5. Reports notes where the best match differs from assignment

## When to Use

- After bulk reorganization of notes
- When knowledge feels incorrectly categorized
- During periodic knowledge base maintenance
- Before major hub restructuring

## Interpreting Results

| Situation                        | Action                                    |
| -------------------------------- | ----------------------------------------- |
| Low similarity + better match    | Consider moving note to suggested hub     |
| Low similarity + no better match | Note may need a new hub or is too generic |
| High similarity                  | Note is well-assigned                     |

## Output Legend

- Current: The hub the note is currently assigned to
- Suggest: The hub with highest semantic similarity
- Percentage: Cosine similarity score
