---
name: cc-hooks-main-vs-subagent
description: |
  How a Claude Code PreToolUse/PostToolUse hook can tell whether a tool call
  came from the MAIN conversation thread or from a SUBAGENT (Task/Agent tool),
  plus the gotchas of testing hooks via headless `claude -p`. Use when:
  (1) building a hook that should apply only to the main thread (e.g.
  orchestrator-only enforcement that denies Edit/Write in main but allows
  subagents) or only to subagents; (2) wondering if hook input contains an
  is_subagent / agent indicator — it does, but it's undocumented;
  (3) a hook behaves differently than expected under `claude -p` because
  CLAUDE_CODE_ENTRYPOINT is sdk-cli there and `env CLAUDE_CODE_ENTRYPOINT=cli`
  does NOT survive (the CLI overwrites it); (4) a headless hook test shows
  "Claude requested permissions ... but you haven't granted it yet" instead of
  the hook's deny reason — the permission gate fires before the hook surfaces;
  (5) you need to force the interactive code path in a headless test (use a
  --settings file with an env block).
author: Claude Code
version: 1.0.0
date: 2026-06-11
---

# Discriminating Main Thread vs Subagent in Claude Code Hooks

## Problem

Hooks configured in settings.json fire for BOTH main-conversation tool calls
and subagent tool calls. The official hooks docs do not document any way to
tell them apart, which blocks patterns like "orchestrator-only main thread"
(deny Edit/Write in main, allow in subagents) or subagent-only auditing.

## Context / Trigger Conditions

- Building a PreToolUse hook that must behave differently for main thread vs
  subagents.
- Testing any hook via headless `claude -p` and getting confusing results.
- Hook input fields needed: nothing in the docs mentions agent identity.

## Solution

### The discriminator (verified empirically on Claude Code 2.1.173)

Subagent tool calls include two extra fields in the hook stdin JSON that are
**entirely absent** for main-thread calls:

```json
"agent_id": "a0fc2a0a18648d281",
"agent_type": "general-purpose"
```

Everything else is identical between main and subagent calls — same
`session_id`, same `transcript_path` (subagents do NOT get an agent-*.jsonl
transcript_path in hook input), same `cwd`, same `permission_mode`, and a
byte-identical environment (no env var distinguishes them).

Hook logic:

```bash
input=$(cat)
if [ -n "$(printf '%s' "$input" | jq -r '.agent_id // empty')" ]; then
  exit 0   # subagent — allow / skip
fi
# ... main-thread handling, e.g. deny:
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}\n'
```

### Distinguishing interactive vs headless sessions

The hook process env contains `CLAUDE_CODE_ENTRYPOINT`: `cli` for interactive
sessions, `sdk-cli` for `claude -p`. Gate on `case "$CLAUDE_CODE_ENTRYPOINT" in
sdk*) exit 0;; esac` to exempt headless workers (ralph loops, autoresearch,
skill evals) from main-thread enforcement.

### Headless testing gotchas (in dependency order)

1. **`env CLAUDE_CODE_ENTRYPOINT=cli claude -p ...` does NOT work** — the CLI
   unconditionally overwrites the var to `sdk-cli` in print mode. To force the
   interactive code path in a headless test, use a settings file instead:
   `claude --settings force-cli.json -p ...` where the file contains
   `{"env":{"CLAUDE_CODE_ENTRYPOINT":"cli"}}`. The settings `env` block wins.
2. **The permission gate masks hook denials**: without `--permission-mode
   acceptEdits` (or an allowedTools grant), a headless Write is rejected with
   "Claude requested permissions to write to X, but you haven't granted it
   yet" — which looks like a hook deny but is not. Grant permissions first so
   the hook's permissionDecisionReason is what you actually observe.
3. **Flag order matters**: flags must precede `-p "prompt"`; putting
   `--allowedTools` between `-p` and the prompt yields "Input must be provided
   either through stdin or as a prompt argument".
4. **Capture everything during discovery**: a logging hook of
   `jq -c --arg env "$(env | grep -iE 'CLAUDE|AGENT')" '{input: ., env: $env}' >> log.jsonl`
   on a temp `--settings` file is the cheapest way to see all hook input
   fields for a given CLI version.

## Verification

- 13 pipe tests (synthetic payloads with explicit env) — all behaviors as
  described.
- Live E2E: with `{"env":{"CLAUDE_CODE_ENTRYPOINT":"cli"}}` settings, a
  main-thread Write was denied with the hook's reason while a delegated
  subagent Write in the same configuration succeeded; plain `claude -p`
  (sdk-cli) main-thread Write succeeded (exemption worked).
- Bonus live proof: the settings watcher hot-reloaded the guard into the
  authoring session itself, and the orchestrator's own main-thread Write of
  this very skill file was denied — a subagent had to write it.

## Example

Working production example: `~/.claude/hooks/orchestrator-guard.sh` wired in
`~/.claude/settings.json` (PreToolUse, matcher `Edit|Write|NotebookEdit|Bash`)
— denies main-thread file mutations in interactive sessions, exempts
subagents via `agent_id`, exempts headless via `CLAUDE_CODE_ENTRYPOINT=sdk*`,
kill switch `CLAUDE_ORCH_GUARD=off`.

## Notes

- `agent_id`/`agent_type` are **undocumented**; re-verify after major Claude
  Code upgrades (one logging-hook run, see gotcha 4). Verified on 2.1.173.
- `SubagentStart`/`SubagentStop` hook events exist in the settings schema but
  are NOT needed for per-call discrimination and are racy for it (parallel
  agents overlap the main loop).
- Permission deny rules in settings.json are NOT an alternative: they apply
  session-wide, crippling subagents too.
