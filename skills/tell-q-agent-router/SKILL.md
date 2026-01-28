# Tell Q Agent Router Skill

## Objective

Intelligently route tasks to the most appropriate Amazon Q CLI agent based on task type, with support
for explicit agent selection and special workflow patterns.

## Trigger Phrases

- "tell q to ..." - Delegate a task to Amazon Q agent
- "tell q \<file\> to quip" - Activate quip-upload workflow (uploads file to Quip)

## Prerequisites

1. **Amazon Q CLI installed:**

   ```bash
   # Check if Q CLI is available
   q --version
   ```

2. **Q agents configured:**
   - See `config/agents.json` for available agents and their capabilities

## Agent Selection Logic

When an agent is NOT explicitly specified, analyze the task and select the most appropriate agent:

| Task Type                | Agent               | Reason                                  |
| ------------------------ | ------------------- | --------------------------------------- |
| Quip Upload/Edit         | `default`           | Has QuipEditor tool                     |
| AWS/CDK/Infrastructure   | `aws-expert`        | AWS docs, CDK, API, diagram MCP servers |
| Documentation/Writing    | `amzn-docs`         | Doc generation, natural writing         |
| Architecture/Design      | `amzn-architecture` | Internal tools, GitLab access           |
| Code Quality/Linting     | `amzn-quality`      | Standards enforcement                   |
| Code Development         | `amzn-code-dev`     | Development specialist                  |
| General/Project-specific | `omega`             | Project context                         |
| Default/Uncertain        | `omega`             | Safe fallback                           |

### Agent Selection Algorithm

1. **Check for explicit agent mention:**
   - If task mentions "tell q aws-expert to..." → use `aws-expert`
   - If task mentions "tell q omega to..." → use `omega`
   - etc.

2. **Check for Quip workflow pattern:**
   - Pattern: "tell q \<file\> to quip" → use `default` agent
   - Pattern: "upload \<file\> to quip" → use `default` agent

3. **Analyze task keywords:**
   - Extract keywords from the task description
   - Match against agent keyword lists in `config/agents.json`
   - Score each agent based on keyword matches
   - Select agent with highest score

4. **Default fallback:**
   - If no clear match → use `omega` agent

## Command Building

### Standard Q Agent Command

```bash
q chat --agent <agent-name> --no-interactive --trust-all-tools "<task-prompt>"
```

### Parameters

| Parameter           | Purpose                 | Required |
| ------------------- | ----------------------- | -------- |
| `--agent <name>`    | Select specific Q agent | Yes      |
| `--no-interactive`  | Non-blocking execution  | Yes      |
| `--trust-all-tools` | Full tool permissions   | Yes      |
| task-prompt         | Task description        | Yes      |

### Execution Mode

- Use `bash` tool with `mode="async"` to run Q agent in background
- This allows monitoring progress while Q agent works
- Returns a sessionId for checking progress

## Workflow Steps

### Step 1: Parse User Input

Extract components from user request:

1. **Identify trigger phrase:**
   - "tell q to..."
   - "tell q \<file\> to quip"

2. **Extract task description:**
   - Everything after "tell q to"
   - For Quip workflow: file path and "to quip"

3. **Check for explicit agent:**
   - Look for agent name in the request
   - Examples: "tell q aws-expert to...", "tell q omega to..."

### Step 2: Select Agent

Apply the agent selection logic:

1. **If explicit agent mentioned:**
   - Validate agent exists in `config/agents.json`
   - Use specified agent

2. **If Quip workflow detected:**
   - Use `default` agent (has QuipEditor tool)

3. **If no explicit agent:**
   - Analyze task keywords
   - Match against agent capabilities
   - Select best-fit agent
   - Default to `omega` if uncertain

### Step 3: Build Command

Construct the Q CLI command:

```bash
q chat --agent <selected-agent> --no-interactive --trust-all-tools "<task-description>"
```

**Task Description Formatting:**

- For standard tasks: Use task as-is
- For Quip workflow: Transform to "Upload \<file\> to Quip"
- Escape special characters in task description
- Preserve quotes properly

### Step 4: Execute in Background

Use bash with async mode:

```bash
# Start Q agent in background
bash command: "q chat --agent <agent-name> --no-interactive --trust-all-tools \"<task>\""
mode: "async"
initial_wait: 10
```

This returns a `sessionId` for monitoring.

### Step 5: Report to User

Provide immediate feedback:

```text
Starting Q agent '<agent-name>' in background to: <brief-task-summary>

Command: q chat --agent <agent-name> --no-interactive --trust-all-tools "<task>"
Background process ID: <bash_sessionId>

You can check progress with: read_bash sessionId: <bash_sessionId>
Or stop the agent with: stop_bash sessionId: <bash_sessionId>
```

## Special Workflows

### Quip Upload Pattern

**Pattern Recognition:**

- Input: "tell q \<file\> to quip"
- Input: "upload \<file\> to quip"

**Workflow:**

1. **Detect pattern:**
   - Match regex: `tell q (.+?) to quip`
   - Extract file path from match group

2. **Validate file:**
   - Check if file exists
   - Confirm file is readable

3. **Select agent:**
   - Use `default` agent (has QuipEditor tool)

4. **Transform task:**
   - Original: "tell q report.md to quip"
   - Transformed: "Upload report.md to Quip using the QuipEditor tool"
   - See [prompts/quip-upload-prompt.md](prompts/quip-upload-prompt.md) for detailed template

5. **Execute:**
   - Run Q agent with transformed task
   - Monitor progress

## Response Format

### Success Response

```text
Starting Q agent '<agent-name>' in background to: <brief-task-summary>

Command: q chat --agent <agent-name> --no-interactive --trust-all-tools "<task>"
Background process ID: <sessionId>

You can check progress with: read_bash sessionId: <sessionId>
Or stop the agent with: stop_bash sessionId: <sessionId>
```

### Error Responses

**Agent Not Found:**

```text
Error: Agent '<agent-name>' not found.

Available agents:
- aws-expert: AWS architecture, CDK, API, diagrams
- amzn-docs: Documentation, Natural writing
- amzn-architecture: Design, Security, Internal systems
- amzn-quality: Code quality, Standards
- amzn-code-dev: Code development
- default: QuipEditor, General
- omega: Project context
```

**Q CLI Not Available:**

```text
Error: Amazon Q CLI (q) is not installed or not in PATH.

To install Q CLI, follow instructions at: <installation-url>
```

**File Not Found (Quip workflow):**

```text
Error: File '<file-path>' not found for Quip upload.

Please verify the file path and try again.
```

## Examples

### Example 1: Explicit Agent Selection

**User Input:**

```text
tell q aws-expert to create a CDK stack for a Lambda function with S3 trigger
```

**Agent Selection:**

- Explicit agent: `aws-expert`
- Task: "create a CDK stack for a Lambda function with S3 trigger"

**Command:**

```bash
q chat --agent aws-expert --no-interactive --trust-all-tools "create a CDK stack for a Lambda function with S3 trigger"
```

### Example 2: Automatic Agent Selection (AWS)

**User Input:**

```text
tell q to deploy a serverless API with Lambda and API Gateway
```

**Agent Selection:**

- No explicit agent
- Keywords detected: "serverless", "Lambda", "API Gateway"
- Best match: `aws-expert` (AWS-related keywords)

**Command:**

```bash
q chat --agent aws-expert --no-interactive --trust-all-tools "deploy a serverless API with Lambda and API Gateway"
```

### Example 3: Documentation Task

**User Input:**

```text
tell q to write comprehensive API documentation for our REST endpoints
```

**Agent Selection:**

- No explicit agent
- Keywords detected: "write", "documentation", "API"
- Best match: `amzn-docs` (documentation specialist)

**Command:**

```bash
q chat --agent amzn-docs --no-interactive --trust-all-tools "write comprehensive API documentation for our REST endpoints"
```

### Example 4: Quip Upload Workflow

**User Input:**

```text
tell q report.md to quip
```

**Workflow Detection:**

- Pattern matched: "tell q \<file\> to quip"
- File: `report.md`
- Special workflow: Quip upload

**Agent Selection:**

- Workflow-specific: `default` agent (has QuipEditor)

**Command:**

```bash
q chat --agent default --no-interactive --trust-all-tools "Upload report.md to Quip using the QuipEditor tool"
```

### Example 5: Code Development

**User Input:**

```text
tell q to implement a new authentication middleware in Express
```

**Agent Selection:**

- No explicit agent
- Keywords detected: "implement", "code", "middleware"
- Best match: `amzn-code-dev` (development specialist)

**Command:**

```bash
q chat --agent amzn-code-dev --no-interactive --trust-all-tools "implement a new authentication middleware in Express"
```

### Example 6: Code Quality Review

**User Input:**

```text
tell q to review and lint all TypeScript files for standards compliance
```

**Agent Selection:**

- No explicit agent
- Keywords detected: "review", "lint", "standards"
- Best match: `amzn-quality` (quality specialist)

**Command:**

```bash
q chat --agent amzn-quality --no-interactive --trust-all-tools "review and lint all TypeScript files for standards compliance"
```

## Monitoring Progress

After starting a Q agent, you can:

### Check Progress

```bash
read_bash sessionId: <sessionId> delay: 5
```

This reads the latest output from the Q agent.

### Stop Agent

```bash
stop_bash sessionId: <sessionId>
```

This terminates the running Q agent.

## Error Handling

### Handle Q CLI Errors

1. **Check if Q CLI is available:**

   ```bash
   which q || echo "Q CLI not found"
   ```

2. **Validate agent exists:**
   - Load `config/agents.json`
   - Check if selected agent is in the list

3. **Handle execution errors:**
   - Monitor bash output for errors
   - Report errors to user
   - Provide troubleshooting guidance

### Common Issues

| Issue             | Solution                                         |
| ----------------- | ------------------------------------------------ |
| Q CLI not found   | Install Q CLI or add to PATH                     |
| Agent not found   | Check agent name spelling, list available agents |
| Permission denied | Run with appropriate permissions                 |
| Task timeout      | Increase wait time or check Q agent logs         |

## Best Practices

1. **Agent Selection:**
   - Use explicit agent for specialized tasks
   - Let automatic selection handle general tasks
   - Default to `omega` when uncertain

2. **Task Description:**
   - Be specific and clear
   - Include relevant context
   - Avoid ambiguous instructions

3. **Monitoring:**
   - Check progress periodically for long-running tasks
   - Review output for errors
   - Stop agent if task is taking too long

4. **Quip Workflow:**
   - Verify file exists before uploading
   - Use descriptive file names
   - Ensure file format is supported by Quip

## Limitations

- Requires Amazon Q CLI to be installed and configured
- Agent selection is keyword-based and may not always be perfect
- Background execution requires monitoring for completion
- Quip workflow requires QuipEditor tool to be configured in Q agent
- Some agents may not have access to certain tools or resources

## Related Tools

- Amazon Q CLI (`q`)
- Background process management (bash async mode)
- File system operations for Quip workflow

## Success Metrics

After implementing this skill, you should be able to:

✓ Delegate tasks to Q agents with simple "tell q to..." commands
✓ Automatically select the most appropriate agent based on task type
✓ Run Q agents in background with progress monitoring
✓ Upload files to Quip with a simple workflow pattern
✓ Override automatic selection with explicit agent names
✓ Get immediate feedback about running agents
✓ Monitor and control background Q agent processes
