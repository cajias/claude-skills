---
name: tell-q
description: |
  Use when:
  (1) User says "tell q to ..." or "tell q <agent-name> to ..."
  (2) User wants to delegate tasks to Amazon Q CLI agents
  (3) User mentions specific Q agents like aws-expert, amzn-docs, amzn-architecture
  (4) User wants background execution with full tool permissions
author: cajias
version: 1.0.0
date: 2025-01-27
---

# Tell Q Agent Skill

## Problem

Users need to delegate tasks to specific Amazon Q CLI agents running in the background, with intelligent agent selection based on the task type.

## Context/Trigger

This skill activates when the user says:
- "tell q to ..."
- "tell q <agent-name> to ..."

## Solution

### Instructions

When the user triggers this skill:

1. **Parse the command**:
   - Extract the agent name if specified (e.g., "tell q aws-expert to ...")
   - Extract the task/prompt after "to"
   - **Check for special patterns**:
     - If task matches "upload <file> to <quip-url>", activate the `quip-upload` skill
     - If task matches "upload <file> to quip", activate the `quip-upload` skill
   - If no agent is specified, analyze the task and select the most appropriate agent

2. **Agent Selection Logic** (when not explicitly specified):
   - **Quip Upload**: Use `default` (has QuipEditor tool for writing to Quip)
   - **AWS/CDK/Infrastructure**: Use `aws-expert` (has AWS docs, CDK, API, diagram MCP servers)
   - **Documentation/Writing**: Use `amzn-docs` (has doc generation, natural writing directives)
   - **Architecture/Design**: Use `amzn-architecture` (has internal tools, GitLab access)
   - **Code Quality/Linting**: Use `amzn-quality`
   - **Code Development**: Use `amzn-code-dev`
   - **General/Project-specific**: Use `omega` (project context)
   - **Default**: Use `omega` if uncertain

3. **Build the Q command**:
   ```bash
   q chat --agent <agent-name> --no-interactive --trust-all-tools "<task-prompt>"
   ```

4. **Execute in background**:
   - Use the Bash tool with `run_in_background: true`
   - Inform the user which agent is being used and that it's running in background
   - Provide the bash_id so they can check progress with BashOutput tool

5. **Response format**:
   ```
   Starting Q agent '<agent-name>' in background to: <brief-task-summary>

   Command: q chat --agent <agent-name> --no-interactive --trust-all-tools "<task>"
   Background process ID: <bash_id>

   You can check progress with: /check-bg <bash_id>
   ```

## Available Q Agents

From `~/.aws/amazonq/cli-agents/`:

- **aws-expert**: AWS architecture, CDK, API, diagrams (claude-sonnet-4.5)
- **amzn-docs**: Documentation specialist with natural writing (claude-sonnet-4.5)
- **amzn-architecture**: Design, security, internal systems (claude-sonnet-4.5)
- **amzn-quality**: Code quality and standards
- **amzn-code-dev**: Code development specialist
- **amzn-oncall**: Oncall and operations
- **amzn-builder**: General builder tasks
- **omega**: Project-specific context (this codebase)
- **strategic-planner-agent**: Planning and strategy
- **sequential-planner-agent**: Step-by-step planning
- **branched-thinking-agent**: Complex decision-making

## Examples

**User**: "tell q to upload docs/architecture.md to https://company.quip.com/ABC123"
**Action**: Use `default` agent (has QuipEditor tool) + `quip-upload` skill workflow

**User**: "tell q to create an architecture diagram for our EventBridge setup"
**Action**: Use `aws-expert` agent (has diagram MCP server)

**User**: "tell q amzn-docs to write documentation for the new API"
**Action**: Use `amzn-docs` agent (explicitly specified)

**User**: "tell q to review the CDK stack for best practices"
**Action**: Use `aws-expert` agent (CDK + best practices)

**User**: "tell q to check our code quality standards"
**Action**: Use `amzn-quality` agent

## Important Notes

- Always use `--trust-all-tools` to give full permissions to agent's configured tools
- Always use `--no-interactive` for background execution
- Always run with `run_in_background: true` in Bash tool
- Provide clear feedback about which agent is running and how to monitor it
- If agent selection is ambiguous, briefly explain your choice to the user
- **For Quip uploads**: Follow the `quip-upload` skill workflow (parse, generate diagrams, validate sections)

## Special Workflows

### Quip Upload Pattern

When the command matches "upload <file> to <quip-url>":

1. Use `amzn-docs` agent (has Quip tools)
2. Include the full `quip-upload` skill workflow in the prompt
3. Emphasize validation requirements for lists and tables
4. Request a detailed summary report at the end

**Prompt template for Quip uploads**:
```
Upload the markdown file '<absolute-file-path>' to Quip document '<quip-url>' using the QuipEditor tool.

Follow the quip-upload skill workflow SECTION BY SECTION:

PHASE 1 - PREPARE CONTENT:
1. Read and parse the markdown file into sections by headers (H1, H2, H3, etc.)
2. For each mermaid or plantuml code block found:
   - Extract the diagram code
   - Generate PNG: mmdc -i /tmp/diagram-<hash>.mmd -o /tmp/diagram-<hash>.png -b transparent
   - Replace the code block with: "> TODO: add image /tmp/diagram-<hash>.png here"
3. For existing image references ![alt](path):
   - Convert to: "> TODO: add image <absolute-path> here"

PHASE 2 - UPLOAD AND VALIDATE EACH SECTION:
For each section (iterate through all sections):
4. Upload section using QuipEditor:
   - documentId: '<quip-url>'
   - content: '<section-markdown-with-placeholders>'
   - format: 'markdown'
   - location: 0 (append to end)
5. IMMEDIATELY validate the uploaded section:
   - Read back: QuipEditor(documentId='<quip-url>', analyzeStructure=true)
   - Check lists: Verify they render as <ul>/<ol> items, NOT plain paragraphs
   - Check tables: Verify cells have content, NOT empty
   - Check headers: Verify H1/H2/H3 levels are correct
6. If validation FAILS for this section:
   - Identify the issue (list/table/header formatting)
   - Use QuipEditor to edit/replace that specific section with corrected markdown
   - Re-validate before proceeding
7. Only move to next section after current section validates successfully

PHASE 3 - SUMMARY:
8. Provide detailed report:
   - Total sections: <count>
   - Sections uploaded successfully: <count>
   - Validation fixes applied: <list of sections that needed fixes>
   - Generated diagrams: <list of PNG files in /tmp/>
   - Image placeholders: <list of all TODO placeholders>
   - Next steps: Manual upload of images to Quip

Use the QuipEditor tool (default Q agent has this).
```
