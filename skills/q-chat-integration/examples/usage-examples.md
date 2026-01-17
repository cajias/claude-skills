# Q Chat Integration - Usage Examples

This document provides detailed examples of how to use the Q Chat Integration skill to delegate
tasks to Amazon Q CLI agents.

## Basic Usage

### Example 1: Update Quip Document

**User Request:**

```text
Tell Q to update the Quip document at https://quip-amazon.com/ABCxyz123 with the contents of
docs/architecture.md
```

**Claude Action:**

Execute the following command in the background:

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Update the Quip document at https://quip-amazon.com/ABCxyz123 with the contents of /home/runner/work/project/project/docs/architecture.md"
```

**Expected Response:**

```text
✓ Task delegated to Amazon Q
  Command: q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "..."
  Status: Running in background
  Session ID: bash_12345

You can monitor progress by checking the session or waiting for Q to complete.
```

---

### Example 2: Create SIM Ticket

**User Request:**

```text
Ask Q to create a SIM ticket for the authentication bug we just fixed
```

**Claude Action:**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Create a SIM ticket for the authentication bug fix. Details: Fixed issue with JWT token validation in the auth middleware that was causing intermittent 401 errors for valid users."
```

**Expected Response:**

```text
✓ Task delegated to Amazon Q
  Command: q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "..."
  Status: Running in background
  Session ID: bash_67890

Q will create the ticket and provide the ticket number when complete.
```

---

### Example 3: Generate Architecture Diagram

**User Request:**

```text
Tell Q to create an architecture diagram for our EventBridge setup
```

**Claude Action:**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Create an architecture diagram for the EventBridge setup in this project. Include event sources, rules, targets, and DLQ configuration."
```

**Expected Response:**

```text
✓ Task delegated to Amazon Q
  Command: q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "..."
  Status: Running in background
  Session ID: bash_11111

Q will analyze the codebase and generate the architecture diagram.
```

---

## Advanced Usage

### Example 4: AWS Infrastructure Task

**User Request:**

```text
Have Q review our CDK stack for best practices
```

**Claude Action:**

Since this is an AWS infrastructure task, Q will use the aws-expert agent:

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Review the CDK stack in this project for AWS best practices. Check for security issues, cost optimization opportunities, and architectural improvements."
```

---

### Example 5: Documentation Generation

**User Request:**

```text
Tell Q to generate API documentation from our OpenAPI spec
```

**Claude Action:**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Generate comprehensive API documentation from the OpenAPI specification file. Include examples, authentication details, and error codes."
```

---

### Example 6: Multiple File Upload to Quip

**User Request:**

```text
Ask Q to create a new Quip document with all markdown files from the docs/ folder
```

**Claude Action:**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Create a new Quip document and populate it with the contents of all markdown files from /home/runner/work/project/project/docs/. Organize sections by file name."
```

---

## Context-Rich Examples

### Example 7: Bug Report with Full Context

**User Request:**

```text
Tell Q to create a detailed bug report for the memory leak we found
```

**Claude Action:**

Claude should gather context before delegating:

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Create a detailed bug report for a memory leak issue. Details:
  - Component: UserService in src/services/user.ts
  - Symptom: Memory usage grows unbounded when processing large user batches
  - Root cause: Event listeners not being cleaned up in processUserBatch() method
  - Impact: Server crashes after ~1000 user batch operations
  - Reproduction: Run batch processor with 100+ batches
  - Proposed fix: Add cleanup in finally block of processUserBatch()"
```

---

### Example 8: Code Review Request

**User Request:**

```text
Have Q do a security review of our authentication endpoints
```

**Claude Action:**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Perform a comprehensive security review of the authentication endpoints in this project. Focus on:
  - JWT token validation
  - Password hashing and storage
  - Session management
  - Rate limiting
  - Input validation
  - CSRF protection
  Provide specific recommendations with code examples."
```

---

## Monitoring Task Progress

### Checking Status

After delegating a task, you can check its status:

```bash
# Using the session ID from the delegation response
read_bash --session-id bash_12345 --delay 10
```

### Long-Running Tasks

For tasks that take longer, adjust the initial wait time:

```bash
# For operations that might take 2-3 minutes
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Generate comprehensive test suite for the entire API" &

# Then check periodically
sleep 30 && read_bash --session-id bash_xxxxx --delay 10
```

---

## When NOT to Use Q Chat

### Tasks Claude Can Handle Directly

Don't delegate these to Q:

```text
❌ "Tell Q to read the README file"
   → Claude can read files directly

❌ "Ask Q to search for TODO comments"
   → Claude has grep/search tools

❌ "Have Q commit these changes"
   → Claude has git tools

❌ "Tell Q to explain this function"
   → Claude can analyze code directly
```

### Use Q Chat for

```text
✓ Quip document operations (Q has QuipEditor tool)
✓ Creating tickets in internal systems (SIM, etc.)
✓ Generating diagrams or visualizations
✓ Tasks requiring special Amazon/internal integrations
✓ Operations that need specific Q agent expertise
```

---

## Error Handling

### What to Do If Q Task Fails

1. **Check the error output:**

   ```bash
   read_bash --session-id bash_xxxxx --delay 5
   ```

2. **Common issues:**
   - Q CLI not installed → Install Amazon Q CLI
   - Authentication expired → Run `q auth login`
   - Invalid model → Check model name spelling
   - Permission denied → Verify tool permissions

3. **Retry with more context:**

   ```bash
   q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
     "Previous attempt failed. Retry task with additional context: ..."
   ```

---

## Best Practices

### 1. Be Specific with File Paths

**Bad:**

```text
"Tell Q to update the Quip doc with the architecture file"
```

**Good:**

```text
"Tell Q to update the Quip document at https://quip-amazon.com/ABC123 with the contents of /home/runner/work/project/project/docs/architecture/system-design.md"
```

### 2. Provide Full Context

**Bad:**

```text
"Ask Q to create a ticket"
```

**Good:**

```text
"Ask Q to create a SIM ticket for the bug we just fixed in the authentication middleware. Include: component name, error description, root cause, impact, and the fix we implemented."
```

### 3. Use Appropriate Wait Times

```bash
# Quick tasks (< 30 seconds)
mode: "sync", initial_wait: 30

# Medium tasks (30 seconds - 2 minutes)
mode: "sync", initial_wait: 60

# Long tasks (> 2 minutes)
mode: "async" with periodic checks
```

### 4. Monitor Background Tasks

Always capture the session ID and check status for important operations:

```text
✓ Delegated to Q (session: bash_12345)
  → Checking status...
  → Task completed successfully
```

---

## Integration with Other Tools

### Combining with Claude's Direct Capabilities

**Workflow:**

1. Claude analyzes the codebase (using grep, file reading)
2. Claude gathers context and prepares summary
3. Claude delegates specific action to Q (Quip update, ticket creation)
4. Claude monitors Q's progress
5. Claude confirms completion to user

**Example:**

```text
User: "Analyze our API and have Q update the Quip doc"

Claude:
1. Analyzes API code (grep, view files)
2. Generates summary
3. Delegates: "Tell Q to update Quip doc at URL with this summary: ..."
4. Monitors Q task
5. Confirms: "✓ Analysis complete and Quip doc updated"
```

---

## Version History

- **1.0.0** - Initial examples covering basic delegation, monitoring, and best practices
