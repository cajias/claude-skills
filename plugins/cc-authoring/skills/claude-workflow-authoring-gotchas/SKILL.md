---
name: claude-workflow-authoring-gotchas
description: |
  Four gotchas that bite when authoring Claude Code Workflow scripts (the
  `Workflow` tool's `.js` files with `export const meta`). Use when: (1)
  Workflow tool call fails immediately with `Invalid workflow script: meta
  must be a pure literal: non-literal node type in meta: BinaryExpression`;
  (2) the script's `args` field arrives as `undefined`/`null`/JSON-string
  even though the caller passed an object; (3) you're starting a new
  Workflow script and want to skip the trial-and-error round on these
  traps; (4) the workflow returns ready/green but agents resolved a
  DIFFERENT file than the one passed via args — a literal "undefined" in
  a prompt made them self-heal onto a substitute source. Covers the
  pure-literal-meta requirement (no string concat, no template literals,
  no variable references inside the `meta` literal), the args delivery
  contract (normalize for object / JSON-string / undefined shapes),
  informative-error patterns for missing required args (multi-line throw
  including the expected Workflow tool invocation), and the silent
  wrong-ground-truth cascade that unnormalized args cause downstream.
author: Claude Code
version: 1.1.0
date: 2026-06-02
---

# claude-workflow-authoring-gotchas

## Problem

Authoring Workflow scripts has four small traps that the Workflow tool's
error messages don't fully explain. Each takes a failed invocation
round-trip to discover. They compound: fixing one surfaces the next.

## Context / Trigger Conditions

- The Workflow tool call rejects the script with `meta must be a pure literal: non-literal node type in meta: BinaryExpression` (or `TemplateLiteral`, or `Identifier`).
- The Workflow tool call succeeds, the script runs, but immediately throws `args.<field> is required` even though the caller passed `args: {<field>: "value"}` in the tool call.
- You're starting a NEW Workflow script and don't want to ship through three rounds of broken tool calls.

## Solution

### Trap 1: `meta` must be a pure literal

The Workflow runtime parses the `meta` block via AST and rejects anything
that isn't a literal value. Forbidden node types include `BinaryExpression`
(string concat), `TemplateLiteral` with substitutions, `Identifier`
(variable reference), and `CallExpression` (function call).

```js
// BAD — BinaryExpression
description: 'Foo ' + 'bar',
// BAD — TemplateLiteral with substitutions
description: `Foo ${something}`,
// BAD — variable reference (Identifier)
description: DESCRIPTION_CONST,
// BAD — function call
description: makeDescription(),
```

Allowed: a single string literal (any length), object literals, array
literals, number/boolean literals. If the string is long, keep it on a
single line — long lines are fine. Do NOT break it across multiple
quoted pieces and concatenate; that produces a `BinaryExpression`.

### Trap 2: `args` delivery contract

Per the Workflow tool docs, `args` is passed verbatim. Empirically
observed shapes in the wild:

- Object — the documented happy path.
- JSON-encoded string — caller serialized it before passing.
- `undefined` — caller forgot the `args:` key, or some other delivery
  failure mode.

Robust pattern at the top of every parametrized script:

```js
let opts = args
if (typeof opts === 'string') {
  try { opts = JSON.parse(opts) } catch { opts = {} }
}
opts = opts || {}
```

### Trap 3: Informative error on missing required args

When `opts.X` is undefined, throw a multi-line error that includes:

1. The exact field name that's missing.
2. `Got args=${JSON.stringify(args)}` — surfaces what the runtime actually delivered.
3. A hint that `args=undefined` likely means the caller forgot the `args:` key.
4. The EXACT Workflow tool invocation shape the caller should use.

```js
if (!opts.workingDir || typeof opts.workingDir !== 'string') {
  throw new Error(
    `args.workingDir is required (absolute path).
Got args=${JSON.stringify(args)}. If args is undefined the caller likely forgot the \`args:\` key.
Expected tool invocation:
  Workflow({
    scriptPath: "<this-file>",
    args: { workingDir: "/abs/path" }
  })`,
  )
}
```

### Trap 4: Silent wrong-ground-truth cascade (downstream of Trap 2)

Observed 2026-07-11. When an unnormalized `args.x` interpolates as the
literal string `"undefined"` into an agent prompt (e.g. "read the CV
source file at: undefined"), capable agents do NOT fail — they self-heal
by searching the filesystem for a plausible substitute (here: an outdated
resume PDF found on disk instead of the intended master markdown). Every
downstream verifier then validates faithfully against the substituted
source, producing a confident all-green verdict on wrong ground truth.
The workflow returns `ready: true`; only cross-checking the verifier
NOTES against what the orchestrator knows (source-path mismatch,
contradicting facts) exposes it.

Mitigations:

1. Prefer inlining known-constant paths/values directly in the script's
   template literals instead of routing them through `args` at all.
2. Normalize args defensively (Trap 2) AND throw loudly if a required
   field is missing:
   `if (!opts.cvPath) throw new Error('cvPath missing — args arrived as ' + typeof args)`
   — a thrown workflow is cheaper than a confidently wrong one.
3. In verifier prompts, pin the exact ground-truth path and instruct:
   "if this exact file is missing or unreadable, report a blocker — do
   NOT substitute another source."
4. Orchestrator habit: on completion, diff the verifier-reported source
   paths/facts against what you passed in before trusting `ready: true`.

## Verification

- Trap 1: re-invoke the Workflow tool; `Invalid workflow script: meta must be a pure literal` no longer appears.
- Trap 2 + 3: pass `args` in three shapes via unit tests using the harness from the `claude-workflow-tdd-harness` skill. All three should reach the first agent call (or throw the informative error in the undefined case).
- Trap 4: grep the composed agent prompts (or the script's template literals under an undefined-args test) for the literal string `undefined` — none should reach an agent.

## Example

Reference implementation:
`nautilus-competition/plugins/nautilus-competition/workflows/competition-single-team-driver.js`

- Lines 1-11: pure-literal `meta` (single-line strings, no concat, no template literals, no variable references).
- Lines 13-45: args normalization (`opts = args`, JSON-parse if string, `opts || {}`) plus informative throws that surface the actual `args` shape and show the expected tool invocation.

Do not copy that file verbatim — copy the pattern.

## Notes

- The `args=undefined` delivery failure observed in this session was never
  explained empirically — a retry with the same JSON shape went through.
  Defensive normalization + informative throws are the durable fix;
  diagnosing the upstream delivery bug is a separate investigation.
- Pair this skill with `claude-workflow-tdd-harness` to lock the
  gotchas in as tests instead of trial-and-error against the live
  Workflow tool.

## References

- Cross-link: `[[claude-workflow-tdd-harness]]` — testing pattern that
  catches these traps locally before any live Workflow call.
