---
name: ai-writing-humanizer
description: |
  Humanize a document by removing AI-writing patterns via a multi-agent workflow
  (analyze → revise → adversarial review → loop-until-clean). Use when the user asks to
  "humanize", "de-AI", "remove AI tells", or "review for AI writing" on a file.
author: Raul
version: 1.0.0
tags: ["writing", "humanizer", "ai-detection", "editing"]
level: user
---

# AI Writing Humanizer (workflow launcher)

This skill launches a multi-agent **Workflow** that humanizes a document: it analyzes AI-writing
tells across three lenses, rewrites fidelity-first, then runs four adversarial reviewers
(fidelity / residual-tells / quality-voice / gap) and loops until clean. It **auto-fixes
critical/high** issues and **surfaces medium/low (and anything the fidelity guard blocks) as
prioritized tasks**.

> A full pass dispatches many agents and is **token-intensive**. Before running, confirm with the
> user: which file, and whether to proceed.

## Steps

1. **Resolve the target.** Get the file path from the user. If they pasted text instead, write it
   to a scratch file first (the engine works on a document). Set
   `ROOT="${CLAUDE_PLUGIN_ROOT}/skills/ai-writing-humanizer"`.

2. **Pre-scan (deterministic).** Run:

   ```bash
   node "$ROOT/workflows/prescan.js" "<file>" "$ROOT/patterns/patterns.json" "$ROOT/config/default.config.json"
   ```

   Capture stdout as `mechanicalFindings` (a JSON array).

3. **Assemble args.** Read `<file>` → `text`; read `$ROOT/patterns/patterns.json` → `patterns`;
   read `$ROOT/prompts/analysis-prompt.md`, `suggestion-prompt.md`, `verification-prompt.md` →
   `prompts = { analysis, suggestion, verification }`; read `$ROOT/config/default.config.json` →
   `config`.

4. **Run the engine:**

   ```text
   Workflow({
     scriptPath: "$ROOT/workflows/humanize.js",
     args: { text, patterns, prompts, mechanicalFindings, config }
   })
   ```

5. **Write the revision.** Write the returned `revisedText` to a sibling `<name>.humanized.<ext>`
   (never overwrite the input). Show the user a diff of `<file>` → the revision.

6. **Print the on-screen report** (no file). Two sections, grouped by priority:
   - `✔ Fixed` — counts from `fixedByPriority`.
   - `⚠ Still flagged` — the `residual` findings (span + why), grouped critical/high/medium/low.
     Include the `fidelity` and `quality` verdicts.

7. **Create residual tasks.** For each finding in `residual`, create ONE task-list entry, its
   priority = the finding's `priority`. If `residual` is empty, create no tasks — say it's clean.

## Fallback (no Workflow tool)

If the Workflow tool is unavailable in this harness, do not fail. Instead run the same phases
inline: dispatch the 3 analyze lenses and 4 reviewers as subagents (Agent tool), do the revise
step yourself, and apply the same loop-until-clean logic, then produce the same report + tasks.
