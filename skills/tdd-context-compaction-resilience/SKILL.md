---
name: tdd-context-compaction-resilience
description: |
  Fix TDD workflow state loss during Claude Code context compaction. Use when:
  (1) Agent forgets which TDD phase (RED/GREEN/REFACTOR) it's in after long sessions,
  (2) Agent repeats exploration/investigation work it already did,
  (3) Ralph-loop iterations lose track of failed approaches,
  (4) Scratchpad exists but agent still loses TDD discipline,
  (5) User has to remind agent "you already tried that" or "write tests first".
  Covers structured state persistence, investigation tracking, and compaction-resistant markers.
author: Claude Code
version: 1.0.0
date: 2026-01-25
tags: [tdd, context-compaction, ralph-loop, scratchpad, state-persistence]
---

# TDD Context Compaction Resilience

## Problem

When Claude Code compacts context during long TDD sessions, the agent loses:

- Current TDD phase (RED/GREEN/REFACTOR)
- Knowledge of what approaches were already tried
- Understanding of which tests were written vs. which need to be written
- Phase gate enforcement ("don't implement until tests fail")

This causes the agent to:

- Skip the RED phase and jump to implementation
- Repeat failed investigations
- Re-explore code it already analyzed
- Lose track of the overall TDD plan

## Context / Trigger Conditions

**Symptoms indicating this problem:**

- Agent says "Let me explore the codebase" when it already did
- Same error message or exploration output appears multiple times in session
- Agent starts writing implementation code without failing tests
- User sees "This session is being continued from a previous conversation that ran out of context"
- Agent proposes approaches it already tried and failed

**Diagnostic checks:**

```bash
# Count context compactions in a session
grep -c "Conversation compacted" ~/.claude/projects/-Users-*/SESSION_ID.jsonl

# Find repeated exploration messages
grep -h '"role":"user"' SESSION_FILE.jsonl | grep -o '"text":"[^"]*"' | sort | uniq -c | sort -rn | head -10
```

## Root Cause

The scratchpad.md file typically stores:

- Task goals ✅
- Exit criteria ✅
- Task status (done/not done) ✅

But it does NOT store:

- Current TDD phase (RED/GREEN/REFACTOR) ❌
- Phase validation checklist status ❌
- Investigation tracker with failed attempts ❌
- Test file locations created in RED phase ❌

Context compaction summarizes prose instructions equally, so "MANDATORY: Write tests first" gets as much priority as
"nice to have: add comments".

## Solution

### 1. Add Structured Phase State to Scratchpad

Replace prose TDD notes with structured state:

````markdown
## TDD Phase State (DO NOT SUMMARIZE - RESTORE VERBATIM)

```yaml
current_phase: RED # RED | GREEN | REFACTOR
phase_start: 2026-01-25T10:00:00Z
iteration: 1
```
````

### RED Phase Metrics

| Metric            | Value                                                   |
| ----------------- | ------------------------------------------------------- |
| New Tests Written | 3                                                       |
| Tests Failing     | 3                                                       |
| Test Files        | `src/handler.test.ts:45-89`, `src/client.test.ts:12-34` |

### Phase Validation Checklist

- [x] Written NEW test files (not just run existing)
- [x] All new tests FAIL with meaningful errors
- [ ] Ready to proceed to GREEN

⚠️ PHASE GATE: Cannot start GREEN until all boxes checked above.

````text

### 2. Populate Investigation Tracker

Actually USE the investigation tracker defined in TDD plans:

```markdown
## Investigation Tracker (READ BEFORE EACH ITERATION)
| Iteration | Issue | Attempted Fix | Result | Next Action |
|-----------|-------|---------------|--------|-------------|
| 1 | Test timeout | Increased to 30s | Still fails | Check async handling |
| 1 | Mock not called | Added jest.mock() | Works | None |
| 2 | Type error | Cast to unknown | Fails | Try generic |
````

**Auto-population rule**: After ANY failure (test, build, lint), add a row IMMEDIATELY.

### 3. Add Compaction-Resistant Markers

Wrap critical instructions in markers that signal importance to summarization:

```markdown
<!-- CRITICAL: Preserve verbatim during context compaction -->

⚠️ PHASE GATE: I am in RED phase. I CANNOT write implementation until:

1. I have created NEW test files (listed above)
2. Those tests FAIL with meaningful errors
3. Phase validation checklist is complete
<!-- /CRITICAL -->
```

### 4. Add Phase Enforcement Hook (Optional)

Create a PreToolUse hook to block implementation before GREEN:

```yaml
# .claude/hooks/enforce-tdd-red.yaml
name: enforce-tdd-red-phase
trigger: PreToolUse
tools: [Edit, Write]
match:
  file_patterns:
    - "src/**/*.ts"
    - "!src/**/*.test.ts"
    - "!src/**/*.spec.ts"
conditions:
  - scratchpad_contains: "current_phase: RED"
action: block
message: |
  ⚠️ TDD VIOLATION: Cannot modify implementation files during RED phase.
  Current phase: RED (write failing tests first)

  To proceed:
  1. Write failing tests in *.test.ts files
  2. Update scratchpad: current_phase: GREEN
  3. Then modify implementation
```

### 5. Session Start Restoration

At the start of each session or iteration, add this prompt pattern:

```markdown
## Session Restoration Checklist

Before starting work, I MUST:

1. Read `.agent/scratchpad.md` for current phase state
2. Read Investigation Tracker for failed approaches
3. Identify: Current phase = [phase], Test files = [files], Last failure = [failure]
4. Resume from that exact point, not from scratch
```

## Verification

After implementing these patterns:

1. **Phase state persists**: After compaction, agent knows it's in GREEN phase
2. **No repeated exploration**: Agent doesn't re-analyze code it already read
3. **Failed approaches remembered**: Agent doesn't retry the same fix twice
4. **Phase gates enforced**: Agent refuses to implement without failing tests

**Test by:**

```bash
# Simulate long session
# 1. Start TDD task
# 2. Complete RED phase
# 3. Force compaction (or wait for natural compaction)
# 4. Ask agent "what phase are we in?" - should answer correctly
# 5. Ask agent "what have we tried?" - should list investigation tracker
```

## Example

**Before (state lost after compaction):**

```text
Session 1: "I'll write failing tests for the handler"
  -> Writes 3 tests, all fail
  -> [COMPACTION]
Session 1 (continued): "Let me explore the codebase to understand the handler"
  -> Re-explores same code
  -> Starts implementing without checking if tests exist
```

**After (state preserved):**

```text
Session 1: "I'll write failing tests for the handler"
  -> Writes 3 tests, all fail
  -> Updates scratchpad: current_phase: RED, tests: [list], failing: 3
  -> [COMPACTION]
Session 1 (continued): "Restoring from scratchpad... Phase: RED complete,
   3 failing tests in handler.test.ts. Moving to GREEN phase."
  -> Updates scratchpad: current_phase: GREEN
  -> Implements minimal code to pass tests
```

## Notes

- **Scratchpad location**: Use `.agent/scratchpad.md` (ralph-loop convention)
- **YAML in markdown**: Use YAML blocks for structured state (easier to parse)
- **Investigation tracker**: Read BEFORE starting, update AFTER any failure
- **Phase transitions**: Only change `current_phase` when validation checklist complete
- **Test file tracking**: Record exact file:line ranges for created tests

## Related Patterns

- **Ralph-loop integration**: This pattern complements ralph-loop's iterative approach
- **TodoWrite discipline**: Use `RED:`, `GREEN:`, `REFACTOR:` prefixes in todo items
- **Exit criteria**: Keep separate from phase state (exit criteria = done, phase = how)

## Orchestration Discipline (Additional Failure Mode)

Another common failure after context compaction: **agent forgets to delegate and does work itself**.

### Symptoms

- Agent starts doing investigation/implementation directly instead of spawning sub-agents
- Concurrent task opportunities missed (sequential execution when parallel is possible)
- Task dependencies not tracked in TodoWrite
- Agent forgets the orchestration pattern mid-session

### Solution: Add Orchestration State to Scratchpad

````markdown
## Orchestration Rules (DO NOT SUMMARIZE - RESTORE VERBATIM)

```yaml
execution_mode: orchestrate # orchestrate | direct
delegation_required: true # Must use sub-agents for implementation
concurrency_target: maximum # Parallelize independent tasks
```
````

### Task Dependency Graph

| Task                | Depends On    | Assignee        | Status  |
| ------------------- | ------------- | --------------- | ------- |
| Explore codebase    | -             | Explore agent   | done    |
| Write failing tests | Explore       | general-purpose | pending |
| Run tests           | Write tests   | Bash            | blocked |
| Implement feature   | Tests written | general-purpose | blocked |

### Orchestration Checklist (MANDATORY)

- [ ] All tasks added to TodoWrite with dependencies
- [ ] Independent tasks marked for parallel execution
- [ ] Sub-agents assigned for implementation work
- [ ] Main agent only coordinates, does NOT implement directly

⚠️ ORCHESTRATION GATE: I MUST delegate implementation to sub-agents.
I am the coordinator. I schedule tasks, I do NOT execute them myself.

```text

### TodoWrite Discipline

Always use TodoWrite with clear structure:
```

- [pending] EXPLORE: Analyze codebase structure (assign: Explore agent)
- [pending] RED: Write failing tests for feature X (assign: general-purpose, depends: EXPLORE)
- [blocked] GREEN: Implement feature X (assign: general-purpose, depends: RED)
- [blocked] REFACTOR: Clean up implementation (assign: general-purpose, depends: GREEN)

````text

**Rules:**
1. EVERY task gets a TodoWrite entry
2. Dependencies are explicit (`depends: TASK_NAME`)
3. Assignee is specified (`assign: agent-type`)
4. Independent tasks should be launched in parallel via multiple Task tool calls in ONE message

### Concurrent Execution Pattern

When tasks are independent, launch them together in a SINGLE message with multiple tool calls:

```text

## CORRECT - Single message, multiple Task tool calls

Message 1:

- Task(prompt="Explore auth module", subagent_type="Explore")
- Task(prompt="Explore database module", subagent_type="Explore")
- Task(prompt="Explore API module", subagent_type="Explore")

## WRONG - Sequential messages for independent tasks

Message 1: Task(prompt="Explore auth module", ...)
[wait for result]
Message 2: Task(prompt="Explore database module", ...)
[wait for result]
Message 3: Task(prompt="Explore API module", ...)

````

### Anti-Patterns to Avoid After Compaction

**1. Doing work instead of delegating:**

```text

## WRONG - Main agent does the work itself

"Let me explore the codebase..."
[Reads files directly]
[Writes implementation directly]

## CORRECT - Main agent schedules sub-agents

"I'll delegate this exploration to sub-agents..."
[Spawns Explore agent]
[Spawns general-purpose agent for implementation]

```

**2. Sequential execution when parallel is possible:**

```text

## WRONG - Tasks run one at a time

Step 1: Explore module A -> wait ->
Step 2: Explore module B -> wait ->
Step 3: Explore module C

## CORRECT - Independent tasks run together

Step 1: [Explore A || Explore B || Explore C] ->
Step 2: Synthesize findings

```

**3. Missing task dependencies:**

```text

## WRONG - No dependency tracking

- [ ] Write tests
- [ ] Implement feature
- [ ] Run tests

## CORRECT - Explicit dependencies

- [pending] RED: Write failing tests (no dependencies)
- [blocked] GREEN: Implement feature (depends: RED)
- [blocked] RUN: Execute tests (depends: GREEN)

```

**4. Not using TodoWrite:**

````text

## WRONG - Tasks only in prose/conversation

"First I'll explore, then write tests, then implement..."

## CORRECT - All tasks in TodoWrite

TodoWrite([
  {content: "Explore codebase", status: "in_progress"},
  {content: "Write failing tests", status: "pending"},
  {content: "Implement feature", status: "pending"}
])

```text

## Summary: What to Persist in Scratchpad

To survive context compaction, the scratchpad MUST contain:

| Category | Required Fields | Purpose |
|----------|-----------------|---------|
| TDD Phase | `current_phase`, `iteration`, `phase_start` | Know where in RED/GREEN/REFACTOR |
| Tests | Test file paths, failing count | Don't re-write existing tests |
| Investigation | Failed attempts table | Don't retry failed approaches |
| Orchestration | `execution_mode`, `delegation_required` | Remember to use sub-agents |
| Dependencies | Task dependency graph | Know what's blocked |

**The golden rule**: If you would be frustrated to lose it after compaction, it MUST be in structured YAML or tables in
  the scratchpad, not prose.
````
