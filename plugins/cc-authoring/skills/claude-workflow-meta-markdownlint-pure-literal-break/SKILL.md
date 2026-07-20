---
name: claude-workflow-meta-markdownlint-pure-literal-break
description: |
  Fix for a Claude Code Workflow script that fails to load with "meta must be a
  pure literal: non-literal node type in meta: BinaryExpression" even though the
  meta block looks fine and all its tests pass. Use when: (1) a workflow .js is
  rejected at load over meta/BinaryExpression; (2) workflow tests are green but the
  real Workflow tool rejects the script; (3) a long meta.description (or name)
  string; (4) the workflow code lives in or is documented inside a markdown file
  that a markdownlint/prettier pre-commit hook reformats. Root cause: line-length
  wrapping split a single string literal into `'a' + 'b'` concatenation.
author: Claude Code
version: 1.0.0
date: 2026-07-04
---

# Markdownlint wrapping breaks a Workflow's pure-literal `meta`

## Problem

A Workflow `.js` that previously loaded (or whose `meta` you wrote as a plain string) starts
failing at load with:

```
Invalid workflow script: meta must be a pure literal: non-literal node type in meta: BinaryExpression
```

…and — the trap — **its test suite still passes**, so nothing warns you.

## Context / Trigger Conditions

- The error names `meta` and `BinaryExpression`.
- The workflow's own tests (via the TDD harness) are green, but the real Workflow tool rejects
  the script.
- `meta.description` (or another meta string) is long.
- The workflow code was committed inside, or copied from, a markdown file (a plan, a README,
  a doc) that has a markdownlint/prettier pre-commit hook.

## Root cause

The Workflow runtime AST-parses `export const meta = {…}` and rejects any non-literal node —
including a `BinaryExpression` (string `+` concatenation). A **markdownlint MD013 (line-length)
or prettier reformat** of a fenced code block will wrap a long single-line string literal into
concatenated pieces to satisfy the max line width:

```js
// what you wrote (pure literal — OK):
description: "Multi-agent humanizer: analyze, revise, review, loop.",

// what the lint/format hook turned it into (BinaryExpression — REJECTED):
description:
  "Multi-agent humanizer: analyze, " +
  "revise, review, loop.",
```

**Why tests don't catch it:** the TDD harness (`harness.mjs` `stripMetaBlock`) locates
`export const meta = {…}` by brace-counting and deletes the whole block **textually** before
wrapping the body in an `AsyncFunction`. `meta` is never parsed or validated, so a broken
`meta` sails through every harness test.

## Solution

1. **Keep `meta` strings as short single literals** that fit under the line limit, so no
   formatter is ever tempted to wrap them. This is the simplest durable fix.
2. **Or exempt code blocks from line-length**: set markdownlint MD013 `code_blocks: false`
   (or disable MD013 in the file) so it stops rewriting fenced code.
3. **Independently verify `meta` purity — the harness can't.** After any lint/format pass over
   a file containing workflow code, grep the `meta` block for `+`, a template `${`, or a
   variable reference. If present, `meta` is broken regardless of green tests.

## Verification

Reproduced this session: a long single-line `meta.description` was silently split into three
`+`-joined literals when a subagent wrapped long lines to satisfy markdownlint on the plan
`.md` that contained the workflow code. All 5 harness tests passed; a manual read of the `meta`
block caught the `+`. Rewriting it as one short literal fixed the load without changing tests.

## Notes

- The same failure mode applies to `name` or any string inside `meta`, and to template literals
  (`` `${x}` ``) and variable references — anything that isn't a plain literal node.
- String `+` concatenation elsewhere in the workflow BODY (e.g. building a `throw new Error(...)`
  message) is legal; only the `meta` object must be a pure literal.
- Related: `claude-workflow-authoring-gotchas` (the pure-literal `meta` rule + `args` contract),
  `claude-workflow-tdd-harness` (why the harness misses this), and
  `claude-workflow-plugin-distribution`.
