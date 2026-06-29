---
name: claude-skills:tdd-plan
description: Use when user says "create a tdd plan", "tdd loop", "iterative plan", "ralph-loop plan", "create plan for ralph". Generates a TDD-based plan formatted for ralph-loop execution with concurrent tasks, pr-review validation, and optional deploy/integration test steps.
---

# TDD Plan Generator for Ralph-Loop

I generate comprehensive TDD-based plans formatted for execution via `ralph-loop`.
The plan includes master goals, concurrent task phases, and strict exit criteria
including code review validation.

## When I Activate

I automatically activate when you:

- Ask to "create a TDD plan"
- Want an "iterative plan using ralph-loop"
- Need a plan with "concurrent tasks"
- Ask for a plan that "runs until tests pass"
- Want to "use pr-review" as part of validation

## Required Inputs

When invoking this skill, provide:

1. **Task description** (required): What you want to accomplish
2. **Deploy command** (optional): e.g., `npm run deploy`
3. **Integration test command** (optional): e.g., `npm run test:integration`

### Example Invocation

```bash
/tdd-plan Implement user authentication with JWT tokens
  --deploy-cmd "npm run deploy"
  --integration-cmd "npm run test:integration"
```

## Generated Plan Structure

I generate a plan with this structure:

````markdown
# Ralph Loop Plan: <task description>

## Master Goals (Immutable)

These goals remain constant throughout all iterations:

- [ ] Goal 1: <derived from task>
- [ ] Goal 2: <derived from task>
- [ ] Goal N: <derived from task>

## Exit Criteria

The loop completes when ALL of these are satisfied:

- [ ] All master goals marked complete
- [ ] Unit tests pass (`npm test`)
- [ ] Build succeeds (`npm run build`)
- [ ] Lint passes (`npm run lint`)
- [ ] Deploy succeeds: `<deploy-cmd>` (if provided)
- [ ] Integration tests pass: `<integration-cmd>` (if provided)
- [ ] `/pr-review-toolkit:review-pr` finds no issues

## Investigation Tracker

Prevents retrying failed approaches across iterations:

| Iteration                    | Issue | Attempted Fix | Result | Next Action |
| ---------------------------- | ----- | ------------- | ------ | ----------- |
| (populated during execution) |

## Current Iteration Plan

### Phase 1: RED - Write Failing Tests

[Concurrent where possible]

- [ ] Test for goal 1
- [ ] Test for goal 2

### Phase 2: GREEN - Implement

[Sequential, implementing each goal]

- [ ] Implement goal 1
- [ ] Implement goal 2

### Phase 3: REFACTOR

[Concurrent where possible]

- [ ] Clean up implementation
- [ ] Remove duplication
- [ ] Improve naming

### Phase 4: VALIDATE

1. Run unit tests
2. Run build & lint
3. Deploy (if command provided)
4. Run integration tests (if command provided)
5. Run `/pr-review-toolkit:review-pr`
6. Collect issues found

### Phase 5: COMMIT

Commit with message describing what was accomplished in this iteration:

```text
feat(<scope>): <what was done>

- Completed: <list of completed goals>
- Fixed: <list of issues resolved>

```

### Phase 6: EVALUATE

- If all exit criteria met → DONE
- If issues found → Add to Investigation Tracker, generate new plan for next iteration
````

## Iteration Workflow

```text
┌─────────────────────────────────────────────────────────┐
│  MASTER GOALS (immutable, set at start)                 │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────── ITERATION N ──────────┐
         │                                 │
         │  1. CREATE PLAN                 │
         │     - Check remaining goals     │
         │     - Review investigation log  │
         │     - Plan concurrent tasks     │
         │                                 │
         │  2. EXECUTE TDD PHASES          │
         │     RED → GREEN → REFACTOR      │
         │                                 │
         │  3. VALIDATE                    │
         │     - Unit tests                │
         │     - Build & lint              │
         │     - Deploy (optional)         │
         │     - Integration tests (opt)   │
         │     - PR review                 │
         │                                 │
         │  4. COMMIT                      │
         │     Message: what was done      │
         │                                 │
         │  5. CHECK EXIT CRITERIA         │
         │     All met? → DONE             │
         │     Issues?  → Log & continue   │
         └─────────────────────────────────┘
                          │
                          ▼
              Next iteration uses:
              - Remaining goals
              - Issues from validation
              - Investigation history
```

## My Process

### Step 1: Analyze Task

I break down your task into discrete, testable goals.

### Step 2: Generate Master Goals

I create an immutable list of goals that define "done."

### Step 3: Create Initial Plan

I generate the first iteration plan with:

- Concurrent test writing where possible
- Sequential implementation (dependencies respected)
- Concurrent refactoring tasks

### Step 4: Define Validation

I set up the validation phase with all provided commands and always include pr-review.

### Step 5: Output Plan

I output the complete plan in a format ready for ralph-loop.

## Concurrency Rules

I maximize concurrency where safe:

**Can run in parallel:**

- Writing independent tests
- Running lint + type-check
- Refactoring unrelated code
- PR review + static analysis

**Must run sequentially:**

- Write test → Implement feature (TDD red-green)
- Build → Deploy → Integration tests
- Fix issue → Re-validate

## Integration with Ralph-Loop

After I generate the plan, start the loop with:

```bash
/ralph-loop:ralph-loop
```

Ralph will:

1. Read the plan from scratchpad
2. Execute the current iteration
3. Update investigation tracker
4. Generate next iteration plan if needed
5. Repeat until exit criteria met

## Example Output

For input: "Implement header forwarding in MCP multiplexer"

````markdown
# Ralph Loop Plan: Implement Header Forwarding in MCP Multiplexer

## Master Goals (Immutable)

- [ ] Forward client request headers to upstream CPRs
- [ ] Pass upstream CPR response headers back to client
- [ ] Handle missing/malformed headers gracefully
- [ ] Maintain existing functionality (no regressions)

## Exit Criteria

- [ ] All master goals marked complete
- [ ] Unit tests pass
- [ ] Build succeeds
- [ ] Lint passes
- [ ] Deploy succeeds: `npm run deploy`
- [ ] Integration tests pass: `npm run test:integration`
- [ ] `/pr-review-toolkit:review-pr` finds no issues

## Investigation Tracker

| Iteration | Issue | Attempted Fix | Result | Next Action |
| --------- | ----- | ------------- | ------ | ----------- |

## Current Iteration Plan

### Phase 1: RED - Write Failing Tests

[Concurrent]

- [ ] Test: request headers are forwarded to upstream
- [ ] Test: response headers are passed to client
- [ ] Test: missing headers handled gracefully

### Phase 2: GREEN - Implement

- [ ] Add header extraction in request handler
- [ ] Forward headers in upstream calls
- [ ] Capture and return response headers

### Phase 3: REFACTOR

[Concurrent]

- [ ] Extract header utilities if needed
- [ ] Ensure consistent error handling

### Phase 4: VALIDATE

1. `npm test`
2. `npm run build && npm run lint`
3. `npm run deploy`
4. `npm run test:integration`
5. `/pr-review-toolkit:review-pr`

### Phase 5: COMMIT

```text
feat(mcp-multiplexer): implement bidirectional header forwarding

- Forward client headers to upstream CPRs
- Pass response headers back to client

```

### Phase 6: EVALUATE

Check exit criteria, log issues, generate next iteration if needed.
````

## Tips for Best Results

- **Be specific**: More detail = better goal breakdown
- **Provide commands**: Deploy and integration test commands enable full validation
- **Trust the loop**: Let ralph iterate until clean
- **Check the tracker**: Investigation history prevents wasted effort

## Related Skills

- **ralph-loop:ralph-loop**: Executes the generated plan
- **pr-review-toolkit:review-pr**: Code review validation
- **orchestration:creating-workflows**: For complex multi-agent workflows

---

**Ready to create a TDD plan? Describe your task and I'll generate a ralph-loop-ready plan!**
