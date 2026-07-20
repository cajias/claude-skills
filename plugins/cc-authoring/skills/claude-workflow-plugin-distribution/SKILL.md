---
name: claude-workflow-plugin-distribution
description: |
  How to distribute a Claude Code Workflow-tool script (the Workflow({script})
  orchestration engine / .claude/workflows/*.js) through a plugin or marketplace,
  and how to architect it around the Workflow sandbox. Use when: (1) you want to
  "ship / package / distribute a workflow" in a plugin; (2) designing a skill or
  command that launches a Workflow; (3) you assumed a plugin has a `workflows/`
  component (it does NOT); (4) your workflow .js needs to read a file/config/data
  but the sandbox has no filesystem; (5) deciding where file I/O and deterministic
  pre-processing should live relative to the engine.
author: Claude Code
version: 1.0.0
date: 2026-07-04
---

# Distributing a Claude Code Workflow through a plugin

## Problem

You built a Workflow-tool script (`Workflow({ script })`, runs as `.claude/workflows/*.js`)
and want to ship it to others via a plugin/marketplace. But Claude Code plugins auto-discover
only **commands, agents, skills, hooks, and MCP servers** — there is **no `workflows/`
component**. A workflow `.js` is a harness feature, not a first-class plugin component, so it
cannot be distributed as one directly.

## Context / Trigger Conditions

- "distribute / ship / package a workflow", "workflow in a plugin/marketplace".
- Designing a skill or slash command that should run a heavy multi-agent Workflow.
- You looked for a `workflows/` directory convention in the plugin spec and found none.
- Your workflow `.js` needs to read the input file / config / a data file, but fails because
  the Workflow sandbox has no filesystem or `import`.

## Solution

**1. Bundle the engine as a skill/command asset; launch it via the Workflow tool.**
Skills and commands may include arbitrary supporting files and reference them with
`${CLAUDE_PLUGIN_ROOT}`. So:

- Put the engine at e.g. `skills/<name>/workflows/engine.js` inside the plugin.
- The skill's `SKILL.md` (the discoverable entry point) instructs Claude to call:
  `Workflow({ scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/<name>/workflows/engine.js", args })`.
- Skill = the door (semantic trigger); the `.js` = the engine behind it. Same pattern plugins
  already use to ship Python hooks (`hooks/*.py` referenced via `${CLAUDE_PLUGIN_ROOT}`).

**2. Architect around the sandbox: the launcher does I/O, the engine stays in-memory.**
The Workflow `.js` sandbox has **no filesystem, no `import`/`require`**, and no
`Date.now()/Math.random()/new Date()` — only in-memory JS built-ins (JSON, RegExp, String…)
and the injected globals (`args, phase, log, agent, parallel, pipeline, workflow, budget`).
Consequences that shape the design:

- **The launcher skill does ALL file I/O** — it reads the input document, config, data files,
  and prompt templates (it runs in the main session with the Read tool), then passes them to
  the engine via `args` (e.g. `{ text, config, patterns, prompts, ... }`). Nothing inside the
  engine reads a file.
- **Deterministic pre/post-processing → a standalone Node module.** Anything mechanical
  (regex scans, parsing, counting) should be a normal Node `.js` module the skill runs
  (`node prescan.js …`) — real Node has `fs`, so it is directly unit-testable — and whose
  output the skill passes into the engine via `args`. Do NOT try to do it inside the sandbox.
- **Push file-work-that-needs-judgment into agents.** The engine can't touch files, but the
  subagents it spawns via `agent()` DO have tool access (Read, Grep, …). So judgment-based
  reading/analysis goes in agent prompts, not in the engine body.

**3. Degrade gracefully.** The launcher only truly runs where the harness has the Workflow
tool. Document a fallback (dispatch the same phases as subagents via the Agent tool) so the
skill still works where the Workflow tool is absent.

## Verification

Shipped exactly this: an `ai-writing-humanizer` skill whose `SKILL.md` reads the doc +
`patterns.json` + prompts, runs a standalone `prescan.js` node module, then launches
`workflows/humanize.js` via `Workflow({ scriptPath: "${CLAUDE_PLUGIN_ROOT}/…/humanize.js",
args })`. The engine ran in-memory and dispatched analyze/revise/review agents; 18/18 tests
passed; the plugin installs as a normal skill.

## Notes

- There is no `workflows` key in `plugin.json`; do not invent one.
- Keep the engine's returned result serializable; the launcher turns it into user-facing output
  (files, on-screen report, tasks) — the engine itself can't write files or create tasks.
- Related: the `claude-workflow-authoring-gotchas` skill (pure-literal `meta`, `args`
  normalization) and the `claude-workflow-tdd-harness` skill (how to unit-test the engine by
  mocking `agent()`). Also see `claude-workflow-meta-markdownlint-pure-literal-break`.
