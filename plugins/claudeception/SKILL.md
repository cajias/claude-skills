---
name: claudeception
description: |
  Extract reusable skills from Claude Code sessions. Triggers: /claudeception command,
  "save this as a skill", "what did we learn?". Creates SKILL.md files for non-obvious
  discoveries, workarounds, and debugging insights.
author: Claude Code
version: 2.0.0
---

# Claudeception

Save valuable learnings as reusable skills.

## When to Use

- After solving a non-obvious problem
- When you discovered a workaround
- When debugging revealed something unexpected
- User says "save this as a skill" or runs `/claudeception`

## What Makes a Good Skill

**Extract when:**

- Solution required real investigation (not just docs lookup)
- Error message was misleading
- Workaround for a tool/framework limitation
- Pattern would help future similar situations

**Skip when:**

- Straightforward documentation lookup
- One-time project-specific fix
- Common knowledge

## How to Create a Skill

1. Identify the learning
2. Create the skill file:

```bash
echo '{"skills": [{
  "name": "skill-name",
  "title": "Brief Title",
  "description": "When to use this - specific triggers",
  "problem": "What went wrong",
  "triggers": "Exact symptoms or error messages",
  "solution": "Step-by-step fix",
  "verification": "How to confirm it worked"
}]}' | python3 ~/.claude/my-claude-skills/plugins/claudeception/hooks/extract-skills.py
```

Or just write to `~/.claude/my-claude-skills/skills/[name]/SKILL.md` directly.

## Skill Template

```markdown
---
name: kebab-case-name
description: |
  Specific trigger conditions. Be precise for semantic matching.
---

# Title

## Problem

What went wrong

## When to Use

Exact symptoms, error messages, scenarios

## Solution

Step-by-step fix

## Verification

How to confirm it worked
```

## Check Stats

```bash
~/.claude/my-claude-skills/plugins/claudeception/observability/simple-stats.sh
```

## Quality Gate

Before creating, verify:

- [ ] Required real investigation
- [ ] Would help someone else
- [ ] Trigger conditions are specific
- [ ] Not duplicating docs
