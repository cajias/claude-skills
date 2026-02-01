---
name: ai-zettelkasten:zadd
description: |
  Manually add knowledge to the Zettelkasten. Use when you want to explicitly
  capture a fact, decision, pattern, or correction without waiting for automatic
  extraction. Supports type flags and auto-tagging.
version: 0.2.0
---

# /zadd - Manually Add Knowledge

Manually add a piece of knowledge to the Zettelkasten. Use when you want to explicitly
capture something without waiting for automatic extraction.

## Usage

```text
/zadd <content>
/zadd --type fact|decision|pattern|correction <content>
/zadd --tags "tag1,tag2" <content>
```

## Examples

- `/zadd S3 Vectors GA December 2025 with 2B vectors per index`
- `/zadd --type decision Chose Mermaid over ASCII for all diagrams`
- `/zadd --type pattern --tags "testing,tdd" Always write failing test first`

## Implementation

When this skill is invoked:

1. **Parse arguments**:
   - Extract type (default: `fact`)
   - Extract tags (auto-generate if not provided)
   - Get content

1. **Auto-generate tags** if not provided:
   - Extract key terms from content
   - Match against common tag vocabulary
   - Suggest 2-5 relevant tags

1. **Create extraction entry** in Obsidian:

```bash
# Append to today's extractions
mcp__obsidian__write_note \
  --path "knowledge-base/extractions/$(date +%Y-%m-%d).md" \
  --mode append \
  --content "
## [$(date +%H:%M)] $TITLE

**Type**: $TYPE
**Tags**: $TAGS
**Source**: manual via /zadd

$CONTENT

---
"
```

1. **Optionally embed immediately** to S3 Vectors:
   - If `--now` flag provided, skip review queue
   - Generate embedding via Bedrock
   - Store directly in S3 Vectors

1. **Confirm**:

```text
✅ Added to knowledge base:

Type: fact
Tags: s3-vectors, aws, architecture
Content: "S3 Vectors GA December 2025 with 2B vectors per index"

Status: Pending review (use /zreview to approve)
```

## Quick Add Shortcuts

For rapid capture during work:

```text
/zadd! <content>     # Add as fact, auto-tags, skip confirmation
/zadd? <content>     # Add as decision (records a choice made)
/zadd~ <content>     # Add as pattern (reusable approach)
/zadd* <content>     # Add as correction (mistake + fix)
```

## Notes

- Manual adds go through the same review queue as auto-extractions
- Use `--now` to bypass review for high-confidence additions
- Tags are comma-separated, no spaces around commas
