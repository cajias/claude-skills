---
name: ralph-loop-invocation
description: Correct way to invoke Ralph Loop skill with proper argument quoting
tags: [ralph-loop, claude-code, skills]
---

# Ralph Loop Invocation

When invoking the Ralph Loop skill, the prompt argument must be properly quoted.

## Correct Invocation

```text
/ralph-loop "Your task description here" --max-iterations 5 --completion-promise "Task complete"
```

Or using the Skill tool:

```text
Skill: ralph-loop:ralph-loop
Args: "Your task description" --max-iterations 5 --completion-promise "Done"
```

## Key Rules

1. **Quote the prompt** - The main task description should be in double quotes
2. **Quote completion promise** - Multi-word promises must be quoted
3. **Avoid special characters** - Parentheses, colons, and other shell metacharacters can cause issues
4. **Keep prompts simple** - Use plain words, avoid complex punctuation

## Common Mistakes

### Wrong - Unquoted prompt with special chars

```text
/ralph-loop Audit links: 1) Check broken, 2) Fix dupes
```

Error: Shell operators require approval

### Wrong - Complex characters

```text
/ralph-loop "Check (parentheses) and [brackets]"
```

May fail due to shell interpretation

### Correct - Simple quoted prompt

```text
/ralph-loop "Audit links and fix issues" --max-iterations 5
```

## Options

- `--max-iterations N` - Stop after N iterations (default: unlimited)
- `--completion-promise "TEXT"` - Exit when this phrase is output in `<promise>` tags

## Monitoring

```bash
# Check current iteration
head -10 .claude/ralph-loop.local.md
```

## Exiting the Loop

Output the exact completion promise in XML tags:

```text
<promise>Your completion promise text</promise>
```

Only output this when the statement is genuinely TRUE - do not lie to escape the loop.
