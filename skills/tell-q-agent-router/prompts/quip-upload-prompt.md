# Quip Upload Prompt Template

## Overview

This prompt template is used when the Quip upload workflow is detected. It transforms user input
like "tell q \<file\> to quip" into a structured prompt for the Q agent.

## Workflow Detection

The Quip upload workflow is triggered when the user input matches one of these patterns:

- `tell q <file> to quip`
- `upload <file> to quip`

## Pattern Matching

**Regex Pattern:**

```regex
tell q (.+?) to quip
```

**Capture Groups:**

- Group 1: File path (e.g., "report.md", "docs/architecture.md")

**Note:** The non-greedy quantifier `(.+?)` captures until the first occurrence of " to quip". For
file paths with spaces, ensure they are properly quoted or use `(.+)` if the pattern is the last
part of the input.

## Prompt Transformation

### Input Format

```text
tell q <file-path> to quip
```

### Output Format

```text
Upload <file-path> to Quip using the QuipEditor tool
```

## Examples

### Example 1: Simple File

**User Input:**

```text
tell q report.md to quip
```

**Transformed Prompt:**

```text
Upload report.md to Quip using the QuipEditor tool
```

**Full Command:**

```bash
q chat --agent default --no-interactive --trust-all-tools "Upload report.md to Quip using the QuipEditor tool"
```

### Example 2: File with Path

**User Input:**

```text
tell q docs/architecture-review.md to quip
```

**Transformed Prompt:**

```text
Upload docs/architecture-review.md to Quip using the QuipEditor tool
```

**Full Command:**

```bash
q chat --agent default --no-interactive --trust-all-tools "Upload docs/architecture-review.md to Quip using the QuipEditor tool"
```

### Example 3: Alternative Pattern

**User Input:**

```text
upload design-doc.md to quip
```

**Transformed Prompt:**

```text
Upload design-doc.md to Quip using the QuipEditor tool
```

**Full Command:**

```bash
q chat --agent default --no-interactive --trust-all-tools "Upload design-doc.md to Quip using the QuipEditor tool"
```

## Prompt Components

### Core Instruction

```text
Upload <file-path> to Quip
```

This tells the agent the primary action to perform.

### Tool Specification

```text
using the QuipEditor tool
```

This ensures the agent uses the correct tool for Quip integration.

### Complete Template

```text
Upload {file_path} to Quip using the QuipEditor tool
```

**Template Variables:**

- `{file_path}`: The file path extracted from user input (template placeholder, not bash syntax)

## Agent Selection

The Quip upload workflow always uses the **`default`** agent because:

- It has the QuipEditor tool configured
- It specializes in Quip document operations
- It can handle markdown to Quip format conversion
- It manages Quip authentication

## Pre-execution Validation

Before executing the prompt, validate:

1. **File exists:**

   ```bash
   # Replace $file_path with actual file path variable
   if [ -f "$file_path" ]; then
     echo "File found"
   else
     echo "Error: File not found"
     exit 1
   fi
   ```

2. **File is readable:**

   ```bash
   # Replace $file_path with actual file path variable
   if [ -r "$file_path" ]; then
     echo "File is readable"
   else
     echo "Error: File is not readable"
     exit 1
   fi
   ```

3. **File has content:**

   ```bash
   # Replace $file_path with actual file path variable
   if [ -s "$file_path" ]; then
     echo "File has content"
   else
     echo "Warning: File is empty"
   fi
   ```

## Expected Agent Behavior

When the Q agent receives this prompt, it should:

1. **Read the file:**
   - Load content from the specified file path
   - Parse markdown format if applicable

2. **Convert format:**
   - Transform markdown to Quip-compatible format
   - Preserve formatting (headers, lists, code blocks)

3. **Upload to Quip:**
   - Use QuipEditor tool to create new document
   - Set document title from filename or content
   - Upload formatted content

4. **Return result:**
   - Provide Quip document URL
   - Confirm successful upload
   - Include any relevant metadata

## Success Response Example

```text
Reading report.md...
✓ File loaded (15,234 bytes)
✓ Converting markdown to Quip format

Uploading to Quip...
✓ Created Quip document
✓ Uploaded content
✓ Set document title: "Report"

Document available at:
https://quip.com/abc123def456/Report

Share this link with your team for collaboration.
```

## Error Handling

### File Not Found

If the file doesn't exist:

```text
Error: File 'report.md' not found for Quip upload.

Please verify the file path and try again.

Current directory: /path/to/project
Files in directory:
  - README.md
  - package.json
  - src/
```

### QuipEditor Not Available

If the QuipEditor tool is not configured:

```text
Error: QuipEditor tool is not available in the default agent.

Please configure the QuipEditor tool in the Q agent configuration.
```

### Upload Failed

If the upload fails:

```text
Error: Failed to upload to Quip.

Reason: Authentication failed

Please check:
1. Quip credentials are configured
2. Network connectivity
3. Quip API access permissions
```

## Usage in Code

### Pattern Detection

```javascript
function detectQuipUpload(userInput) {
  const patterns = [/tell q (.+?) to quip/i, /upload (.+?) to quip/i];

  for (const pattern of patterns) {
    const match = userInput.match(pattern);
    if (match) {
      return {
        detected: true,
        filePath: match[1],
      };
    }
  }

  return { detected: false };
}
```

### Prompt Construction

```javascript
function buildQuipUploadPrompt(filePath) {
  return `Upload ${filePath} to Quip using the QuipEditor tool`;
}
```

### Complete Workflow

```javascript
function handleQuipUpload(userInput) {
  // 1. Detect pattern
  const detection = detectQuipUpload(userInput);
  if (!detection.detected) {
    return null;
  }

  // 2. Validate file
  if (!fileExists(detection.filePath)) {
    return {
      error: `File '${detection.filePath}' not found`,
    };
  }

  // 3. Build prompt
  const prompt = buildQuipUploadPrompt(detection.filePath);

  // 4. Build command
  const command = `q chat --agent default --no-interactive --trust-all-tools "${prompt}"`;

  return {
    agent: "default",
    prompt: prompt,
    command: command,
    filePath: detection.filePath,
  };
}
```

## Customization

### Adding Context

To add more context to the upload:

```text
Upload <file-path> to Quip using the QuipEditor tool. Set the document title to "<title>" and add tags: <tags>.
```

### Specifying Folder

To upload to a specific Quip folder:

```text
Upload <file-path> to Quip folder "<folder-name>" using the QuipEditor tool.
```

### Batch Upload

For multiple files:

```text
Upload the following files to Quip using the QuipEditor tool: <file1>, <file2>, <file3>
```

## Best Practices

1. **Always validate file paths** before constructing the prompt
2. **Use absolute paths** when possible to avoid ambiguity
3. **Escape special characters** in file paths if necessary
4. **Provide clear error messages** when validation fails
5. **Include file metadata** in success responses (size, format, etc.)

## Related Documentation

- [Quip Upload Example](../examples/quip-upload.md) - Complete workflow example
- [Special Workflows](../SKILL.md#special-workflows) - Full workflow documentation
- [Agent Configuration](../config/agents.json) - Default agent configuration
