# Q Chat Integration Skill

Delegate tasks to Amazon Q CLI agents with specialized tool integrations that Claude doesn't have
direct access to.

## Overview

This skill enables Claude Code to seamlessly delegate specific tasks to Amazon Q CLI agents running
in the background. It's designed for operations that require Q's specialized integrations like
Quip document management, ticketing systems, diagram generation, and AWS-specific expertise.

## What It Does

1. **Recognizes** when the user wants to delegate to Q ("tell Q to...", "ask Q to...")
2. **Validates** that Q is actually needed (vs. Claude handling it directly)
3. **Gathers** complete context (file paths, URLs, detailed task description)
4. **Executes** Q chat with proper flags (`--no-interactive`, `--trust-all-tools`)
5. **Monitors** task progress and reports status back to the user

## When to Use

### ✅ Perfect For Q Chat

- **Quip Operations**: Create, update, or manage Quip documents (Q has QuipEditor tool)
- **Ticket Creation**: Create SIM tickets or other internal ticketing system entries
- **Diagram Generation**: Generate architecture diagrams, flow charts, visualizations
- **AWS Tasks**: Leverage Q's AWS expertise for infrastructure reviews and generation
- **Documentation**: When Q's specialized documentation tools provide value
- **Internal Integrations**: Tasks requiring Amazon-specific tool integrations

### ❌ Don't Use Q Chat For

- File operations (reading, editing, creating) - Claude can do this
- Code search (grep, glob) - Claude has these tools
- Git operations (commits, branches) - Claude handles git directly
- Code analysis and explanations - Claude can analyze code
- Simple questions - Claude can answer without Q

## Quick Start

### Basic Usage

Simply ask Claude to delegate a task to Q:

```text
"Tell Q to update the Quip document at https://quip-amazon.com/ABC123 with the contents of
docs/architecture.md"
```

Claude will:

1. Resolve the full file path
2. Build the Q chat command
3. Execute it in the background
4. Report status and results

### Common Patterns

#### Update Quip Document

```text
User: "Tell Q to update the Quip doc at [URL] with [file]"

Claude executes:
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Update the Quip document at [URL] with the contents of [FULL_PATH]"
```

#### Create Ticket

```text
User: "Ask Q to create a SIM ticket for this bug"

Claude executes:
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Create a SIM ticket for: [detailed bug context]"
```

#### Generate Architecture Diagram

```text
User: "Have Q create an architecture diagram for our EventBridge setup"

Claude executes:
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
  "Create an architecture diagram for the EventBridge setup in this project"
```

## Key Features

### Non-Interactive Execution

All Q commands run with `--no-interactive` flag, meaning they execute without waiting for user
input. This is essential for automation and background execution.

### Full Tool Permissions

Commands include `--trust-all-tools` flag, allowing Q to execute all necessary tools
autonomously. This eliminates confirmation prompts and enables fire-and-forget operation.

### Background Monitoring

Long-running tasks execute in the background with session tracking. Claude monitors progress and
reports status updates.

### Intelligent Routing

While you don't specify agents explicitly, Q intelligently routes tasks to specialized agents:

- **AWS tasks** → aws-expert
- **Documentation** → amzn-docs
- **Architecture** → amzn-architecture
- **Code quality** → amzn-quality
- **Quip operations** → default (has QuipEditor)

### Context Enrichment

Before delegating, Claude:

- Resolves relative paths to absolute paths
- Gathers relevant context from the codebase
- Includes error details, stack traces, or other relevant information
- Ensures Q has everything needed to complete the task

## Prerequisites

1. **Amazon Q CLI installed and configured:**

   ```bash
   q --version
   ```

2. **Active authentication:**

   ```bash
   q auth status
   ```

   If expired, reauthenticate:

   ```bash
   q auth login
   ```

3. **Bash tool available** (Claude's standard bash execution capability)

## Command Structure

All Q Chat delegations use this command pattern:

```bash
q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools "<REQUEST>"
```

Where:

- `--model claude-sonnet-4.5` - Specifies the Claude model for Q to use
- `--no-interactive` - Runs without prompts (fire and forget)
- `--trust-all-tools` - Allows Q to execute tools without confirmation
- `<REQUEST>` - Your detailed task description in quotes

## Execution Modes

### Quick Tasks (< 30 seconds)

```bash
# Synchronous with 30 second wait
bash(command: "q chat ...", mode: "sync", initial_wait: 30)
```

Use for: Simple Quip updates, quick queries

### Medium Tasks (30 seconds - 2 minutes)

```bash
# Synchronous with 60-120 second wait
bash(command: "q chat ...", mode: "sync", initial_wait: 60)
```

Use for: Ticket creation, simple diagrams

### Long Tasks (> 2 minutes)

```bash
# Asynchronous with monitoring
bash(command: "q chat ...", mode: "async")
# Then monitor with read_bash
```

Use for: Complex analysis, large documentation, architecture reviews

## Available Q Agents

Q Chat has access to these specialized agents (automatic routing based on task):

| Agent               | Specialization        | Use For                              |
| ------------------- | --------------------- | ------------------------------------ |
| `default`           | General + QuipEditor  | Quip documents, general tasks        |
| `aws-expert`        | AWS infrastructure    | CDK, CloudFormation, AWS services    |
| `amzn-docs`         | Documentation         | READMEs, API docs, technical writing |
| `amzn-architecture` | Architecture & design | System design, security, patterns    |
| `amzn-quality`      | Code quality          | Linting, standards, best practices   |

See `config/agents.json` for complete agent details.

## Examples

### Example 1: Quip Update with Context

```text
User: "Tell Q to update our architecture Quip doc with the latest changes"

Claude:
1. Identifies the Quip document URL (from previous context or asks user)
2. Locates relevant architecture documentation
3. Delegates to Q with full context:

   q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
     "Update the Quip document at https://quip-amazon.com/ABC123 with the contents of /home/runner/work/project/project/docs/architecture/system-design.md"
```

### Example 2: Bug Ticket Creation

```text
User: "Ask Q to create a SIM ticket for the auth bug we just fixed"

Claude:
1. Gathers context: what was the bug, how was it fixed, what's the impact
2. Delegates to Q with detailed context:

   q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
     "Create a SIM ticket for authentication bug fix.
     Component: UserService (src/services/user.ts)
     Issue: JWT token validation failing for valid users
     Root Cause: Timezone handling in validateToken() method
     Fix: Updated to use UTC timezone for token expiry checks
     Impact: Resolves intermittent 401 errors for authenticated users"
```

### Example 3: Architecture Diagram

```text
User: "Have Q create an architecture diagram showing our Lambda functions and their triggers"

Claude:
1. Analyzes the codebase to understand the Lambda setup
2. Delegates to Q with specific requirements:

   q chat --model claude-sonnet-4.5 --no-interactive --trust-all-tools \
     "Create an architecture diagram for the Lambda functions in this project. Include:
     - Function names and their purposes
     - Event triggers (API Gateway, EventBridge, SQS)
     - IAM roles and permissions
     - Connected services (DynamoDB, S3, etc.)
     - Error handling and DLQ configuration"
```

For more examples, see `examples/usage-examples.md`.

## Best Practices

### 1. Be Specific

Always provide complete information:

- Full URLs for Quip documents
- Absolute file paths
- Detailed context for tickets
- Specific requirements for diagrams

### 2. Use Absolute Paths

```text
❌ "Update with the config file"
✅ "Update with /home/runner/work/project/project/config/settings.json"
```

### 3. Monitor Important Tasks

For critical operations, track the session and verify completion:

```text
✓ Task delegated (session: bash_12345)
  Status: Running...
  [wait for completion]
  ✓ Task completed successfully
```

### 4. Don't Over-Delegate

Only use Q for tasks that require its specialized tools. Claude can handle most operations
directly:

- File operations → Claude
- Git operations → Claude
- Code search → Claude
- Code analysis → Claude
- Quip operations → Q
- Ticket creation → Q
- Diagram generation → Q

## Troubleshooting

### Q CLI Not Found

```bash
Error: q: command not found
Solution: Install Amazon Q CLI from https://docs.aws.amazon.com/amazonq/
```

### Authentication Expired

```bash
Error: Authentication required
Solution: Run 'q auth login' to reauthenticate
```

### Task Timeout

```bash
Error: Task exceeded timeout
Solution: Use async mode for long-running tasks and monitor with read_bash
```

### Permission Denied

```bash
Error: Tool execution not allowed
Solution: Verify --trust-all-tools flag is included in command
```

## Files in This Skill

```text
skills/q-chat-integration/
├── README.md                    # This file - overview and quick start
├── skill.md                     # Complete skill documentation with workflow
├── config/
│   └── agents.json              # Available Q agents and routing hints
└── examples/
    └── usage-examples.md        # Detailed examples and patterns
```

## Success Criteria

A successful Q Chat delegation achieves:

- ✓ Executes without user interaction (non-interactive mode)
- ✓ Completes the requested task autonomously
- ✓ Provides clear status updates throughout
- ✓ Uses appropriate execution mode for task duration
- ✓ Includes complete context and absolute paths
- ✓ Reports meaningful results to the user

## Limitations

- **Requires Q CLI**: Must have Amazon Q CLI installed and configured
- **Authentication**: Q authentication may expire and need renewal
- **Tool Availability**: Limited to tools available in Q CLI
- **Amazon Internal**: Some integrations may be Amazon-internal only
- **No Output Parsing**: Results returned as-is from Q
- **Manual Monitoring**: Long tasks require manual status checks

## Related Skills

- [GitHub Issue Grooming](../github-issue-grooming/) - Repository organization
- [AI Writing Humanizer](../ai-writing-humanizer/) - Text improvement
- [Software Effort Estimation](../software-effort-estimation/) - Codebase analysis

## Version

**1.0.0** - Initial release

### Features

- Trigger phrase recognition
- Command building with proper flags
- Background execution with monitoring
- Context gathering and enrichment
- Agent routing awareness
- Error handling and retry strategies

## Contributing

To improve this skill:

1. Add new trigger phrases to `skill.md`
2. Document new use cases in `examples/usage-examples.md`
3. Update agent configurations in `config/agents.json`
4. Add error handling patterns

## License

MIT License - See repository LICENSE file for details
