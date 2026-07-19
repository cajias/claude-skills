---
name: claude-workflow-tdd-harness
description: |
  Reusable Node.js harness for unit-testing Claude Code Workflow scripts
  (the `Workflow` tool's `.js` files) with `node:test`. Use when: (1) you
  need to test a Workflow script's args contract / phase order / per-agent
  schema shape WITHOUT actually invoking the Workflow tool (which spawns
  real agents, costs tokens, is slow, and is only available in the parent
  session); (2) `node --test` rejects the file with `SyntaxError:
  Unexpected token 'export'` or `Illegal return statement` because the
  script uses top-level `await`, top-level `return`, and injected globals
  (`agent`, `phase`, `log`, `budget`, `parallel`, `pipeline`, `workflow`);
  (3) you want a per-label mock-agent dispatch pattern so each `agent()`
  call can return a different shape; (4) you want budget-gate /
  short-circuit / phase-order tests to land before any live Workflow call.
  Ships a ~110-line ESM harness (no deps) that strips `export const
  meta = {...}` via brace-counting, wraps the body in `AsyncFunction`,
  injects configurable mocks for all Workflow globals.
author: Claude Code
version: 1.0.0
date: 2026-06-02
---

# claude-workflow-tdd-harness

## Problem

Workflow scripts use top-level `await`, top-level `return`,
`export const meta = {...}`, and globals injected by the Workflow runtime
(`agent`, `phase`, `log`, `budget`, `parallel`, `pipeline`, `workflow`) —
none of which standard `node --test` will accept. The only way to "test"
a Workflow script without this harness is to invoke the Workflow tool
live, which spawns real Claude agents (slow + expensive + only available
in the parent session).

## Context / Trigger Conditions

- `node --check path/to/workflow.js` fails with `SyntaxError: Unexpected token 'export'` or `Illegal return statement`.
- You want to assert on a Workflow script's args contract (object / JSON string / undefined), phase order, agent schemas, short-circuit behavior, or budget gate WITHOUT a live Workflow call.
- You're adopting TDD for a plugin that ships Workflow scripts and want the test loop to be <5 seconds, not 5 minutes.

## Solution

1. Copy `scripts/harness.mjs` (shipped with this skill) into your
   project's `tests/workflows/` directory.
2. The harness exposes
   `runWorkflow({ scriptPath, args, mockAgent, mockWorkflow, budget })`
   which returns `{ result, error, agentCalls, workflowCalls, phases, logs }`
   for assertions.
3. Pattern for `mockAgent`: dispatch by `opts.label` so each `agent()`
   call can return a different shape (see Example).
4. Write tests with `node:test` + `node:assert/strict`.

How the harness works (read `scripts/harness.mjs` for the actual code):

- Reads the `.js` file.
- Strips `export const meta = {...}` via balanced-brace counting that is
  string-literal aware (won't get confused by `{` inside a string).
- Wraps the remaining body in
  `new AsyncFunction('args', 'phase', 'log', 'agent', 'parallel', 'pipeline', 'workflow', 'budget', body)`.
- Calls it with the mock injections.
- Returns the structured result for the test to assert on.

## Verification

After dropping the harness in place:

```bash
node --test tests/workflows/*.test.mjs
```

should run without `SyntaxError`. The tests themselves drive what passes
and what fails.

## Example

Pattern for a single test:

```js
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { runWorkflow } from './harness.mjs'

const mockAgent = (_prompt, opts) => {
  const label = opts?.label || ''
  if (label === 'preflight') return { ok: true /* schema-shaped */ }
  if (label === 'launch')    return { ok: true, runId: 'r0', pid: 1 /* ... */ }
  if (label.startsWith('watch:')) return { stillRunning: false /* ... */ }
  return null
}

test('CONTRACT: args contract — happy path reaches first agent', async () => {
  const r = await runWorkflow({
    scriptPath: '/abs/path/to/my-workflow.js',
    args: { workingDir: '/tmp/x' },
    mockAgent,
  })
  assert.equal(r.error, null)
  assert.match(r.agentCalls[0].prompt, /workingDir.*\/tmp\/x/)
})
```

Reference examples (real, exercised in production):

- `nautilus-competition/tests/workflows/babysitter.test.mjs` — 7 tests
  including preflight-short-circuit and budget gate.
- `nautilus-competition/tests/workflows/single-team-driver.test.mjs` — 7
  tests including args contract for object / JSON-string / undefined and
  `gatePassed` early-exit.
- `nautilus-competition/tests/workflows/forensics.test.mjs` — 6 tests
  including phase order and per-team pipeline cardinality.

## Notes

- Budget-gate tests need a STATEFUL `remaining()` mock because the script
  calls `budget.remaining()` multiple times per loop iteration. A
  constant-low value will exit the loop on iteration 0 before any agent
  runs, which is rarely what you want to assert on.
- The harness's `pipeline()` mock iterates items sequentially (await per
  item, stages applied in order) and passes the REAL runtime stage
  contract `(prevResult, originalItem, index)` — scripts that use
  `originalItem` in later stages (common for labeling) depend on this. If the production script depends on
  per-item concurrency, use `parallel(items.map(t => () => fn(t)))`
  instead and assert label cardinality, not wall-clock.
- The default `budget` is
  `{ total: null, spent: () => 0, remaining: () => Infinity }` — override
  per-test when you want to drive gate behavior.
- Pair with `[[claude-workflow-authoring-gotchas]]` to catch the
  meta-literal + args-contract traps before they reach a live Workflow
  call.

## References

- Cross-link: `[[claude-workflow-authoring-gotchas]]` — the three traps
  this harness pins as tests.
