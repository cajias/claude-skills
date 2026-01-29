---
name: obsidian-memory:memory-system
description: |
  Use Obsidian as Claude's primary workspace and persistent memory. Activates for ALL file
  operations during sessions - working notes, scratchpads, analysis, task tracking - not just
  permanent knowledge. Prefer Obsidian MCP tools over local disk writes. Use proactively for
  any information worth preserving beyond the current conversation turn.
version: 2.0.0
---

# Obsidian Memory System

**Obsidian is my primary workspace**, not just long-term storage. Use it for:
- Working memory during sessions (scratchpads, analysis, task tracking)
- Permanent knowledge (decisions, lessons, patterns)
- Everything in between

## Why Obsidian Over Local Disk

| Aspect | Local Disk | Obsidian |
|--------|------------|----------|
| Folder creation | Need `mkdir` first | **Auto-created** |
| Searchability | Grep/Glob | `search_notes` with frontmatter |
| User visibility | Hidden in filesystem | **Visible in Obsidian app** |
| Cross-session | Lost or scattered | **Organized, persistent** |
| Linking | None | `[[wiki-links]]` work |

**Default choice: Obsidian.** Only use local disk for generated code or build artifacts.

## MCP Tools for Workspace

| Need | Tool | Example |
|------|------|---------|
| Create/overwrite | `write_note` | Session context, scratchpad |
| Surgical edit | `patch_note` | Update status, add findings |
| Read | `read_note` | Load previous context |
| Search | `search_notes` | Find related work |
| List | `list_directory` | Browse folder contents |

## Session Workspace Protocol

For ANY working memory during a session:

### 1. Create Session Folder (Auto-Created)

Just write your first file - folder is created automatically:

```
agent-workspaces/claude-[YYYYMMDD]-[HHMMSS]-[context]/context.md
```

Context examples: `vault-setup`, `feature-auth`, `debug-api`, `pr-review-123`

### 2. Standard Session Files

| File | Purpose |
|------|---------|
| `context.md` | Session state, current task, status |
| `scratchpad.md` | Working notes, analysis, draft content |
| `findings.md` | Discoveries, results, outputs |
| `tasks.md` | Task tracking if complex |

### 3. Update Status When Done

Use `patch_note` to mark session completed:

```yaml
status: completed
```

## When to Write to Obsidian

### Always (Proactive)

| Trigger | What to Capture | Where |
|---------|-----------------|-------|
| Starting any task | Session context | `agent-workspaces/claude-[timestamp]-[context]/` |
| "Let's do X instead of Y" | Decision + rationale | `decisions/` folder as ADR |
| "I prefer..." | User preference | `agent-workspaces/shared/persistent.md` |
| "That worked/didn't work" | Lesson learned | `knowledge-base/lessons-learned/` |
| Person mentioned | Facts about them | `people/[name].md` |
| Recurring pattern | Pattern documentation | `knowledge-base/` with `#pattern` |
| Important constraint | Project context | `engagements/active/[project]/` |
| Quick note, unsure where | Inbox for triage | `agent-workspaces/shared/inbox.md` |

### During Complex Tasks

- Multi-step analysis → write intermediate findings to scratchpad
- Research → capture sources and summaries
- Debugging → log what you tried and results
- Code review → note issues found before reporting

## When to Read from Obsidian

### Before Starting Work

- **Any task** → Check `agent-workspaces/shared/persistent.md` for standing context
- **Client work** → Read `engagements/active/[client]/context.md`
- **Technical decision** → Check relevant `decisions/` folder
- **Person mentioned** → Check `people/[name].md`
- **Implementation** → Check `playbooks/` and `knowledge-base/`

### Resuming Work

- Check `agent-workspaces/` for previous sessions on same topic
- Search by context identifier if you know it

## Write Location Decision Tree

```
ANY working memory (scratchpad, analysis, tasks)?
  └─ YES → agent-workspaces/claude-[timestamp]-[context]/

Decision or choice made?
  └─ YES → relevant decisions/ folder as ADR

Reusable pattern or lesson?
  └─ YES → knowledge-base/lessons-learned/

About a person?
  └─ YES → people/[name].md

Engagement-specific?
  └─ YES → engagements/active/[project]/

Reference material?
  └─ YES → knowledge-base/[technology]/

Unsure?
  └─ agent-workspaces/shared/inbox.md
```

## Standard Frontmatter

Always include when creating notes:

```yaml
---
type: context | scratchpad | decision | lesson | person | note
status: active | completed | archived
date: YYYY-MM-DD
summary: "1-2 sentences for quick scanning without reading content"
tags: [relevant, tags]
related: [[other-note]]
---
```

The `summary` field is critical for efficient navigation.

## Shared Persistent Context

`agent-workspaces/shared/persistent.md` stores cross-session knowledge:

- User preferences and corrections
- Standing instructions
- Patterns specific to this user
- Things learned that should persist

**Update this file** when you learn something that should survive session boundaries.

## Tag Taxonomy

| Category | Tags |
|----------|------|
| Status | `#draft` `#active` `#completed` `#archived` |
| Type | `#decision` `#pattern` `#lesson` `#meeting` `#blocker` |
| Priority | `#urgent` `#backlog` |
| Sharing | `#shareable` `#internal` `#sensitive` |

## What NOT to Store in Obsidian

- Generated code (belongs in git)
- Build artifacts
- Secrets or credentials
- Large binary files
- Ephemeral single-turn conversation details

## Related

- `obsidian-memory:search-navigation` - Efficient vault searching
- `CLAUDE.md` in vault root - User-specific instructions
