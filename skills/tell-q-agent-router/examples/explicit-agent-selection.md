# Example: Explicit Agent Selection

## Scenario

You want to use a specific Q agent for a task, overriding automatic agent selection.

## User Request

```
tell q omega to analyze the current project structure and suggest improvements
```

## Agent Selection Process

1. **Parse request:**
   - Trigger: "tell q"
   - Explicit agent: "omega"
   - Task: "analyze the current project structure and suggest improvements"

2. **Agent validation:**
   - Check if `omega` agent exists in `config/agents.json`
   - Status: ✓ Found

3. **Selected agent:** `omega` (as explicitly requested)

## Command Execution

```bash
q chat --agent omega --no-interactive --trust-all-tools "analyze the current project structure and suggest improvements"
```

## Response to User

```
Starting Q agent 'omega' in background to: analyze the current project structure and suggest improvements

Command: q chat --agent omega --no-interactive --trust-all-tools "analyze the current project structure and suggest improvements"
Background process ID: async_session_321

You can check progress with: read_bash sessionId: async_session_321
Or stop the agent with: stop_bash sessionId: async_session_321
```

## Why Explicit Selection?

You might explicitly select an agent when:

1. **You know which agent is best:**
   - You're familiar with agent capabilities
   - Task matches a specific agent's specialization

2. **Overriding automatic selection:**
   - Automatic selection chose wrong agent
   - You want different perspective

3. **Agent has unique access:**
   - Specific tools or resources
   - Project-specific context (like omega)

4. **Testing different agents:**
   - Comparing agent outputs
   - Evaluating agent performance

## Examples of Explicit Selection

### Example 1: Force aws-expert

```
tell q aws-expert to document our Lambda functions
```

Even though "document" might suggest `amzn-docs`, you want AWS-specific documentation.

### Example 2: Use omega for general tasks

```
tell q omega to help me understand the authentication flow
```

Using `omega` because it has project-specific context.

### Example 3: Code quality focus

```
tell q amzn-quality to review the entire codebase
```

Want comprehensive quality review from the quality specialist.

### Example 4: Architecture review

```
tell q amzn-architecture to design a microservices architecture
```

Specifically need architecture expertise and design tools.

## Agent Selection Priority

When processing a request:

1. **Explicit agent in command** (highest priority)
   - "tell q \<agent\> to..."
   - Uses specified agent, no analysis needed

2. **Special workflow pattern**
   - "tell q \<file\> to quip"
   - Uses workflow-specific agent

3. **Keyword matching**
   - Analyzes task content
   - Matches against agent keywords

4. **Default fallback** (lowest priority)
   - No clear match
   - Uses `omega` as safe default

## When Explicit Selection Fails

If the specified agent doesn't exist:

```
Error: Agent 'invalid-agent' not found.

Available agents:
- aws-expert: AWS architecture, CDK, API, diagrams
- amzn-docs: Documentation, Natural writing
- amzn-architecture: Design, Security, Internal systems
- amzn-quality: Code quality, Standards
- amzn-code-dev: Code development
- default: QuipEditor, General
- omega: Project context

Did you mean one of these?
```

## Best Practices for Explicit Selection

1. **Know your agents:**
   - Understand each agent's capabilities
   - Review agent configurations regularly

2. **Be specific with tasks:**
   - Clear task descriptions help any agent
   - Provide necessary context

3. **Use when appropriate:**
   - Don't override automatic selection unnecessarily
   - Trust keyword matching for obvious tasks

4. **Validate agent exists:**
   - Use correct agent names
   - Check spelling

5. **Monitor results:**
   - Verify agent is performing well
   - Switch agents if needed

## Comparison: Automatic vs Explicit

### Automatic Selection

**Request:**

```
tell q to create Lambda function documentation
```

**Process:**

- Analyzes keywords: "Lambda", "documentation"
- Could match: `aws-expert` (Lambda) or `amzn-docs` (documentation)
- Likely selects: `aws-expert` (AWS keyword stronger)

### Explicit Selection

**Request:**

```
tell q amzn-docs to create Lambda function documentation
```

**Process:**

- Skips analysis
- Uses `amzn-docs` as specified
- Focuses on documentation quality over AWS expertise

**Result difference:**

- Automatic: More AWS-specific, technical documentation
- Explicit (amzn-docs): More readable, user-friendly documentation

## Summary

Explicit agent selection gives you:

✓ **Control** - Choose exactly which agent to use
✓ **Override** - Bypass automatic selection when needed
✓ **Precision** - Match specific agent capabilities to task
✓ **Flexibility** - Test different agents for same task
✓ **Context** - Use agents with specific knowledge or access

Use it wisely to get the best results from Q agents!
