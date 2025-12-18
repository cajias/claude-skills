# Quip Document Writer Skill

## Objective

Transfer markdown documents to Quip with proper formatting validation, handling the common issues
with lists, tables, and diagrams that occur during bulk uploads.

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

## Core Strategy: Section-by-Section Transfer

Instead of writing the entire markdown file at once:

1. **Parse the markdown into sections** (split by `##` headers)
2. **Write each section individually** to Quip
3. **Verify each section** before moving to the next
4. **Handle special content** (images, diagrams, tables, lists) with care

## Content Handling Rules

### Numbered Lists (CRITICAL - OFTEN FAIL)

**Problem**: Markdown numbered lists (`1.`, `2.`) often render as plain paragraphs in Quip

**Detection**: Look for literal `1.` at start of lines instead of actual numbered list

**MANDATORY PRE-PROCESSING**:

Before uploading any section with numbered lists, convert markdown to HTML:

```markdown
1. First item
2. Second item
3. Third item
```

MUST become:

```html
<ol>
  <li>First item</li>
  <li>Second item</li>
  <li>Third item</li>
</ol>
```

**Nested numbered lists**:

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

**Mixed lists (bullet inside numbered)**:

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

**Mixed lists (numbered inside bullet)**:

```html
<ul>
  <li>
    First bullet
    <ol>
      <li>Sub numbered 1</li>
      <li>Sub numbered 2</li>
    </ol>
  </li>
  <li>Second bullet</li>
</ul>
```

### Bullet Lists (Usually Work)

- Markdown syntax (`-` or `*`) typically renders correctly
- **Verification Required**: After upload, confirm items appear with bullet points, not literal
  characters
- If verification fails, convert to HTML `<ul>` tags like numbered lists

### Images (`![alt](path)` or HTML `<img>`)

**DO NOT** attempt to upload images programmatically.

**Replacement Strategy**:

```text
[TODO: INSERT IMAGE]
Name: <filename>
Alt text: <alt_text>
Original path: <path>
```

**Example**:

```text
[TODO: INSERT IMAGE]
Name: architecture-diagram.png
Alt text: System architecture showing three-tier design
Original path: ./images/architecture-diagram.png
```

### Mermaid Diagrams

**Detection**: Code blocks with `mermaid` language identifier

**Replacement Strategy**:

````text
[TODO: INSERT DIAGRAM]
Type: Mermaid <diagram_type>
Description: <brief_description>

Original code (in markdown):
    ```mermaid
    <diagram_code>
    ```
````

**Example**:

````text
[TODO: INSERT DIAGRAM]
Type: Mermaid flowchart
Description: User authentication flow showing login, validation, and session creation

Original code (in markdown):
    ```mermaid
    flowchart TD
        A[Start] --> B{Login?}
        B -->|Yes| C[Validate]
        B -->|No| D[Register]
    ```
````

### Tables

**Handling**:

1. Upload table as markdown first
2. **Verify after upload**: Check that all cells contain correct data
3. **Common issues**:
   - Cell values may shift columns
   - Empty cells may collapse
   - Alignment may be lost
4. **If verification fails**:
   - Flag the table for manual review
   - Consider converting to HTML `<table>` tags
   - Document which rows/columns have issues

### Code Blocks

**Handling**:

- Code blocks with syntax highlighting usually work
- Verify that indentation is preserved
- Check that special characters are not escaped incorrectly
- Long code blocks may need to be split

### Headers

**Handling**:

- H1 (`#`) becomes document title (use only once)
- H2 (`##`) becomes section headers
- H3-H6 (`###` through `######`) become nested headers
- **Avoid** using H1 multiple times in a document

## Step-by-Step Workflow

### Phase 1: Pre-Processing

1. **Read the markdown file**

   ```bash
   cat document.md
   ```

1. **Identify all numbered lists** in the document
   - Search for patterns: `^\d+\.` (lines starting with number, dot, space)
   - Note line numbers and context

1. **Convert numbered lists to HTML**
   - For each numbered list section:
     - Parse the list structure (handle nesting)
     - Generate proper HTML `<ol>` and `<li>` tags
     - Preserve any nested bullet lists as `<ul>` tags
     - Replace original markdown with HTML

1. **Replace images with placeholders**
   - Find all `![alt](path)` patterns
   - Find all `<img>` tags
   - Replace each with standardized placeholder format

1. **Replace Mermaid diagrams with placeholders**
   - Find all code blocks with `mermaid` language
   - Replace each with standardized diagram placeholder format

1. **Save pre-processed markdown** to temporary file

### Phase 2: Section Parsing

1. **Split document by H2 headers** (`##`)

   ```python
   import re

   def split_by_headers(content):
       sections = []
       current_section = {"title": "Introduction", "content": ""}

       for line in content.split('\n'):
           if line.startswith('## '):
               if current_section["content"].strip():
                   sections.append(current_section)
               current_section = {
                   "title": line[3:].strip(),
                   "content": ""
               }
           else:
               current_section["content"] += line + '\n'

       if current_section["content"].strip():
           sections.append(current_section)

       return sections
   ```

2. **Create section list** with metadata:
   - Section number
   - Section title
   - Section content
   - Special content flags (has tables, has code, has lists)

### Phase 3: Upload Sections

**For each section**:

1. **Prepare section content**
   - Add section header if not present
   - Ensure proper spacing

2. **Upload to Quip**

   ```bash
   # Using Quip API (example with curl)
   curl -X POST "https://platform.quip.com/1/threads/edit-document" \
     -H "Authorization: Bearer $QUIP_API_TOKEN" \
     -d "thread_id=$DOCUMENT_ID" \
     -d "content=$SECTION_CONTENT" \
     -d "format=markdown" \
     -d "operation=append"
   ```

3. **Wait for processing**
   - Allow 2-5 seconds for Quip to process the content

4. **Retrieve and verify**

   ```bash
   curl -X GET "https://platform.quip.com/1/threads/$DOCUMENT_ID" \
     -H "Authorization: Bearer $QUIP_API_TOKEN"
   ```

5. **Check for issues**:
   - **Numbered lists**: Verify they appear as actual numbered lists, not plain text with `1.`
   - **Bullet lists**: Verify they appear with bullet points
   - **Tables**: Verify all cells contain correct data
   - **Code blocks**: Verify formatting is preserved

6. **If issues found**:
   - Log the issue with section number and type
   - Attempt fix:
     - For lists: Try HTML version
     - For tables: Try HTML version or flag for manual review
   - Re-upload section if fix applied
   - Re-verify

7. **Move to next section** only after current section is verified

### Phase 4: Final Verification

1. **Review complete document** in Quip UI

2. **Create TODO list** for manual tasks:
   - List all image placeholders with filenames
   - List all diagram placeholders with descriptions
   - List any tables flagged for manual review
   - List any other issues found during verification

3. **Document the transfer**:
   - Total sections uploaded
   - Number of issues encountered and resolved
   - Number of issues requiring manual intervention
   - List of manual tasks remaining

### Phase 5: Manual Follow-Up Instructions

Provide clear instructions for manual tasks:

```text
## Manual Tasks Required

### Images to Upload (X items)
1. Upload `architecture-diagram.png` to section "System Design"
   - Location: Search for "[TODO: INSERT IMAGE]" with name "architecture-diagram.png"
   - Alt text: System architecture showing three-tier design

### Diagrams to Create (X items)
1. Create Mermaid flowchart in section "Authentication Flow"
   - Location: Search for "[TODO: INSERT DIAGRAM]" with type "Mermaid flowchart"
   - Use provided diagram code to recreate manually or as image

### Tables to Review (X items)
1. Review table in section "API Endpoints"
   - Issue: Cell alignment may be incorrect
   - Verify all endpoint URLs are in correct column
```

## Error Handling

### Common Errors and Solutions

1. **API Authentication Failure**
   - Error: `401 Unauthorized`
   - Solution: Verify `QUIP_API_TOKEN` is valid and not expired
   - Check token permissions include document edit access

2. **Document Not Found**
   - Error: `404 Not Found`
   - Solution: Verify `DOCUMENT_ID` is correct
   - Check that token has access to the document

3. **Rate Limiting**
   - Error: `429 Too Many Requests`
   - Solution: Implement exponential backoff
   - Wait 60 seconds before retrying
   - Reduce upload frequency

4. **Content Too Large**
   - Error: `413 Payload Too Large`
   - Solution: Split section into smaller chunks
   - Upload paragraph by paragraph if needed

5. **Numbered List Still Renders as Plain Text**
   - Issue: Even HTML version shows literal numbers
   - Solution: Try different HTML format:
     - Add `type="1"` attribute to `<ol>`
     - Use `<ol style="list-style-type: decimal;">`
     - As last resort, flag for manual creation in Quip UI

6. **Table Data Corrupted**
   - Issue: Cell values in wrong columns or lost
   - Solution: Convert to HTML `<table>` format
   - If still fails, flag for manual creation

## Best Practices

1. **Always Pre-Process Numbered Lists**
   - Never upload markdown numbered lists directly
   - Always convert to HTML first
   - Saves time and reduces failures

2. **Verify After Each Section**
   - Don't wait until end to check
   - Catch issues early when easier to fix
   - Prevents cascading problems

3. **Keep Original Markdown**
   - Don't delete source file
   - Keep pre-processed version for reference
   - Useful for debugging and re-attempts

4. **Use Descriptive Placeholders**
   - Include enough context for manual insertion
   - Preserve alt text and descriptions
   - Makes follow-up tasks easier

5. **Document Everything**
   - Log all issues encountered
   - Note which solutions worked
   - Create clear TODO list for manual tasks

6. **Test with Small Section First**
   - Upload one section completely before proceeding
   - Verify the process works end-to-end
   - Adjust strategy if needed

## API Reference

### Quip API Endpoints

**Append to Document**:

```bash
POST https://platform.quip.com/1/threads/edit-document
Headers:
  Authorization: Bearer {api_token}
Body:
  thread_id: {document_id}
  content: {markdown_content}
  format: markdown
  operation: append
```

**Get Document Content**:

```bash
GET https://platform.quip.com/1/threads/{document_id}
Headers:
  Authorization: Bearer {api_token}
```

**Create New Document**:

```bash
POST https://platform.quip.com/1/threads/new-document
Headers:
  Authorization: Bearer {api_token}
Body:
  title: {document_title}
  content: {initial_content}
  format: markdown
```

### Environment Variables

Set these before starting:

```bash
export QUIP_API_TOKEN="your-api-token-here"
export QUIP_DOCUMENT_ID="document-id-or-create-new"
```

Get API token from: <https://quip.com/dev/token>

## Example Workflow

### Complete Transfer Example

**Input**: `technical-spec.md` (50 KB, 15 sections, multiple numbered lists, 5 images, 2 tables)

**Process**:

1. Pre-process (2 minutes):
   - Convert 8 numbered lists to HTML
   - Replace 5 images with placeholders
   - No Mermaid diagrams

2. Parse into 15 sections (10 seconds)

3. Upload sections sequentially (15 minutes):
   - Section 1-3: Success on first try
   - Section 4: Numbered list issue, fixed with HTML, re-uploaded
   - Section 5-10: Success on first try
   - Section 11: Table alignment issue, flagged for manual review
   - Section 12-15: Success on first try

4. Final verification (5 minutes):
   - All sections present
   - All lists rendering correctly
   - 1 table needs manual review

5. Manual tasks documented (2 minutes):
   - 5 images to upload
   - 1 table to review

**Total Time**: ~25 minutes automated + manual tasks  
**Success Rate**: 14/15 sections perfect, 1 needs minor fix

## Dependencies

- Quip API access (get token from <https://quip.com/dev/token>)
- Markdown parser (Python `markdown` library or similar)
- HTTP client (curl, requests, etc.)
- Text processing tools (sed, awk, or Python)

## Related Skills

- Markdown linting and formatting
- API authentication and error handling
- Content migration and validation
- Document structure analysis
