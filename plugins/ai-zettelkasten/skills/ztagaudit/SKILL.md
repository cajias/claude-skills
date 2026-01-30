---
name: ztagaudit
description: Audit tags in the knowledge base to identify orphans, over-tagged notes, and tag health metrics
---

# /ztagaudit - Tag Audit

Generate a comprehensive tag health report for the knowledge base, identifying issues and opportunities for consolidation.

## Usage

```
/ztagaudit                    # Generate audit report
```

## Implementation

Run the tag audit command with proper AWS credentials:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
export OBSIDIAN_VAULT=/Users/cajias/Documents/obsidian-vault-work
zk-tag-audit
'
```

## What It Does

1. **Scans all notes** - Reads permanent/ and fleeting/ folders
2. **Extracts tags** - Parses frontmatter from each note
3. **Calculates metrics** - Tag frequency, co-occurrence, distribution
4. **Identifies issues** - Orphan tags, over-tagged notes
5. **Generates report** - Markdown file in `.reports/` folder

## Output Sections

### Summary
- Total notes scanned
- Notes with tags (count and percentage)
- Unique tag count
- Orphan tag count (used only once)
- Over-tagged note count (7+ tags)

### Tag Frequency Distribution
Table showing each tag, its count, and percentage of tagged notes.

### Orphan Tags
List of tags used only once, with the note that uses them.

### Over-Tagged Notes
Table of notes with 7+ tags (target is 4-6).

### Co-occurrence Matrix
Top tag pairs that frequently appear together.

## Interpretation Guide

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Tagged notes | >40% | 20-40% | <20% |
| Orphan tags | <10% of vocab | 10-30% | >30% |
| Over-tagged | 0 notes | 1-3 notes | >3 notes |
| Unique tags | 25-35 | 35-50 | >50 |

## When to Use

- Monthly knowledge base maintenance
- Before/after tag consolidation
- When planning tag taxonomy changes
- After bulk imports of new knowledge
- When knowledge base feels disorganized

## Follow-up Actions

After running audit:

1. **For orphan tags**: Consider consolidating to broader categories using `/ztagfix`
2. **For over-tagged notes**: Prune excess tags using `/ztagfix`
3. **For low tag adoption**: Run `/ztagsuggest` on untagged notes
4. **For co-occurrence patterns**: Consider if tags should be merged

## Related Commands

- `/ztagfix` - Interactive remediation workflow
- `/ztagsuggest` - AI-assisted tag suggestions
- `/zhubcheck` - Validate hub assignments
- `/zhubreview` - Comprehensive hub analysis
