---
name: q-quip-writer
description: |
  Use when:
  (1) User says "write to Quip", "update Quip with markdown", "sync markdown to Quip"
  (2) User needs to transfer markdown documents to Quip with proper formatting
  (3) Previous bulk upload resulted in broken tables or lists
  (4) Document contains images, diagrams, tables, or lists that need careful handling
author: cajias
version: 1.0.0
date: 2025-01-27
---

# Quip Document Writer Skill

## Problem

Quip's editor has limitations when importing markdown in bulk:

- **Tables**: Cell values may be lost or misaligned
- **Lists**: Bullet points and numbered lists often render as plain paragraphs with literal `*` or `-` characters
- **Images**: Cannot be programmatically uploaded - require manual insertion
- **Mermaid diagrams**: Not supported natively - require pre-rendered images

## Context/Trigger

This skill activates when the user says:

- "write to Quip"
- "update Quip with markdown"
- "sync markdown to Quip"
- Any variation asking to transfer a markdown document to a Quip document

## Solution: Section-by-Section Transfer

Instead of writing the entire markdown file at once, this skill instructs Q Chat to:

1. **Parse the markdown into sections** (split by `##` headers)
2. **Write each section individually** to Quip
3. **Verify each section** before moving to the next
4. **Handle special content** (images, diagrams, tables, lists) with care

### Usage

When the user wants to write a markdown document to Quip, invoke Q Chat with this prompt:

**IMPORTANT: Always run q chat as a background process** to avoid timeouts. The "Thinking..." messages are normal and
indicate the command is processing - not that it's stuck. Large files (15KB+) may take several minutes to process.

```bash
# Run as background process with extended timeout
q chat --trust-all-tools "<PROMPT>"
```

Use `run_in_background: true` in the Bash tool and monitor with `BashOutput` to track progress.

### The Prompt Template

```text
You are transferring a markdown document to Quip. Follow these rules STRICTLY:

SOURCE FILE: <MARKDOWN_FILE_PATH>
TARGET QUIP: <QUIP_URL>

## TRANSFER STRATEGY

1. **Read the entire markdown file first** to understand its structure
2. **Clear the Quip document** (or confirm it should be appended)
3. **Transfer section by section** - each H2 (##) header starts a new section
4. **After each section, verify** it rendered correctly before proceeding

## CONTENT HANDLING RULES

### Images (![alt](path) or HTML <img>)
- DO NOT attempt to upload images
- Replace with placeholder:
```

[TODO: INSERT IMAGE]
Name: <filename>
Alt text: <alt text>
Original path: <full path>

````text

### Mermaid Diagrams (```mermaid blocks)
- DO NOT include raw mermaid code
- Replace with placeholder:
````

[TODO: INSERT DIAGRAM]
Type: Mermaid
Description: <brief description of what the diagram shows>
Source file: <path to .mmd file if referenced>

````text

### Tables
- Write tables ONE ROW AT A TIME if needed
- After writing a table, VERIFY each cell contains the correct value
- If a table renders incorrectly, delete it and try again with explicit formatting
- For complex tables, consider using Quip's native table format instead of markdown

### Lists (Bullet Points and Numbered)

**CRITICAL: Bullet lists and numbered lists behave DIFFERENTLY in Quip!**

#### Bullet Lists (usually work with markdown)
- Markdown syntax (`-` or `*`) typically renders correctly
- Verify: Items appear with bullet points, not literal `-` or `*` characters
- If failed: Use HTML format `<ul><li>Item</li></ul>`

#### Numbered Lists (OFTEN FAIL - require special handling)
- **Problem**: Markdown numbered lists (`1.`, `2.`) often render as plain paragraphs
- **Detection**: Look for literal `1.` at start of lines instead of actual numbered list
- **Root cause**: Quip's markdown parser poorly handles `1. Item` syntax

**MANDATORY PRE-PROCESSING FOR NUMBERED LISTS:**

Before uploading any section with numbered lists, convert markdown to HTML:

```markdown
1. First item
2. Second item
3. Third item
````

MUST become:

```html
<ol>
  <li>First item</li>
  <li>Second item</li>
  <li>Third item</li>
</ol>
```

**Nested numbered lists:**

```markdown
1. First item
   1. Nested first
   2. Nested second
2. Second item
```

MUST become:

```html
<ol>
  <li>
    First item
    <ol>
      <li>Nested first</li>
      <li>Nested second</li>
    </ol>
  </li>
  <li>Second item</li>
</ol>
```

**Mixed lists (bullet inside numbered):**

```markdown
1. First item
   - Sub bullet A
   - Sub bullet B
2. Second item
```

MUST become:

```html
<ol>
  <li>
    First item
    <ul>
      <li>Sub bullet A</li>
      <li>Sub bullet B</li>
    </ul>
  </li>
  <li>Second item</li>
</ol>
```

**Verification checklist for numbered lists:**

- [ ] Numbers appear as actual list numbers (1, 2, 3...), not literal text
- [ ] Items are indented as list items, not as paragraphs
- [ ] Nested lists maintain proper hierarchy
- [ ] List continues with correct sequential numbering

**If numbered list verification fails:**

1. Delete the malformed content
2. Re-upload using explicit HTML `<ol><li>...</li></ol>` format
3. Use QuipEditor with `format="html"` instead of `format="markdown"`

### Code Blocks

- Verify code blocks render with monospace font
- Verify syntax highlighting is applied if language is specified
- Long code blocks may need to be split

## VERIFICATION CHECKLIST

After writing each section, verify:

- [ ] Headers are correct level (H1, H2, H3)
- [ ] **Bullet lists** render with bullet points (not literal `-` or `*`)
- [ ] **Numbered lists** render with sequential numbers (not literal `1.`, `2.` text)
- [ ] Nested lists maintain proper indentation hierarchy
- [ ] Tables have all cells populated with correct values
- [ ] Code blocks are formatted as code
- [ ] Links are clickable
- [ ] Image/diagram placeholders are clearly marked

**IMPORTANT: Numbered list verification is critical!** If you see lines starting with `1.` as plain text,
the list failed and must be re-uploaded as HTML.

## ERROR RECOVERY

If a section fails to render correctly:

1. Delete the malformed content
2. Try writing it in smaller chunks
3. If markdown syntax fails, use Quip's native formatting
4. Report any sections that could not be transferred correctly

## FINAL REPORT

After completing the transfer, provide:

- List of sections transferred successfully
- List of image placeholders (with paths for manual upload)
- List of diagram placeholders
- Any sections that had rendering issues
- Any tables that needed manual correction

````text

## Example Invocation

**User says:** "Write the ADR-010 markdown to Quip"

**You execute (as background process):**
```bash
# Use Bash tool with run_in_background: true and timeout: 600000
q chat --trust-all-tools "You are transferring a markdown document to Quip. Follow these rules STRICTLY:

SOURCE FILE: /Users/cajias/Projects/omega-worktree/adr-009/docs/adr/adr-010-agentcore-gateway-migration.md
TARGET QUIP: https://quip-amazon.com/3XRMA6802u9T/ADR10

## TRANSFER STRATEGY
1. Read the entire markdown file first to understand its structure
2. Clear the Quip document or start fresh
3. Transfer section by section - each H2 (##) header starts a new section
4. After each section, verify it rendered correctly before proceeding

## CONTENT HANDLING RULES

### Images
Replace with: [TODO: INSERT IMAGE] Name: <filename> Path: <path>

### Mermaid Diagrams
Replace with: [TODO: INSERT DIAGRAM] Type: Mermaid Description: <description>

### Tables
Write tables carefully, verify each cell has correct value. Re-do if cells are empty.

### Lists - CRITICAL DIFFERENCE BETWEEN BULLET AND NUMBERED

**Bullet lists** (`-` or `*`): Usually work with markdown format.

**Numbered lists** (`1.`, `2.`): OFTEN FAIL! Must be pre-converted to HTML:
- Before uploading, convert ALL numbered lists from markdown to HTML
- Convert: '1. Item' -> '<ol><li>Item</li></ol>'
- If verification shows literal '1.' text, delete and re-upload as HTML with format='html'
- Use QuipEditor with format='html' for sections containing numbered lists

### Verification
After each section:
1. Check bullet lists show actual bullets (not `-` or `*` text)
2. Check numbered lists show actual numbers (not `1.` text) - THIS IS THE MOST COMMON FAILURE
3. If numbered list failed, re-upload that section using HTML format

## After completion, report:
- Sections transferred
- Image placeholders created
- Any rendering issues found"
````

## When to Use This Skill

- Transferring ADRs, design docs, or READMEs to Quip
- When a previous bulk upload resulted in broken tables or lists
- When the document contains images or diagrams that need placeholders
- When accuracy of tables and lists is critical

## When NOT to Use

- Simple text updates (use regular q-chat skill)
- Documents without tables, lists, or images (bulk upload is fine)
- When you just need to append a small section
