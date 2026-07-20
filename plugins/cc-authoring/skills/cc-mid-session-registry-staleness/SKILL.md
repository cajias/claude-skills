---
name: cc-mid-session-registry-staleness
description: |
  Fix for two Claude Code mid-session staleness traps that fail Workflow runs
  instantly (<15ms). Use when: (1) a Workflow agent() call fails with
  "agent type '<name>' not found" listing only plugin/built-in agents, even
  though .claude/agents/<name>.md exists with valid frontmatter — the agent
  registry only loads .claude/agents/ at session START, so agent files created
  mid-session are not resolvable via agentType/subagent_type until restart;
  (2) re-invoking a saved workflow via Workflow({name}) runs STALE code after
  you edited .claude/workflows/<name>.js — name resolution serves a cached
  snapshot, so mid-session edits never reach it. Both failures look like your
  code is wrong when it's actually registry caching. Fixes: launch via
  Workflow({scriptPath: <live file path>}) to bypass the name cache, and
  design workflow scripts with a registry-independent persona fallback
  (prompt the agent to Read its own .claude/agents/<name>.md and adopt the
  role) toggled by an arg like useAgentTypes:false.
---

# cc-mid-session-registry-staleness

## Problem

Two Claude Code registries are loaded at session start and NOT refreshed when
files change mid-session:

1. **Agent registry** (`.claude/agents/*.md`): agents created during the
   session are invisible to `agentType` (Workflow tool) and `subagent_type`
   (Agent tool). The error lists only plugin/built-in agents — your project
   agents are absent entirely, which is the tell.
2. **Saved-workflow registry** (`.claude/workflows/*.js` via
   `Workflow({name})`): name resolution snapshots the script; later edits to
   the file on disk are silently ignored on re-invocation.

Both fail fast (<15ms, agent_count 1, 0 tool uses) — that timing signature
means registry/validation failure, not a logic bug in your script.

## Solution

**Trap 2 (stale workflow):** invoke by path, not name:

```
Workflow({ scriptPath: "/abs/path/.claude/workflows/my-workflow.js", args: {...} })
```

`scriptPath` reads the live file every time.

**Trap 1 (unregistered agents):** add a registry-independent fallback to the
workflow script — same persona content, delivered by file read instead of
system prompt:

```js
const USE_AGENT_TYPES = opts.useAgentTypes !== false
const roleRef = (t) => USE_AGENT_TYPES ? '' :
  `FIRST: Read ${ROOT}/.claude/agents/${t}.md and fully adopt the role, method, and rules defined there.\n`
const roleOpts = (t, base) => USE_AGENT_TYPES ? { ...base, agentType: t } : base
// call sites:
agent(`${roleRef('my-role')}<task...>`, roleOpts('my-role', { label: 'x', schema: S }))
```

Run with `args: { useAgentTypes: false }` in the session that created the
agents; after a session restart the registry has them and the default
(agentType) path works.

## Verification

- Stale-workflow: `diff` the snapshot script (path printed in the Workflow
  result, `.../workflows/scripts/<name>-<runId>.js`) against your live file —
  if they differ, you hit the cache.
- Agent registry: the failure's "Available agents:" list — if NO project
  agents appear (not just yours missing), the registry predates them.

## Notes

- A skill file created mid-session (`.claude/skills/`) shows the same
  session-start loading behavior for its slash-command registration.
- The file-read fallback is slightly weaker than a true system prompt (the
  persona arrives as user-message content), but in practice agents follow
  "read and adopt" reliably; the content is identical.
