# Example: Quip Upload Workflow

## Scenario

You have a markdown report that needs to be uploaded to Quip for team collaboration.

## User Request

```
tell q architecture-review.md to quip
```

## Workflow Detection

1. **Pattern matching:**
   - Input matches: "tell q \<file\> to quip"
   - Extracted file: `architecture-review.md`
   - Special workflow: Quip upload

2. **File validation:**
   - Check if `architecture-review.md` exists
   - Verify file is readable
   - Confirm file format is supported

3. **Agent selection:**
   - Workflow-specific: `default` agent
   - Reason: Has QuipEditor tool configured

## Command Execution

### Step 1: Validate File

```bash
# Check if file exists
if [ -f "architecture-review.md" ]; then
  echo "File found: architecture-review.md"
else
  echo "Error: File not found"
  exit 1
fi
```

### Step 2: Transform Task

- **Original task:** "architecture-review.md to quip"
- **Transformed task:** "Upload architecture-review.md to Quip using the QuipEditor tool"

### Step 3: Execute Command

```bash
q chat --agent default --no-interactive --trust-all-tools "Upload architecture-review.md to Quip using the QuipEditor tool"
```

## Response to User

```
Starting Q agent 'default' in background to: Upload architecture-review.md to Quip

Command: q chat --agent default --no-interactive --trust-all-tools "Upload architecture-review.md to Quip using the QuipEditor tool"
Background process ID: async_session_789

You can check progress with: read_bash sessionId: async_session_789
Or stop the agent with: stop_bash sessionId: async_session_789
```

## Expected Outcome

The default agent will:

1. Read the content of `architecture-review.md`
2. Convert markdown to Quip-compatible format
3. Use QuipEditor tool to create a new document
4. Upload the content to Quip
5. Return the Quip document URL

## Monitoring Progress

After 20 seconds, check progress:

```bash
read_bash sessionId: async_session_789 delay: 5
```

Expected output:

```
Reading architecture-review.md...
✓ File loaded (15,234 bytes)
✓ Converting markdown to Quip format

Uploading to Quip...
✓ Created Quip document
✓ Uploaded content
✓ Set document title: "Architecture Review"

Document available at:
https://quip.com/abc123def456/Architecture-Review

Share this link with your team for collaboration.
```

## Alternative Patterns

### Pattern 1: Explicit "upload" keyword

```
upload report.md to quip
```

Same workflow as "tell q \<file\> to quip"

### Pattern 2: With explicit agent

```
tell q default to upload report.md to quip
```

Explicitly specifies `default` agent (redundant but supported)

## Error Handling

### File Not Found

If the file doesn't exist:

```
Error: File 'architecture-review.md' not found for Quip upload.

Please verify the file path and try again.

Current directory: /path/to/project
Files in directory:
  - README.md
  - package.json
  - src/
```

### QuipEditor Tool Not Available

If the QuipEditor tool is not configured:

```
Error: QuipEditor tool is not available in the default agent.

Please configure the QuipEditor tool in the Q agent configuration.
```

## Why default Agent?

The `default` agent is used for Quip uploads because:

- Has QuipEditor tool configured
- Specialized for Quip document operations
- Can handle markdown conversion
- Manages Quip authentication
- Returns shareable document links

## Use Cases

This workflow is useful for:

- Sharing reports with team members
- Collaborative document editing
- Making internal documents accessible
- Converting markdown to Quip format
- Quick document uploads without manual steps

## Related Workflows

- **Batch upload:** Upload multiple files to Quip
- **Update existing:** Update existing Quip document
- **Convert and upload:** Convert from other formats before upload
