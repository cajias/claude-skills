# Quip Document Writer Skill

Transfer markdown documents to Quip with proper formatting validation, handling common issues with
lists, tables, and diagrams.

## Overview

This skill enables Claude to transfer markdown documents to Quip using a section-by-section approach
that validates formatting and handles the problematic content types that often fail during bulk
uploads.

## Why This Skill Exists

Quip's editor has significant limitations when importing markdown in bulk:

| Content Type       | Problem                                                       |
| ------------------ | ------------------------------------------------------------- |
| **Tables**         | Cell values may be lost or misaligned                         |
| **Numbered Lists** | Often render as plain paragraphs with literal `1.` characters |
| **Bullet Lists**   | Sometimes render with literal `-` or `*` characters           |
| **Images**         | Cannot be programmatically uploaded                           |
| **Mermaid**        | Not supported natively                                        |

## Trigger Phrases

- "write to Quip"
- "update Quip with markdown"
- "sync markdown to Quip"
- "upload to Quip"

## Key Features

### Section-by-Section Transfer

Instead of writing entire markdown files at once:

1. **Parse** markdown into sections (split by `##` headers)
2. **Write** each section individually to Quip
3. **Verify** each section before moving to the next
4. **Handle** special content (images, diagrams, tables, lists) with care

### Smart List Handling

- **Bullet Lists**: Usually work correctly, but verification is required
- **Numbered Lists**: Automatically converted to HTML `<ol>` tags to prevent rendering failures
- **Nested Lists**: Properly handle nested numbered and bullet lists
- **Mixed Lists**: Support for bullet lists inside numbered lists and vice versa

### Image and Diagram Management

- Replace images with standardized placeholders
- Convert Mermaid diagrams to text descriptions with TODO markers
- Preserve alt text and source information for manual insertion

### Table Validation

- Verify table structure after upload
- Check for cell alignment and data integrity
- Flag any tables that need manual review

## When to Use

Use this skill when you need to:

- Transfer markdown documentation to Quip
- Migrate content from GitHub/GitLab wikis to Quip
- Sync technical documentation to Quip
- Convert markdown blog posts or articles to Quip format
- Update existing Quip documents with markdown content

## Prerequisites

- Quip API access token
- Target Quip document or folder
- Markdown file(s) to transfer
- Network access to Quip API

## Success Criteria

After running this skill, your Quip document will have:

✓ All sections properly formatted with correct headers  
✓ Numbered lists rendered as actual numbered lists, not plain text  
✓ Bullet lists with proper bullet points  
✓ Tables with correct structure and data  
✓ Image placeholders with source information  
✓ Diagram descriptions with TODO markers for manual insertion  
✓ Clean, readable formatting that matches the original markdown intent

## Limitations

- Images must be manually uploaded after document creation
- Mermaid diagrams cannot be rendered natively
- Complex nested tables may require manual adjustment
- Code syntax highlighting may differ from markdown renderers
- Cross-references between documents need manual linking

## Related Tools

- Quip API
- Markdown parsers
- HTML to Markdown converters
- Quip Desktop/Web application (for manual image uploads)

## Examples

See the `examples/` directory for sample workflows and before/after comparisons.
