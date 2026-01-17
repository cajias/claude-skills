# Q Chat Integration Skill

## Objective

Enable Claude Code to delegate specific tasks to Amazon Q CLI agents running in the background with
full tool permissions. This skill acts as a bridge to leverage Q's specialized integrations (Quip,
ticketing systems, diagram generation) that Claude doesn't have direct access to.

## Prerequisites

Before using this skill, ensure:

1. **Amazon Q CLI is installed and configured:**

   ```bash
   q --version
   ```

2. **Authentication is active:**

   ```bash
   q auth status
   ```

3. **Bash tool is available** for command execution

4. **Working directory context** is available for providing full file paths

## Trigger Phrases

This skill activates when the user says:

- "tell Q to..."
- "ask Q to..."
- "have Q..."
- "q chat..."
- "delegate to Q..."
- Any variation explicitly requesting Q Chat assistance

## When to Use This Skill

### ✅ Use Q Chat For

- **Quip operations**: Updating, creating, or managing Quip documents (Q has QuipEditor tool)
- **Ticket creation**: Creating SIM tickets or other internal ticketing systems
- **Diagram generation**: Architecture diagrams, flow charts, visualizations
- **AWS-specific tasks**: Leveraging Q's AWS expertise for infrastructure tasks
- **Documentation generation**: When Q's specialized doc tools are beneficial
- **Internal integrations**: Any task requiring Amazon-specific tool integrations

### ❌ Don't Use Q Chat For

- **File operations**: Reading, editing, creating files (Claude can do this directly)
- **Code search**: Finding functions, patterns in code (use grep/glob)
- **Git operations**: Commits, branches, diffs (use git commands)
- **Simple questions**: General coding help, explanations (Claude can answer)
- **Code analysis**: Understanding existing code (Claude can analyze)

## Core Functionality

### Command Template

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "<USER_REQUEST>"
```

### Parameter Details

| Parameter           | Value              | Purpose                                       |
| ------------------- | ------------------ | --------------------------------------------- |
| `--model`           | claude-sonnet-4.5  | Specify the Claude model for Q to use         |
| `--no-interactive`  | (flag)             | Run without prompts (fire and forget)         |
| `--trust-all-tools` | (flag)             | Allow Q to execute all tools without approval |
| `<USER_REQUEST>`    | string (in quotes) | The specific task for Q to perform            |

### Execution Modes

**For quick tasks (< 30 seconds):**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "task" &
# Use bash tool with mode: "sync", initial_wait: 30
```

**For longer tasks (30 seconds - 2 minutes):**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "task" &
# Use bash tool with mode: "sync", initial_wait: 60-120
```

**For long-running tasks (> 2 minutes):**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "task" &
# Use bash tool with mode: "async", then monitor with read_bash
```

## Step-by-Step Workflow

### Phase 1: Parse User Request

**Identify the core task:**

1. Extract the action Q should perform
2. Identify relevant files, URLs, or resources
3. Determine task type (Quip, ticket, diagram, etc.)
4. Check if Q is actually needed (could Claude do it directly?)

**Examples:**

```text
User: "Tell Q to update the Quip doc at https://quip-amazon.com/ABC"
→ Action: Update Quip document
→ Resource: https://quip-amazon.com/ABC
→ Q needed: Yes (Claude doesn't have QuipEditor)

User: "Ask Q to read the README file"
→ Action: Read file
→ Q needed: No (Claude can read files directly)
→ Response: "I can read the README directly. Let me do that for you."
```

### Phase 2: Gather Context

**Prepare complete information:**

1. **Resolve file paths to absolute paths:**

   ```bash
   # If user says "the config file", find and use full path
   /home/runner/work/project/project/config/settings.json
   ```

2. **Extract relevant context:**
   - For bug reports: error details, stack traces, reproduction steps
   - For documentation: current state, what needs updating
   - For tickets: component, severity, impact, proposed fix

3. **Verify resources exist:**
   - Check if files mentioned actually exist
   - Validate URLs are complete

### Phase 3: Build Q Chat Command

**Construct the command:**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "<DETAILED_REQUEST>"
```

**Request formatting guidelines:**

1. **Be specific and complete:**

   ```text
   ❌ "Update the Quip doc"
   ✅ "Update the Quip document at https://quip-amazon.com/ABC123 with the contents of /home/runner/work/project/project/docs/api.md"
   ```

2. **Include full context for complex tasks:**

   ```text
   "Create a SIM ticket for authentication bug. Details:
   - Component: UserService (src/services/user.ts)
   - Error: JWT validation fails for valid tokens
   - Impact: Users getting 401 errors intermittently
   - Root cause: Token expiry check using wrong timezone
   - Fix: Updated timezone handling in validateToken() method"
   ```

3. **Escape quotes properly:**

   ```bash
   # Use single quotes in the request string
   "Update doc with summary: 'Project completed successfully'"
   ```

### Phase 4: Execute Command

**Choose execution mode:**

```bash
# For quick operations (Quip updates, simple queries)
bash(
  command: 'q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "..."',
  mode: "sync",
  initial_wait: 30
)

# For medium operations (ticket creation, simple diagrams)
bash(
  command: 'q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "..."',
  mode: "sync",
  initial_wait: 60
)

# For long operations (complex analysis, large docs)
bash(
  command: 'q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "..."',
  mode: "async"
)
# Then use read_bash to monitor progress
```

**Capture session information:**

```text
Session ID: bash_12345
Status: Running
Command: q chat --model claude-sonnet-4.5...
```

### Phase 5: Monitor Progress

**For synchronous execution:**

- Wait for command completion
- Capture output
- Report results to user

**For asynchronous execution:**

```bash
# Check status periodically
read_bash --session-id bash_12345 --delay 10

# Continue checking until complete
read_bash --session-id bash_12345 --delay 15
```

### Phase 6: Report Results

**Success response:**

```text
✓ Task delegated to Amazon Q successfully

Action: Updated Quip document
URL: https://quip-amazon.com/ABC123
Status: Completed
Duration: 15 seconds

Q has updated the document with the latest API documentation.
```

**In-progress response:**

```text
⏳ Task running in Amazon Q

Action: Creating SIM ticket
Session: bash_12345
Status: Running (30 seconds elapsed)

You can check progress by asking me to monitor the session.
```

**Error response:**

```text
❌ Q Chat task failed

Error: Authentication expired
Command: q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "..."

Suggested fix: Run 'q auth login' to reauthenticate.
```

## Common Task Patterns

### Pattern 1: Quip Document Update

**Trigger:**

```text
"Tell Q to update the Quip doc at [URL] with [content]"
```

**Implementation:**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Update the Quip document at [URL] with the contents of [ABSOLUTE_PATH]"
```

**Agent:** Uses default agent (has QuipEditor tool)

### Pattern 2: Ticket Creation

**Trigger:**

```text
"Ask Q to create a SIM/ticket for [issue]"
```

**Implementation:**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Create a SIM ticket with the following details: [DETAILED_CONTEXT]"
```

**Agent:** Uses default agent

### Pattern 3: Architecture Diagram

**Trigger:**

```text
"Tell Q to create an architecture diagram for [system]"
```

**Implementation:**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Create an architecture diagram for [system]. Include [specific components]."
```

**Agent:** Can use amzn-architecture agent for complex designs

### Pattern 4: AWS Infrastructure

**Trigger:**

```text
"Have Q review/create/update [AWS resource]"
```

**Implementation:**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Review the CDK stack for AWS best practices. Focus on [specific areas]."
```

**Agent:** Uses aws-expert agent for AWS tasks

### Pattern 5: Documentation Generation

**Trigger:**

```text
"Ask Q to generate documentation for [component]"
```

**Implementation:**

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Generate comprehensive documentation for [component]. Include examples and usage."
```

**Agent:** Uses amzn-docs agent for documentation tasks

## Agent Selection (Reference)

Q Chat can leverage specialized agents for different task types. While the basic command remains
the same, Q will internally route to the appropriate agent based on the task description.

| Agent               | Purpose                       | Keywords to Trigger                         |
| ------------------- | ----------------------------- | ------------------------------------------- |
| `default`           | General + Quip operations     | quip, document, general                     |
| `aws-expert`        | AWS infrastructure & services | aws, cdk, cloudformation, lambda            |
| `amzn-docs`         | Documentation specialist      | documentation, readme, docs, api-docs       |
| `amzn-architecture` | Architecture & design         | architecture, design, security, patterns    |
| `amzn-quality`      | Code quality & standards      | quality, linting, standards, best-practices |

**Note:** You don't need to explicitly specify the agent in the command. Q will automatically route
based on the task description keywords.

## Error Handling

### Common Errors and Solutions

**1. Q CLI Not Found:**

```text
Error: q: command not found
Solution: Install Amazon Q CLI: https://docs.aws.amazon.com/amazonq/
```

**2. Authentication Expired:**

```text
Error: Authentication required
Solution: Run 'q auth login' to reauthenticate
```

**3. Invalid Model:**

```text
Error: Model 'claude-sonnet-4.5' not found
Solution: Verify model name or use available model
```

**4. Tool Execution Denied:**

```text
Error: Tool execution not allowed
Solution: Ensure --trust-all-tools flag is included
```

**5. Task Timeout:**

```text
Error: Task exceeded timeout
Solution: Use async mode for long-running tasks
```

### Retry Strategy

If a Q task fails:

1. **Check the error output:**

   ```bash
   read_bash --session-id bash_xxxxx --delay 5
   ```

2. **Analyze the error:**
   - Authentication issue? → Re-authenticate
   - Missing context? → Add more details to request
   - Q CLI issue? → Check Q installation

3. **Retry with improvements:**

   ```bash
   q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
     "Previous attempt failed due to [reason]. Retry with additional context: ..."
   ```

## Important Notes

### Best Practices

1. **Always use absolute file paths**
   - ❌ `"Update with file.md"`
   - ✅ `"Update with /home/runner/work/project/project/file.md"`

2. **Provide complete context for tickets and reports**
   - Include component names, error details, impact, reproduction steps

3. **Choose appropriate execution mode**
   - Quick tasks: sync with short wait
   - Long tasks: async with monitoring

4. **Monitor important operations**
   - Capture session IDs
   - Check status for critical tasks
   - Verify completion before proceeding

5. **Don't over-delegate**
   - Only use Q for tasks requiring its specialized tools
   - Claude can handle most file, git, and code operations directly

### Security Considerations

1. **--trust-all-tools flag** allows Q to execute tools without prompts
   - Only use for trusted, well-defined tasks
   - Review Q's capabilities before delegating sensitive operations

2. **API keys and credentials** should not be included in Q chat requests
   - Q will use configured credentials automatically
   - Don't pass secrets in command line arguments

3. **File permissions** are inherited from the current user
   - Q can only access files the user can access
   - Verify file permissions before delegating file operations

## Examples

For detailed usage examples, see:

- `examples/usage-examples.md` - Comprehensive examples with before/after
- `config/agents.json` - Available Q agents and their capabilities

## Success Criteria

A successful Q Chat delegation should:

- ✓ Execute without requiring user input (non-interactive)
- ✓ Complete the specific task requested
- ✓ Provide clear status updates (running, completed, failed)
- ✓ Use appropriate execution mode for task duration
- ✓ Include full context and absolute paths
- ✓ Report meaningful results back to the user

## Limitations

1. **Q CLI dependency**: Requires Amazon Q CLI to be installed and configured
2. **Authentication**: Requires valid Q authentication (may expire)
3. **Tool availability**: Can only use tools available to Q CLI
4. **Amazon internal**: Some integrations may be Amazon-internal only
5. **Async monitoring**: Long-running tasks require manual status checks
6. **No direct output parsing**: Q's output is returned as-is to the user

## Related Skills

- **GitHub Issue Grooming**: For repository organization (Claude can do directly)
- **AI Writing Humanizer**: For text improvement (Claude can do directly)
- **Software Effort Estimation**: For codebase analysis (Claude can do directly)

## Version

1.0.0 - Initial release with basic delegation, monitoring, and agent awareness
