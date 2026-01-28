# TDD Plan Generator Skill

Generate comprehensive TDD-based plans formatted for execution via `ralph-loop`.

## Overview

This skill creates structured, iterative development plans that follow Test-Driven Development
principles. Plans include master goals, concurrent task phases, and strict exit criteria
including code review validation.

## What It Does

1. **Analyzes** your task requirements and breaks them into testable goals
2. **Generates** a master goals list (immutable throughout execution)
3. **Creates** phased iteration plan (RED → GREEN → REFACTOR → VALIDATE → COMMIT → EVALUATE)
4. **Defines** exit criteria including tests, lint, deploy, and PR review
5. **Tracks** investigation history to prevent retrying failed approaches

## When to Use

Use this skill when you need to:

- Create a TDD plan for a new feature
- Generate an iterative plan using ralph-loop
- Plan development with concurrent tasks where possible
- Ensure code quality with PR review validation
- Track investigation history across iterations

## Key Features

### TDD Phases

- **RED**: Write failing tests (concurrent where possible)
- **GREEN**: Implement to make tests pass (sequential with dependencies)
- **REFACTOR**: Clean up code (concurrent where safe)
- **VALIDATE**: Run tests, lint, deploy, integration tests, PR review
- **COMMIT**: Commit with descriptive message
- **EVALUATE**: Check exit criteria, generate next iteration if needed

### Investigation Tracker

Prevents wasted effort by tracking:

- What issues occurred
- What fixes were attempted
- What results were achieved
- What next actions are needed

### Concurrency Optimization

The plan maximizes parallel execution where safe:

- Writing independent tests
- Running lint + type-check
- Refactoring unrelated code

## Quick Start

```bash
/tdd-plan Implement user authentication with JWT tokens
```

With optional deploy and integration test commands:

```bash
/tdd-plan Implement header forwarding in MCP multiplexer
  --deploy-cmd "npm run deploy"
  --integration-cmd "isengardcli run --account X --role Admin -- npm run test:integration"
```

## Integration

After plan generation, start execution with:

```bash
/ralph-loop:ralph-loop
```

## Related Skills

- **ralph-loop:ralph-loop**: Executes the generated plan
- **pr-review-toolkit:review-pr**: Code review validation
- **orchestration:creating-workflows**: For complex multi-agent workflows

## Version

1.0.0 - Initial release with TDD plan generation for ralph-loop
