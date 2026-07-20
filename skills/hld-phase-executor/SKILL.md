---
name: hld-phase-executor
description: This skill should be used when the user asks to "execute an HLD", "implement a high-level design", "run phased migration", "execute architecture phases", "implement HLD with TDD", or has a multi-phase project document (HLD, architecture doc, migration plan) that needs systematic implementation with phase gates and dependency tracking.
version: 1.0.0
---

# HLD Phase Executor

Execute High-Level Design documents through systematic, gated phases with TDD methodology and dependency tracking.

## Overview

This skill transforms HLD documents into executable phase plans, ensuring:

- Each phase follows RED-GREEN-REFACTOR
- Phase gates prevent premature advancement
- Cross-phase dependencies are tracked and respected
- Deployment validation gates each phase transition
- Phase collapsing is prevented through strict ordering

**Core principle:** A phase cannot start until all blocking phases complete AND pass their validation gates.

## When This Skill Activates

- User provides an HLD, architecture document, or migration plan
- User asks to "execute phases", "implement HLD", or "phased implementation"
- Complex multi-phase projects requiring ordered execution
- Infrastructure or code migrations with dependencies

## Dependencies

| Dependency                                   | Purpose                           |
| -------------------------------------------- | --------------------------------- |
| `tdd-plan`                                   | Generate TDD plans for each phase |
| `ralph-loop:ralph-loop`                      | Execute iterative TDD loops       |
| `superpowers:verification-before-completion` | Pre-completion validation         |

## Phase Execution Model

```text
HLD Document
     │
     ▼
┌─────────────────────────────────────────────────┐
│  PHASE 0: HLD PARSING & DEPENDENCY ANALYSIS     │
│  - Extract phases from document                 │
│  - Build dependency graph                       │
│  - Identify phase gates and validation criteria │
└─────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────┐
│  PHASE N: EXECUTION (for each phase)            │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │ 1. DEPENDENCY CHECK                       │  │
│  │    - Verify all blockedBy phases complete │  │
│  │    - Verify their validation gates passed │  │
│  └───────────────────────────────────────────┘  │
│                   │                             │
│                   ▼                             │
│  ┌───────────────────────────────────────────┐  │
│  │ 2. MINI TDD PLAN                          │  │
│  │    - Generate phase-specific goals        │  │
│  │    - Create RED-GREEN-REFACTOR plan       │  │
│  │    - Define phase exit criteria           │  │
│  └───────────────────────────────────────────┘  │
│                   │                             │
│                   ▼                             │
│  ┌───────────────────────────────────────────┐  │
│  │ 3. TDD EXECUTION                          │  │
│  │    RED: Write failing tests               │  │
│  │    GREEN: Minimal implementation          │  │
│  │    REFACTOR: Clean up                     │  │
│  └───────────────────────────────────────────┘  │
│                   │                             │
│                   ▼                             │
│  ┌───────────────────────────────────────────┐  │
│  │ 4. PHASE VALIDATION GATE                  │  │
│  │    - Run phase-specific tests             │  │
│  │    - Execute deployment validation        │  │
│  │    - Security/code review checks          │  │
│  │    - User checkpoint for approval         │  │
│  └───────────────────────────────────────────┘  │
│                   │                             │
│                   ▼                             │
│  ┌───────────────────────────────────────────┐  │
│  │ 5. PHASE COMPLETION                       │  │
│  │    - Mark phase complete                  │  │
│  │    - Update dependency graph              │  │
│  │    - Unblock dependent phases             │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
     │
     ▼
   NEXT PHASE (repeat until all complete)
```

## HLD Document Format

The skill parses HLD documents with this structure:

```markdown
# HLD: <Project Name>

## Phase 1: <Phase Name>

### Description

<What this phase accomplishes>

### Dependencies

- Depends on: Phase 0 (or "none" for first phase)

### Deliverables

- [ ] Deliverable 1
- [ ] Deliverable 2

### Validation Criteria

- All unit tests pass
- CDK synth succeeds
- Integration tests pass (if applicable)

### Deployment Command (optional)

`npm run deploy:phase1`

---

## Phase 2: <Phase Name>

### Dependencies

- Depends on: Phase 1

### Deliverables

...
```

## Parsing Process

### Step 1: Extract Phases

Parse the HLD to identify:

- Phase names and numbers
- Phase descriptions
- Deliverables (become TDD goals)
- Dependencies (become blockedBy)
- Validation criteria (become exit criteria)
- Deployment commands (for validation gates)

### Step 2: Build Dependency Graph

Create a directed acyclic graph (DAG):

```text
Phase 1 ──┬──► Phase 2 ──► Phase 4
          │
          └──► Phase 3 ──► Phase 4
```

Validate:

- No circular dependencies
- All referenced phases exist
- At least one phase has no dependencies (entry point)

### Step 3: Generate Phase State Tracker

Create `.agent/hld-execution-state.md`:

```markdown
# HLD Execution State: <Project Name>

## Dependency Graph

| Phase   | Depends On       | Status  | Validation |
| ------- | ---------------- | ------- | ---------- |
| Phase 1 | -                | pending | -          |
| Phase 2 | Phase 1          | blocked | -          |
| Phase 3 | Phase 1          | blocked | -          |
| Phase 4 | Phase 2, Phase 3 | blocked | -          |

## Current Phase: None

## Completed Phases

(none yet)

## Phase Execution Log

| Phase | Started | Completed | Validation Result |
| ----- | ------- | --------- | ----------------- |
```

## Phase Execution Process

### For Each Unblocked Phase

#### 1. Dependency Check

Before starting any phase:

```text
CHECK: Are all blockedBy phases complete?
  - If NO: Cannot start, remain blocked
  - If YES: Check validation gates

CHECK: Did all blockedBy phases pass validation?
  - If NO: Cannot start, dependency failed
  - If YES: Proceed to TDD plan generation
```

#### 2. Generate Mini TDD Plan

Transform phase deliverables into TDD plan:

```markdown
# Ralph Loop Plan: Phase N - <Phase Name>

## Master Goals (from HLD deliverables)

- [ ] Goal 1: <deliverable 1>
- [ ] Goal 2: <deliverable 2>

## Exit Criteria (from HLD validation criteria)

- [ ] All phase goals complete
- [ ] Unit tests pass
- [ ] Build succeeds
- [ ] Deployment validation: `<deploy-cmd>`
- [ ] Code review passes

## Current Iteration Plan

### Phase 1: RED - Write Failing Tests

- [ ] RED: Test for goal 1
- [ ] RED: Test for goal 2

### Phase 2: GREEN - Implement

- [ ] GREEN: Implement goal 1
- [ ] GREEN: Implement goal 2

### Phase 3: REFACTOR

- [ ] Clean up implementation
- [ ] Apply code simplifier

### Phase 4: VALIDATE

- [ ] Run all tests
- [ ] Execute deployment: `<deploy-cmd>`
- [ ] Run security review

### Phase 5: COMMIT
```

#### 3. Execute TDD via Ralph Loop

Invoke ralph-loop with the generated plan:

```text
Skill({ skill: "ralph-loop:ralph-loop", args: "--completion-promise 'Phase N exit criteria satisfied'" })
```

Ralph iterates until:

- All tests pass
- Deployment succeeds
- Validation criteria met

#### 4. Phase Validation Gate

After TDD completion, execute the phase gate:

**Parallel validation:**

- Unit tests: `npm test`
- Build: `npm run build`
- Lint: `npm run lint`
- Security: `/security-review`

**Sequential validation (if deployment command provided):**

- Deploy: `<phase-deploy-cmd>`
- Integration tests: `<integration-cmd>`

**User checkpoint:**

```text
@phase-N-validation-gate

Phase N: <Phase Name> completed.

Validation Results:
- Tests: PASS/FAIL
- Build: PASS/FAIL
- Deploy: PASS/FAIL (or N/A)
- Security: PASS/FAIL

Approve to proceed to dependent phases?
```

#### 5. Phase Completion

On approval:

1. Mark phase complete in state tracker
2. Record validation results
3. Update dependency graph
4. Identify newly unblocked phases
5. Proceed to next unblocked phase

## Anti-Collapse Mechanisms

### Mechanism 1: Strict Phase Ordering

Phases MUST execute in dependency order. Even if Phase 3 deliverables seem "simple", execution waits for blocking phases.

### Mechanism 2: Validation Gates

Every phase transition requires passing a validation gate. No skipping validation "because it looks fine".

### Mechanism 3: User Checkpoints

User approval required between phases. This prevents autonomous phase collapsing where the agent decides to "combine" phases.

### Mechanism 4: State Persistence

`.agent/hld-execution-state.md` persists across context windows. Even after compaction, the
agent can read state and resume correctly.

### Mechanism 5: Explicit Phase Boundaries

Each phase has:

- Clear start marker in logs
- Explicit TDD cycle
- Validation gate
- Clear completion marker

## Cross-Phase Dependency Tracking

### Shared Resources

Track resources created in earlier phases that later phases depend on:

```markdown
## Cross-Phase Resources

| Resource  | Created In | Used By    | Type      |
| --------- | ---------- | ---------- | --------- |
| UserTable | Phase 1    | Phase 2, 3 | DynamoDB  |
| AuthStack | Phase 2    | Phase 3, 4 | CDK Stack |
```

### Interface Contracts

When Phase N creates an interface that Phase N+1 consumes:

1. Phase N defines the interface in tests
2. Phase N implements the interface
3. Phase N+1 imports and tests against the interface
4. Interface changes require re-validation of dependent phases

### Rollback Points

After each phase gate:

- Create git tag: `hld-phase-N-complete`
- If later phase fails, can rollback to known-good state

## Workflow Template

Orchestration syntax for the full HLD execution:

```flow
# HLD Phase Executor Workflow

# Parse HLD and build dependency graph
general-purpose:"Parse HLD document, extract phases, build dependency DAG, create state tracker":hld_parsed ->

# Phase execution loop (conceptual - actual execution is iterative)
@phase-execution-start ->

# For each unblocked phase
general-purpose:"Check dependencies, identify next executable phase":phase_identified ->

# Generate phase TDD plan
general-purpose:"Generate mini TDD plan for phase deliverables":tdd_plan_generated ->

# Execute TDD via ralph-loop
general-purpose:"Execute ralph-loop for phase TDD cycle":tdd_complete ->

# Phase validation gate
[
  general-purpose:"Run unit tests" ||
  general-purpose:"Run build and lint" ||
  general-purpose:"Run security review"
] ->
general-purpose:"Execute deployment validation if applicable":validation_complete ->

# User checkpoint
@phase-validation-gate ->

# Mark complete and continue
general-purpose:"Mark phase complete, update state, identify next phase":phase_marked ->

@phase-execution-complete
```

## Example: Infrastructure Migration HLD

Input HLD:

```markdown
# HLD: Database Migration

## Phase 1: Create New Tables

### Dependencies: none

### Deliverables

- [ ] Create UserTableV2 with new schema
- [ ] Create indexes for query patterns

### Validation

- CDK synth succeeds
- Tables deploy to dev environment

---

## Phase 2: Dual-Write Implementation

### Dependencies: Phase 1

### Deliverables

- [ ] Write to both old and new tables
- [ ] Read from old table

### Validation

- Integration tests pass
- No data loss in writes

---

## Phase 3: Migration Script

### Dependencies: Phase 1

### Deliverables

- [ ] Backfill script for historical data
- [ ] Validation script to compare tables

### Validation

- Script completes successfully
- Data integrity verified

---

## Phase 4: Switch Reads

### Dependencies: Phase 2, Phase 3

### Deliverables

- [ ] Read from new table
- [ ] Fallback to old on errors

### Validation

- Integration tests pass
- Performance benchmarks met
```

Execution order:

1. Phase 1 (no deps) - Create tables
2. Phase 2 AND Phase 3 (parallel, both depend on Phase 1)
3. Phase 4 (after both 2 and 3 complete)

## Integration with tdd-plan

This skill uses `tdd-plan` to generate mini TDD plans for each phase:

1. **Invoke tdd-plan with phase deliverables**
2. **tdd-plan asks clarifying questions** (scoped to phase)
3. **tdd-plan generates phase-specific plan**
4. **ralph-loop executes the plan**
5. **Return control to hld-phase-executor for validation gate**

## State Recovery

If context is compacted or session restarts:

1. Read `.agent/hld-execution-state.md`
2. Identify current phase status
3. Check if phase was in-progress
4. Resume from last known state:
   - If TDD incomplete: Re-invoke ralph-loop
   - If validation incomplete: Re-run validation
   - If waiting on user: Re-prompt for approval

## Failure Handling

### Phase Validation Fails

1. Do NOT proceed to dependent phases
2. Log failure in execution state
3. Generate remediation plan
4. Re-execute TDD cycle
5. Re-attempt validation

### Dependency Phase Failed

1. Block all dependent phases
2. Notify user of blocked phases
3. Wait for blocking phase remediation
4. Re-validate blocker before unblocking

### Circular Dependency Detected

1. Reject HLD parsing
2. Report circular path to user
3. Request HLD correction

## Additional Resources

### Reference Files

- **`references/hld-parsing-patterns.md`** - Common HLD formats and parsing strategies
- **`references/validation-gate-patterns.md`** - Validation gate configurations

### Example Files

- **`examples/infrastructure-migration.hld.md`** - Example infrastructure HLD
- **`examples/feature-rollout.hld.md`** - Example feature rollout HLD

## Checklist Before Starting

- [ ] HLD document provided and readable
- [ ] Phases have clear deliverables
- [ ] Dependencies are explicit
- [ ] Validation criteria defined for each phase
- [ ] Deployment commands provided (if applicable)
- [ ] No circular dependencies in phase graph
