# Transfer Prompt Template

Use this prompt template when transferring markdown documents to Quip.

---

## Prompt for Q Chat / Claude

```text
I need to transfer a markdown document to Quip with proper formatting validation.

**Source Document**: [path/to/document.md]
**Target Quip Document**: [document_id or URL]
**Quip API Token**: [Set as environment variable QUIP_API_TOKEN]

Please follow the Quip Document Writer skill workflow:

1. **Pre-process the document**:
   - Convert ALL numbered lists to HTML <ol> format
   - Replace images with [TODO: INSERT IMAGE] placeholders
   - Replace Mermaid diagrams with [TODO: INSERT DIAGRAM] placeholders
   - Preserve all other content as-is

2. **Parse into sections**:
   - Split by ## (H2) headers
   - Create a section list with titles and content

3. **Upload sections one by one**:
   - Start with section 1
   - Upload to Quip
   - Wait 3-5 seconds for processing
   - Verify the section rendered correctly
   - Check for numbered list issues (literal "1." instead of formatted list)
   - Check for table issues (missing cells, wrong alignment)
   - If issues found, fix and re-upload
   - Move to next section only after verification passes

4. **Final verification**:
   - Review complete document in Quip
   - Create TODO list for manual tasks (images, diagrams)
   - Report any issues that need manual intervention

**Important**:
- ALWAYS convert numbered lists to HTML before upload
- Verify each section before proceeding
- Flag any tables with data corruption for manual review
- Don't skip sections even if they seem simple

Please start with section 1 and proceed sequentially.
```

---

## Customization Options

### For Specific Content Types

**Document with many images:**

```text
Note: This document contains [X] images. All will be replaced with placeholders.
Please create a comprehensive list of images to upload manually after transfer.
```

**Document with complex tables:**

```text
Note: This document contains [X] tables. Please verify each table after upload
and flag any with data corruption for manual HTML conversion.
```

**Document with Mermaid diagrams:**

```text
Note: This document contains [X] Mermaid diagrams. Replace each with a detailed
text description and preserve the original code for manual recreation.
```

### For Different Upload Strategies

**New document:**

```text
Create a new Quip document titled "[Document Title]" and upload all sections.
```

**Append to existing:**

```text
Append sections to existing Quip document [document_id]. Start after the
current content.
```

**Replace existing:**

```text
Replace the content of Quip document [document_id] with the new sections.
Clear existing content first.
```

### For Different Verification Levels

**Quick verification (bullet lists OK, numbered lists only):**

```text
Verification level: Quick
- Check numbered lists render as formatted lists (not literal "1.")
- Assume bullet lists and tables are OK unless obviously broken
```

**Standard verification (recommended):**

```text
Verification level: Standard
- Check all numbered lists render correctly
- Check bullet lists have actual bullet points
- Verify tables have all cells in correct positions
- Flag any obvious issues
```

**Thorough verification (high-stakes documents):**

```text
Verification level: Thorough
- Check every numbered list item individually
- Verify all bullet points render correctly
- Compare table data cell-by-cell with source
- Verify all links work
- Check code block formatting
- Validate header hierarchy
```

## Pre-Processing Instructions

### For Lists

```text
Pre-processing for lists:
1. Find all numbered lists (pattern: ^\d+\.)
2. Convert each to HTML <ol><li> format
3. Handle nested lists (parse indentation)
4. Preserve inline formatting in list items
5. Test conversion before upload
```

### For Images

```text
Pre-processing for images:
1. Find all ![alt](path) patterns
2. Find all <img> tags
3. Replace each with:
   [TODO: INSERT IMAGE]
   Name: <filename>
   Alt text: <alt_text>
   Original path: <path>
4. Keep track of all images for manual upload list
```

### For Diagrams

````text
Pre-processing for Mermaid diagrams:
1. Find all ```mermaid code blocks
2. Identify diagram type (flowchart, sequence, etc.)
3. Generate text description of diagram
4. Replace with:
   [TODO: INSERT DIAGRAM]
   Type: Mermaid <type>
   Description: <description>
   Original code: (preserved below)
5. Keep original code for reference
````

## Section Upload Template

```text
Uploading section [X] of [Y]: "[Section Title]"

Content preview:
[First 100 characters...]

Uploading...
[API call details]

Waiting 3 seconds for processing...

Verification:
- [ ] Section appears in document
- [ ] Header formatted correctly
- [ ] Numbered lists render as formatted lists (not literal numbers)
- [ ] Bullet lists have bullet points
- [ ] Tables have all cells
- [ ] Code blocks preserved
- [ ] Links work

Status: [PASS / FAIL]

[If FAIL, describe issue and retry strategy]
```

## Error Recovery Template

```text
Error detected in section [X]: [Issue description]

Recovery strategy:
1. [First attempt - e.g., "Convert markdown list to HTML"]
2. [Second attempt - e.g., "Upload as plain text with manual formatting note"]
3. [Fallback - e.g., "Flag for manual creation"]

Attempting recovery...
[Details of retry]

Result: [SUCCESS / FLAGGED FOR MANUAL FIX]
```

## Completion Report Template

```text
Transfer Complete

**Summary**:
- Total sections: [X]
- Successful: [Y]
- Required fixes: [Z]
- Manual tasks remaining: [N]

**Manual Tasks**:

Images to upload: [X]
1. [Filename] in section "[Section Name]"
2. [Filename] in section "[Section Name]"
...

Diagrams to create: [Y]
1. [Type] in section "[Section Name]" - [Description]
2. [Type] in section "[Section Name]" - [Description]
...

Tables to review: [Z]
1. Section "[Section Name]" - [Issue description]
2. Section "[Section Name]" - [Issue description]
...

**Issues Fixed During Transfer**:
- [List of issues that were automatically fixed]

**Overall Status**: [SUCCESS / SUCCESS WITH MANUAL TASKS / NEEDS REVIEW]

**Next Steps**:
1. Review document at [Quip URL]
2. Upload images as listed above
3. Create/insert diagrams as listed above
4. Review and fix tables as listed above
5. Final review and publish
```

## Tips for Using This Prompt

1. **Set environment variables first**:

   ```bash
   export QUIP_API_TOKEN="your-token-here"
   export QUIP_DOCUMENT_ID="document-id-or-create-new"
   ```

2. **Have markdown file ready**: Ensure file is accessible and readable

3. **Check Quip access**: Verify token has edit permissions for target document

4. **Allocate time**: Section-by-section transfer takes longer but is more reliable

5. **Monitor progress**: Watch for verification failures and be ready to intervene

6. **Keep source file**: Don't delete markdown until transfer is verified complete

7. **Manual tasks are normal**: Expect to upload images and create diagrams manually

## Example Usage

```text
I need to transfer the API documentation from api-docs.md to Quip.

Source: ./docs/api-docs.md
Target: New Quip document titled "API Documentation v2.0"
Token: Already set in QUIP_API_TOKEN

The document has:
- 12 sections
- 5 numbered lists (need HTML conversion)
- 8 images (need placeholders)
- 3 tables
- No Mermaid diagrams

Please transfer with standard verification level, and provide a complete
list of images to upload manually after transfer.

Start now.
```
