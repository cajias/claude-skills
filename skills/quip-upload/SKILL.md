---
name: quip-upload
description: |
  Use when:
  (1) User says "tell q to upload <file-path> to <quip-url>" or similar
  (2) User wants to upload markdown files to Quip with proper formatting
  (3) Document contains mermaid/plantuml diagrams that need PNG generation
  (4) User needs section-by-section upload with validation
author: cajias
version: 1.0.0
date: 2025-01-27
---

# Quip Upload Skill

## Problem

Uploading markdown to Quip requires careful handling of diagrams, images, and formatting. Numbered lists frequently fail and need HTML conversion.

## Context/Trigger

This skill activates when the user says:
- "tell q to upload <file-path> to <quip-url>"
- Similar variations requesting file upload to Quip

## Prerequisites

- Mermaid CLI installed: `mmdc` command available at `/Users/cajias/.nvm/versions/node/v22.12.0/bin/mmdc`
- Quip API token available in environment or from `~/.aws/amazonq/cli-agents/amzn-docs.json`
- Agent: Use `amzn-docs` (has Quip context and tools)

## Solution: Workflow

### Phase 1: Parse and Prepare

1. **Extract information from user command**:
   - Source markdown file path
   - Target Quip URL
   - Extract Quip thread ID from URL (format: `https://<company>.quip.com/<thread-id>`)

2. **Read and parse the markdown file**:
   - Read entire markdown content
   - Split into sections (by headers: `#`, `##`, `###`, etc.)
   - Identify all images: `![alt](path)` or `<img src="path">`
   - Identify all diagram blocks:
     - Mermaid: ` ```mermaid ... ``` `
     - PlantUML: ` ```plantuml ... ``` ` or ` ```puml ... ``` `

### Phase 2: Generate Diagrams

For each mermaid or PlantUML diagram found:

1. **Extract diagram code** from the code block

2. **Generate image for Mermaid**:
   ```bash
   # Create temp file with mermaid code
   echo '<mermaid-code>' > /tmp/diagram-<hash>.mmd

   # Generate PNG using mmdc
   mmdc -i /tmp/diagram-<hash>.mmd -o /tmp/diagram-<hash>.png -b transparent
   ```

3. **Generate image for PlantUML** (if plantuml available):
   ```bash
   # Use PlantUML to generate PNG
   plantuml -tpng /tmp/diagram-<hash>.puml
   ```

4. **Replace diagram code block with placeholder**:
   ```markdown
   > TODO: add image /tmp/diagram-<hash>.png here
   ```

### Phase 3: Prepare Content with Placeholders

Transform the markdown content:

1. **Replace existing image references**:
   - Convert `![alt](path)` to:
     ```markdown
     > TODO: add image <absolute-path> here
     ```

2. **Replace generated diagrams** with their PNG paths (from Phase 2)

3. **Keep markdown formatting intact**:
   - Headers (`#`, `##`, `###`)
   - Lists (`-`, `*`, `1.`)
   - Tables (with proper pipe syntax)
   - Code blocks (with language specifiers)
   - Bold, italic, inline code

### Phase 4: Upload Using QuipEditor Tool

Use the `QuipEditor` tool available in the default Q agent:

1. **Use QuipEditor with contentFilePath**:
   ```bash
   # Upload entire markdown file at once
   QuipEditor(
     documentId="<quip-url>",
     contentFilePath="<absolute-path-to-markdown>",
     format="markdown",
     location=0  # append to document
   )
   ```

2. **For section-by-section uploads**:
   ```bash
   # First analyze document structure
   QuipEditor(
     documentId="<quip-url>",
     analyzeStructure=true,
     returnSectionIds=true
   )

   # Then append each section
   QuipEditor(
     documentId="<quip-url>",
     content="<markdown-section-content>",
     format="markdown",
     location=0  # append
   )
   ```

3. **CRITICAL: Validate the uploaded content immediately**:
   ```bash
   # Read back using QuipEditor
   QuipEditor(
     documentId="<quip-url>",
     analyzeStructure=true
   )
   # Verify structure matches expectations
   ```

### Phase 5: Validation and Fix

**After each section is uploaded, perform validation**:

1. **Check Lists** - CRITICAL: Bullet and Numbered lists behave DIFFERENTLY!

   **Bullet Lists** (`-` or `*`):
   - Usually render correctly with markdown format
   - Detection: Look for literal `-` or `*` characters instead of actual bullets
   - Fix if failed: Re-upload using `<ul><li>Item</li></ul>`

   **Numbered Lists** (`1.`, `2.`) - MOST COMMON FAILURE POINT:
   - Problem: Markdown numbered lists OFTEN render as plain paragraphs with literal `1.` text
   - Detection: Look for lines starting with `1.` as plain text instead of actual numbered list
   - Root cause: Quip's markdown parser poorly handles `1. Item` syntax

   **MANDATORY: Pre-convert numbered lists to HTML before upload:**
   ```markdown
   1. First item
   2. Second item
   ```
   MUST become:
   ```html
   <ol>
   <li>First item</li>
   <li>Second item</li>
   </ol>
   ```

   **For nested numbered lists:**
   ```html
   <ol>
   <li>First item
   <ol>
   <li>Nested first</li>
   <li>Nested second</li>
   </ol>
   </li>
   <li>Second item</li>
   </ol>
   ```

   **Fix for failed numbered lists:**
   - Delete the malformed content
   - Re-upload using HTML `<ol><li>...</li></ol>` format
   - Use QuipEditor with `format="html"` instead of `format="markdown"`

2. **Check Tables**:
   - Problem: Tables created but cells are empty
   - Detection: Read back content, verify table cells have content
   - Fix: Re-upload using proper Quip table HTML format:
     ```html
     <table>
       <tr><th>Header 1</th><th>Header 2</th></tr>
       <tr><td>Cell 1</td><td>Cell 2</td></tr>
     </table>
     ```

3. **Check Headers**:
   - Verify header levels are correct (h1, h2, h3)
   - Verify header text is preserved

4. **Check Code Blocks**:
   - Verify code blocks are formatted as code (not plain text)
   - Verify syntax highlighting if applicable

5. **Retry Logic**:
   - If validation fails, re-upload the section with corrected formatting
   - Maximum 2 retries per section
   - Log any persistent issues for manual review

### Phase 6: Summary Report

After all sections are uploaded, provide:

1. **Success Summary**:
   - Total sections uploaded
   - Number of images/diagrams with placeholders
   - List of generated diagram files (in `/tmp/`)

2. **Validation Results**:
   - Number of sections that required fixes
   - Types of issues encountered (lists, tables, etc.)
   - Any unresolved issues

3. **Next Steps**:
   - Instructions for uploading images manually
   - List of placeholder locations in the document
   - Generated diagram file paths for reference

## Markdown to Quip HTML Conversion Reference

**Bullet Lists** (usually work with markdown, but HTML is safer):
```markdown
- Item 1
- Item 2
```
becomes:
```html
<ul><li>Item 1</li><li>Item 2</li></ul>
```

**Numbered Lists** (MUST use HTML - markdown often fails!):
```markdown
1. First item
2. Second item
3. Third item
```
becomes:
```html
<ol><li>First item</li><li>Second item</li><li>Third item</li></ol>
```

**Tables**:
```markdown
| Col1 | Col2 |
|------|------|
| A    | B    |
```
becomes:
```html
<table><tr><th>Col1</th><th>Col2</th></tr><tr><td>A</td><td>B</td></tr></table>
```

**Headers**:
```markdown
# H1
## H2
```
becomes:
```html
<h1>H1</h1>
<h2>H2</h2>
```

**Code Blocks**:
````markdown
```python
code here
```
````
becomes:
```html
<pre><code class="language-python">code here</code></pre>
```

## Agent Selection

**IMPORTANT**: Always use the **default Q agent** (not amzn-docs) because it has the `QuipEditor` tool which can write to Quip documents.

## Command Construction

**CRITICAL: Always run q chat as a background process** to avoid timeouts.

```bash
# In Claude Code, use Bash tool with:
#   run_in_background: true
#   timeout: 600000  (10 minutes)
# Then monitor with BashOutput tool to track progress

q chat --trust-all-tools "Upload the markdown file '<absolute-file-path>' to Quip document '<quip-url>' using the QuipEditor tool..."
```

## Important Notes

- **Always validate after each section upload** - this is critical
- **NUMBERED LISTS ARE THE #1 FAILURE POINT** - Always verify numbered lists show actual numbers, not literal `1.` text
- **Bullet lists usually work** - markdown `-` or `*` syntax typically renders correctly
- **Tables are also common failure points** - verify all cells have content
- **Use absolute paths** for image placeholders
- **ALWAYS run q chat as a background process** with `run_in_background: true`
