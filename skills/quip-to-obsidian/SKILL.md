---
name: quip-to-obsidian
description: This skill should be used when the user asks to "migrate quip to obsidian", "download quip images", "fix quip diagrams", "export quip folder", or mentions migrating Quip documents with images/diagrams to Obsidian. Handles complete Quip folder migration including blob/image downloads.
---

# Quip to Obsidian Migration

Migrate Quip folders and documents to Obsidian with full image/diagram support.

## Overview

Quip documents exported to markdown retain image references as `/blob/THREAD_ID/BLOB_ID` URLs, but the actual images require authenticated API access to download. This skill provides the complete workflow to:

1. Download all blob images from Quip using the API
2. Update markdown references to use local paths
3. Convert reference-style images to inline format for Obsidian compatibility
4. Fix Quip table formatting (removes empty first columns and row numbers)

## Prerequisites

### Quip API Token

Obtain a Quip API token from: `https://quip-amazon.com/dev/token`

Configure the token in one of these locations:
```bash
# Option 1: Environment variable
export QUIP_API_TOKEN="your-token-here"

# Option 2: amzn-mcp config file
mkdir -p ~/.amazon-internal-mcp-server
echo 'QUIP_API_TOKEN="your-token-here"' > ~/.amazon-internal-mcp-server/.env
chmod 600 ~/.amazon-internal-mcp-server/.env
```

### Quip API Endpoint

For Amazon internal Quip: `https://platform.quip-amazon.com/1/blob/{thread_id}/{blob_id}`
For public Quip: `https://platform.quip.com/1/blob/{thread_id}/{blob_id}`

## Migration Workflow

### Step 1: Identify Blob References

Extract all unique blob references from the migrated markdown files:

```bash
grep -rhoE '/blob/[A-Za-z0-9]+/[A-Za-z0-9_-]+' /path/to/obsidian/folder | sort -u > /tmp/quip-blobs.txt
```

Filter out non-Quip patterns (documentation references):
```bash
grep -v "main/articles\|pattern/" /tmp/quip-blobs.txt > /tmp/quip-blobs-filtered.txt
```

### Step 2: Download Blobs

Use the download script at `scripts/download-quip-blobs.sh`:

```bash
# Set variables
export QUIP_API_TOKEN="your-token"
export BLOB_LIST="/tmp/quip-blobs-filtered.txt"
export OUTPUT_DIR="/path/to/obsidian/folder/attachments"

# Run download script
bash ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/download-quip-blobs.sh
```

The script:
- Downloads each blob via the Quip API
- Detects file type (PNG, JPG, GIF, SVG)
- Names files as `{thread_id}_{blob_id}.{ext}`
- Reports success/failure counts

### Step 3: Update Markdown References

After downloading, update all markdown files to reference local images:

```bash
# Update blob paths to local attachments
find "$OBSIDIAN_DIR" -name "*.md" -type f -exec sed -i '' -E \
  "s|/blob/([A-Za-z0-9]+)/([A-Za-z0-9_-]+)|attachments/\1_\2.png|g" {} \;
```

### Step 4: Convert to Obsidian Format

Obsidian works better with inline image syntax. Use the Python script at `scripts/fix-obsidian-images.py`:

```bash
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-obsidian-images.py \
  --directory "/path/to/obsidian/folder"
```

This converts reference-style links:
```markdown
![alt text][1]
[1]: attachments/image.png
```

To inline format:
```markdown
![alt text](attachments/image.png)
```

### Step 5: Fix Code Block Formatting

Quip exports code blocks with extra blank lines between every line. Fix the spacing:

```bash
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-code-block-spacing.py \
  "/path/to/obsidian/folder"
```

Then add language hints (Quip exports without them):

```bash
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-code-block-langs.py \
  "/path/to/obsidian/folder"
```

Detects: mermaid, json, yaml, typescript, python, go, bash, cedar, sql, http, xml, and directory trees.

### Step 6: Remove Invisible Characters

Quip exports contain zero-width space characters (U+200B) that break markdown rendering:

```bash
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-zero-width-spaces.py \
  "/path/to/obsidian/folder"
```

### Step 7: Fix Table Formatting

Quip exports tables with extra empty columns, row numbers, and escaped characters. Fix with:

```bash
# Fix table structure (empty columns, row numbers, escaped chars)
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-quip-tables.py \
  "/path/to/obsidian/folder"

# Fix separator lines to match column count
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-table-separators.py \
  "/path/to/obsidian/folder"

# Remove any remaining escaped characters
find "/path/to/obsidian/folder" -name "*.md" -exec sed -i '' 's/\\(/(/g; s/\\)/)/g; s/\\_/_/g' {} \;
```

This converts malformed tables:
```markdown
||Header1|Header2|
|---|---|---|
|1|Cell1|Cell2|
```

To proper markdown:
```markdown
|Header1|Header2|
|---|---|
|Cell1|Cell2|
```

## Quick Migration Command

For a complete migration in one go:

```bash
# Set environment
export QUIP_API_TOKEN="your-token"
export OBSIDIAN_DIR="/path/to/obsidian/migration/folder"

# 1. Extract blob list
grep -rhoE '/blob/[A-Za-z0-9]+/[A-Za-z0-9_-]+' "$OBSIDIAN_DIR" | \
  grep -v "main/articles\|pattern/" | sort -u > /tmp/quip-blobs.txt

# 2. Create attachments folder
mkdir -p "$OBSIDIAN_DIR/attachments"

# 3. Download blobs
BLOB_LIST=/tmp/quip-blobs.txt OUTPUT_DIR="$OBSIDIAN_DIR/attachments" \
  bash ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/download-quip-blobs.sh

# 4. Update references and convert format
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-obsidian-images.py \
  --directory "$OBSIDIAN_DIR"

# 5. Fix code block formatting
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-code-block-spacing.py "$OBSIDIAN_DIR"
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-code-block-langs.py "$OBSIDIAN_DIR"

# 6. Remove invisible characters (zero-width spaces)
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-zero-width-spaces.py "$OBSIDIAN_DIR"

# 7. Fix table formatting
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-quip-tables.py "$OBSIDIAN_DIR"
python3 ~/.claude/my-claude-skills/skills/quip-to-obsidian/scripts/fix-table-separators.py "$OBSIDIAN_DIR"
find "$OBSIDIAN_DIR" -name "*.md" -exec sed -i '' 's/\\(/(/g; s/\\)/)/g; s/\\_/_/g' {} \;
```

## Troubleshooting

### Token Verification Failed (400)

- Verify token is correctly quoted (contains `|` and `=` characters)
- Check token hasn't expired
- Ensure using correct API endpoint (amazon vs public)

### Images Not Rendering in Obsidian

1. Check relative paths are correct from markdown file to attachments folder
2. Verify inline image syntax (not reference-style)
3. Try Obsidian wikilink format: `![[attachments/filename.png]]`

### Missing Images

Some blob references may be to non-existent or deleted images. Check the download script output for failed downloads.

### Tables Not Rendering

Quip exports tables with extra leading columns (`||`) and row numbers (`|1|`, `|2|`). Run `fix-quip-tables.py` to correct the format.

Also check for zero-width space characters (U+200B) before tables - these invisible characters can prevent table recognition. Run `fix-zero-width-spaces.py` to remove them.

## Blob URL Format Reference

Quip blob URLs follow this pattern:
- **Markdown reference**: `/blob/THREAD_ID/BLOB_ID`
- **Full API URL**: `https://platform.quip-amazon.com/1/blob/THREAD_ID/BLOB_ID`
- **Local path**: `attachments/THREAD_ID_BLOB_ID.png`

Thread IDs and Blob IDs are base64-like strings (alphanumeric with `-` and `_`).

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/download-quip-blobs.sh` | Download all blobs from a list file |
| `scripts/fix-obsidian-images.py` | Convert reference-style to inline images |
| `scripts/fix-code-block-spacing.py` | Remove extra blank lines from code blocks |
| `scripts/fix-code-block-langs.py` | Auto-detect and add language hints to code blocks |
| `scripts/fix-zero-width-spaces.py` | Remove invisible Unicode characters that break rendering |
| `scripts/fix-quip-tables.py` | Fix Quip table formatting (empty columns, row numbers, escapes) |
| `scripts/fix-table-separators.py` | Ensure table separators match column count |

## Additional Resources

- **`references/quip-api.md`** - Detailed Quip API documentation and authentication
