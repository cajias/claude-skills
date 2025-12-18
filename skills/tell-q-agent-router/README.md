# Tell Q Agent Router Skill

Intelligently route tasks to the most appropriate Amazon Q CLI agent based on task type, with
support for explicit agent selection and special workflow patterns.

## Overview

This skill enables Claude to seamlessly delegate tasks to Amazon Q agents by:

- **Intelligent Routing**: Automatically selects the best Q agent based on task analysis
- **Explicit Control**: Support for manual agent selection when needed
- **Background Execution**: Non-blocking agent execution with progress monitoring
- **Special Workflows**: Built-in patterns like Quip file upload
- **Simple Interface**: Natural language commands like "tell q to..."

## When to Use

Use this skill when you need to:

- Delegate specialized tasks to domain-expert Q agents
- Upload files to Quip documents
- Leverage specific Q agent capabilities (AWS, documentation, architecture, etc.)
- Run long-running Q tasks in the background
- Automatically route tasks based on content analysis

## Quick Start

### Basic Usage

Simply use the "tell q to..." pattern:

```text
tell q to deploy a Lambda function with S3 trigger
```

The skill will:

1. Analyze the task (AWS/Lambda/S3 keywords)
2. Select `aws-expert` agent
3. Execute in background
4. Provide monitoring instructions

### Explicit Agent Selection

Specify the agent name directly:

```text
tell q omega to analyze the current project structure
```

### Quip Upload

Use the special workflow pattern:

```text
tell q report.md to quip
```

## Available Agents

| Agent                 | Specialization              | Best For                                   |
| --------------------- | --------------------------- | ------------------------------------------ |
| **aws-expert**        | AWS architecture, CDK, APIs | Infrastructure, Lambda, S3, CloudFormation |
| **amzn-docs**         | Documentation writing       | README files, API docs, technical writing  |
| **amzn-architecture** | System design, security     | Architecture reviews, design docs, GitLab  |
| **amzn-quality**      | Code standards, linting     | Code reviews, quality checks, standards    |
| **amzn-code-dev**     | Development tasks           | Feature implementation, code building      |
| **default**           | QuipEditor, general tasks   | Quip uploads, miscellaneous tasks          |
| **omega**             | Project-specific context    | General tasks, project exploration         |

## Key Features

### 1. Intelligent Agent Selection

Analyzes task content and selects the most appropriate agent:

- **Keyword Matching**: Compares task against agent capability keywords
- **Context Analysis**: Considers task type and domain
- **Smart Defaults**: Falls back to `omega` for uncertain tasks

### 2. Background Execution

Runs Q agents asynchronously:

- **Non-blocking**: Continue working while agent runs
- **Progress Monitoring**: Check output periodically
- **Process Control**: Stop agent if needed

### 3. Special Workflow Patterns

Built-in support for common workflows:

- **Quip Upload**: Automatic file upload to Quip documents
- **More patterns can be added**: Extensible design

### 4. Simple Natural Language Interface

No complex syntax required:

- "tell q to \<task\>" - Basic delegation
- "tell q \<agent\> to \<task\>" - Explicit agent
- "tell q \<file\> to quip" - Quip upload

## Command Format

The skill constructs Q CLI commands in this format:

```bash
q chat --agent <agent-name> --no-interactive --trust-all-tools "<task>"
```

**Parameters:**

- `--agent`: Specifies which Q agent to use
- `--no-interactive`: Enables background execution
- `--trust-all-tools`: Grants full tool permissions to agent

## Usage Examples

### Example 1: AWS Infrastructure

**Input:**

```text
tell q to create a CDK stack for a serverless REST API
```

**Result:**

- Agent selected: `aws-expert`
- Background execution with session ID
- Progress monitoring instructions provided

### Example 2: Documentation

**Input:**

```text
tell q to write API documentation for our GraphQL endpoints
```

**Result:**

- Agent selected: `amzn-docs`
- Documentation specialist handles the task
- Natural, professional writing style

### Example 3: Code Quality

**Input:**

```text
tell q to lint and review all TypeScript files
```

**Result:**

- Agent selected: `amzn-quality`
- Standards enforcement and quality checks
- Comprehensive review feedback

### Example 4: Quip Upload

**Input:**

```text
tell q design-doc.md to quip
```

**Result:**

- Agent selected: `default` (has QuipEditor)
- File uploaded to Quip
- Quip document link provided

## Prerequisites

**Required:**

- Amazon Q CLI (`q`) installed and configured
- Q agents set up (aws-expert, amzn-docs, etc.)
- Appropriate permissions for agent execution

**Optional:**

- QuipEditor tool configured (for Quip workflows)
- Agent-specific tools and resources

## Response Format

When you delegate a task, you'll receive:

```text
Starting Q agent '<agent-name>' in background to: <task-summary>

Command: q chat --agent <agent-name> --no-interactive --trust-all-tools "<task>"
Background process ID: <sessionId>

You can check progress with: read_bash sessionId: <sessionId>
Or stop the agent with: stop_bash sessionId: <sessionId>
```

## Monitoring and Control

### Check Progress

```bash
read_bash sessionId: <sessionId> delay: 5
```

Reads the latest output from the running Q agent.

### Stop Agent

```bash
stop_bash sessionId: <sessionId>
```

Terminates the Q agent if needed.

## Configuration

Agent configurations are stored in `config/agents.json`:

```json
{
  "agents": [
    {
      "name": "aws-expert",
      "model": "claude-sonnet-4.5",
      "capabilities": ["AWS architecture", "CDK", "API", "diagrams"],
      "keywords": ["aws", "cdk", "lambda", "s3", "ec2", "cloudformation"]
    }
    // ... more agents
  ]
}
```

**Customization:**

- Add new agents to the configuration
- Modify keyword lists for better matching
- Adjust agent capabilities

## Error Handling

The skill handles common errors gracefully:

- **Q CLI not found**: Provides installation instructions
- **Agent not found**: Lists available agents
- **File not found**: Validates file paths for Quip uploads
- **Execution errors**: Reports Q agent errors with context

## Limitations

- Requires Amazon Q CLI to be installed and configured
- Agent selection is keyword-based (may occasionally miss context)
- Background execution requires manual monitoring for completion
- Quip workflow requires QuipEditor tool configured
- Some agents may have limited tool access based on configuration

## Best Practices

1. **Be Specific**: Clear task descriptions lead to better agent selection
2. **Use Explicit Selection**: Override automatic selection when you know which agent is best
3. **Monitor Progress**: Check background tasks periodically for long-running operations
4. **Leverage Specialization**: Use specialized agents for their domain expertise
5. **Validate Files**: Ensure files exist before Quip uploads

## Related Skills

- Project management and task delegation
- Amazon Q agent configuration and management
- Background process monitoring and control

## Success Metrics

After implementing this skill, you should experience:

✓ Seamless task delegation to Q agents
✓ Appropriate agent selection based on task analysis
✓ Non-blocking background execution
✓ Simple, natural language interface
✓ Effective use of specialized agent capabilities
✓ Reduced context switching and improved productivity
