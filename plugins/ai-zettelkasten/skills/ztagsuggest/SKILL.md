---
name: ztagsuggest
description: AI-assisted tag suggestions for untagged notes using semantic similarity to find common tags from related notes
---

# /ztagsuggest - Tag Suggestions

Suggest tags for untagged or under-tagged notes by analyzing semantically similar notes.

## Usage

```text
/ztagsuggest                  # Interactive suggestion workflow
/ztagsuggest <note-id>        # Suggest tags for specific note
```

## How It Works

1. **Find untagged notes** - Scan permanent/ folder for notes with empty or minimal tags
2. **Query similar notes** - Use `/zrelated` to find semantically similar tagged notes
3. **Extract tag patterns** - Collect tags from top 5 similar notes
4. **Score suggestions** - Rank tags by frequency across similar notes
5. **Present for review** - Human approves before applying

## Implementation

### Step 1: Find Untagged Notes

List permanent notes without tags or with <2 tags:

```bash
# Scan for untagged notes
find /Users/cajias/Documents/obsidian-vault-work/knowledge-base/permanent -name "*.md" -exec grep -l "tags: \[\]" {} \; 2>/dev/null | head -20
```

Or notes with minimal tags:

```bash
grep -l "tags:" /Users/cajias/Documents/obsidian-vault-work/knowledge-base/permanent/*.md | while read f; do
  count=$(grep "tags:" "$f" | grep -oE '\[.*\]' | tr ',' '\n' | wc -l)
  if [ "$count" -lt 2 ]; then echo "$f: $count tags"; fi
done
```

### Step 2: Get Related Notes

For each untagged note, find similar notes using semantic search:

```bash
isengardcli run --account 806230523044 -- bash -c '
export ZETTELKASTEN_BUCKET=zettelkasten-cajias
export ZETTELKASTEN_INDEX=knowledge-index
export OBSIDIAN_VAULT=/Users/cajias/Documents/obsidian-vault-work
zk-related "<note title or content excerpt>" --top 5
'
```

### Step 3: Extract Tag Patterns

From the related notes output, collect tags and count frequencies:

| Tag                  | Occurrences | Confidence |
| -------------------- | ----------- | ---------- |
| `context-management` | 4/5         | 80%        |
| `ai-agents`          | 3/5         | 60%        |
| `workflows`          | 2/5         | 40%        |

### Step 4: Review and Apply

Present suggestions to user:

```text
Note: subagent-delegation-for-context-management.md
Current tags: []
Hub: AI Engineering

Suggested tags (from 5 similar notes):
  ★ context-management (4/5 matches, 80%)
  ★ ai-agents (3/5 matches, 60%)
  ○ workflows (2/5 matches, 40%)

Apply suggestions? [y/n/edit]
```

**Only apply tags with ≥40% confidence unless user explicitly approves lower.**

### Step 5: Update Note

If approved, manually add tags to the note's frontmatter:

```yaml
tags: [context-management, ai-agents]
```

Then run `/zsync` to update the vector store.

## Scoring Algorithm

Tag confidence = (# similar notes with tag) / (# similar notes checked) × 100

| Confidence | Recommendation                                |
| ---------- | --------------------------------------------- |
| ≥80%       | Strong suggestion - apply unless contradicted |
| 60-79%     | Good suggestion - likely appropriate          |
| 40-59%     | Moderate suggestion - review carefully        |
| <40%       | Weak suggestion - only if clearly relevant    |

## Batch Processing

For bulk suggestions:

1. Run audit to identify all untagged notes
2. For each note:
   - Query related notes
   - Collect tag suggestions
   - Batch review with user
3. Apply approved tags
4. Re-sync vectors

## Human Review Gates

**IMPORTANT**: Always get human approval before applying tags:

- AI suggests based on patterns
- Human validates relevance
- Human can override or edit suggestions
- Never auto-apply without review

## Success Metrics

| Metric                   | Before   | Target     |
| ------------------------ | -------- | ---------- |
| Tagged notes             | 96 (20%) | 190+ (40%) |
| Avg tags per tagged note | varies   | 3-5        |

## Tag Taxonomy Compliance

Suggestions should comply with `[[hubs/tag-taxonomy|Tag Taxonomy]]`:

- Only suggest approved tags
- Warn if suggesting deprecated tags
- Respect maximum 6 tags guideline

## Related

- `/ztagaudit` - Generate tag health report
- `/ztagfix` - Tag remediation workflow
- `/zrelated` - Find semantically related notes
- `[[hubs/tag-taxonomy|Tag Taxonomy]]` - Tag governance
