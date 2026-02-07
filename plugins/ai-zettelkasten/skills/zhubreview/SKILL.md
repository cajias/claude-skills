---
name: zhubreview
description: Comprehensive hub review analyzing semantic clusters against existing hubs to find gaps, unassigned notes, and optimization opportunities
---

# /zhubreview - Comprehensive Hub Review

Analyze the entire knowledge base to evaluate hub organization, discover cluster gaps, and identify optimization opportunities.

## Usage

```text
/zhubreview                    # Default 10 clusters
/zhubreview --clusters 15      # More fine-grained analysis
```

## Implementation

Run the hub review command with proper AWS credentials:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
export ZETTELKASTEN_ROLE_ARN=arn:aws:iam::806230523044:role/ZettelkastenPluginRole
export OBSIDIAN_VAULT="${OBSIDIAN_VAULT:-$HOME/Documents/Obsidian Vault}"
zk-hub-review --clusters 10
'
```

## What It Does

1. **Load existing hubs** - Embeds each hub file to create semantic centroids
2. **Fetch all vectors** - Gets all note embeddings from S3 Vectors
3. **Analyze assignments** - Counts notes with/without hub assignments
4. **Discover clusters** - Uses k-means clustering on embeddings
5. **Match clusters to hubs** - Calculates similarity between cluster centroids and hubs
6. **Generate report** - Identifies gaps, suggests new hubs, recommends assignments

## Output Sections

### Cluster Analysis

Each discovered cluster shows:

- **Status**: ✓ (matched), ~ WEAK (partial match), ⚠ GAP (needs new hub)
- **Keywords**: Auto-extracted from note titles
- **Best hub**: Most similar existing hub
- **Sample notes**: Representative notes in the cluster

### Summary Table

| Metric            | Description                     |
| ----------------- | ------------------------------- |
| Permanent notes   | Total permanent notes analyzed  |
| Notes with hub    | Notes that have hub assignments |
| Notes without hub | Notes missing hub assignments   |
| Existing hubs     | Current hub count               |
| Gap clusters      | Clusters without matching hubs  |

### Recommendations

- **Suggested New Hubs**: Cluster topics that need dedicated hubs
- **Notes Needing Assignment**: Breakdown by cluster of unassigned notes

## When to Use

- After bulk import of new knowledge
- Periodic knowledge base maintenance (weekly/monthly)
- Before major reorganization
- When knowledge feels poorly organized
- After significant topic expansion

## Interpretation Guide

| Hub Similarity | Meaning                                         |
| -------------- | ----------------------------------------------- |
| > 55%          | Good match - cluster covered by existing hub    |
| 40-55%         | Weak match - hub exists but may need refinement |
| < 40%          | Gap - cluster needs a new dedicated hub         |

## Follow-up Actions

After running hub review:

1. **Create new hubs** for gap clusters using `/zadd` or manual creation
2. **Bulk-assign notes** to appropriate hubs
3. **Run `/zhubcheck`** to validate assignments
4. **Run `/zsync`** to update S3 Vectors with changes
