---
name: plan-mode-orchestrator-write-deadlock
description: |
  Recognize and escape the deadlock where NO write can succeed because plan mode
  and an "orchestrator mode" hook block each other. Use when: (1) a PostToolUse/
  PreToolUse hook returns "ORCHESTRATOR MODE: the main thread must not edit or write
  files directly... delegate it to a subagent"; (2) you are ALSO in plan mode (system
  message says only the plan file may be edited); (3) subagents you dispatch to do the
  write refuse with "plan mode became active... forbids writing to any file except my
  designated plan file"; (4) you find you cannot even rewrite your own plan file via a
  subagent; (5) you catch yourself dispatching a 2nd/3rd/4th subagent for the same
  write and each returns a plan instead of doing it. Covers MCP writes (e.g. Notion
  notion-create-pages) and local file writes alike.
author: Claude Code
version: 1.0.0
date: 2026-06-29
---

# Plan-Mode + Orchestrator-Hook Write Deadlock

## Problem

Two independent harness constraints can combine into a total write lock that no
agent-side action can break:

- **Orchestrator-mode hook** (a user PreToolUse/PostToolUse hook): the MAIN thread
  may not edit/write files or run mutating shell commands; it must delegate writes to
  a subagent via the Agent tool.
- **Plan mode**: only the plan file may be written; everything else is read-only — and
  this restriction is INHERITED by subagents you dispatch.

Result: main thread can't write (hook), and subagents can't write either (plan mode).
Subagents asked to write instead return a "here is my plan, approve to proceed"
message and a separate per-subagent plan file. Even rewriting your OWN plan file via a
subagent fails, because a subagent is restricted to ITS designated plan file, not yours.

## Context / Trigger Conditions

- Hook output contains: `ORCHESTRATOR MODE: the main thread must not edit or write files directly`.
- Plan-mode system message present: `you are only allowed to take READ-ONLY actions` /
  `the only file you are allowed to edit`.
- A dispatched subagent replies with something like: `plan mode became active mid-task,
  and its rules forbid writing to any file except my designated plan file`.
- The deliverable requires a write (creating a Notion page, writing a doc, editing code).

## Solution

1. **Detect early.** The FIRST time a subagent returns a plan-instead-of-action for a
   write, stop. Do not dispatch more subagents — they will all fail identically. (In one
   session this pattern wasted ~4 dispatches before being recognized.)
2. **Understand the escape is user-side only.** There is no agent-side workaround. Only
   the user can lift plan mode: pressing **Shift+Tab** to leave plan mode, or approving
   an **ExitPlanMode** call.
3. **Separate "what blocks" from "what the user deferred."** If the user said "design
   only, no implementation plan," do NOT call ExitPlanMode pretending to approve the
   implementation plan. Instead: finish all READ-ONLY work (research, verifying the
   delivery path), then state plainly that plan mode is blocking the single remaining
   write and ask them to exit plan mode.
4. **After plan mode is off, writes STILL go through a subagent** if the orchestrator
   hook is active. Re-dispatch the write to a subagent and tell it explicitly
   "plan mode is OFF; execute the write, do not ask for approval."
5. **Do all verification BEFORE asking to unblock**, so the moment plan mode lifts, the
   write is a single, already-validated action (e.g. confirm a Notion parent page exists,
   auth is correct, and the content format renders — all read-only — before requesting exit).

## Verification

After the user exits plan mode, the re-dispatched subagent completes the write and
returns a concrete artifact (e.g. a created page URL / written file path) instead of a
"plan to do it" message.

## Example

Task: publish a design doc as a Notion sub-page, while both plan mode and an
orchestrator hook are active.

- Verified read-only: fetched the parent page (exists), fetched `self` (auth ok), read
  the Notion `enhanced-markdown-spec` resource (confirmed ```mermaid``` renders).
- Attempted publish via subagent → subagent returned a plan, held for approval (plan
  mode). Same for a 2nd subagent and for rewriting the plan file.
- Stopped looping; told the user plan mode was the blocker and to press Shift+Tab.
- User exited plan mode → re-dispatched the publish subagent with "plan mode is OFF,
  execute now" → page created, URL returned.

## Notes

- Symptom that should trigger this skill instantly: a subagent you spawned to WRITE
  something instead produces a `*-agent-*.md` plan file and asks for approval.
- Do not fight the hook by trying main-thread writes repeatedly — the hook is a hard gate.
- ExitPlanMode shows the user the CURRENT plan file. If that file still holds deferred
  content you cannot rewrite (because of this very deadlock), say so explicitly in the
  message accompanying ExitPlanMode so the user is not misled.
