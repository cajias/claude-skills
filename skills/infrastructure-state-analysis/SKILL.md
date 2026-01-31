---
name: infrastructure-state-analysis
description: "Phase 0.5: Infrastructure State Analysis for CDK/CloudFormation work. MANDATORY before TDD RED phase when working with infrastructure code. Prevents architectural errors by analyzing deployed state, cross-stack dependencies, and synth behavior."
argument-hint: "[--stack STACK_NAME] [--region REGION] [--account ACCOUNT_ID]"
---

# Phase 0.5: Infrastructure State Analysis

**MANDATORY CHECKPOINT** for all CDK/CloudFormation infrastructure work. This phase must complete with ALL exit criteria met BEFORE proceeding to the TDD RED phase.

## Why This Phase Exists

This skill was created based on postmortem analysis of a critical infrastructure failure where:

1. SSM parameter lookups were placed at **App level** instead of **Stack level**
2. Cross-stack dependencies weren't analyzed before implementation
3. CDK synth wasn't run to validate the approach
4. The error wasn't discovered until after significant implementation effort

**Root Cause:** Jumping into TDD without understanding current infrastructure state leads to architectural errors that are expensive to fix.

## When This Phase Is Required

**MANDATORY** when the task involves ANY of:
- Creating or modifying CDK stacks
- Changing CloudFormation exports/imports
- Adding or modifying SSM parameter lookups
- Changing cross-stack references
- Modifying VPC, IAM, or security group dependencies
- Migrating from cross-stack exports to SSM parameters
- Adding or removing stack dependencies

**SKIP** when the task is:
- Pure application code (no infrastructure changes)
- Documentation only
- Test-only changes to existing infrastructure tests
- Configuration changes that don't affect stack structure

## Mandatory Questions to Ask

### Category 1: Current State Understanding

Before ANY infrastructure work, you MUST answer these questions:

| Question | How to Answer | Why It Matters |
|----------|---------------|----------------|
| What stacks currently exist in the target account? | `aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE` | Avoid creating duplicate stacks or breaking existing deployments |
| What are the current CloudFormation exports? | `aws cloudformation list-exports` | Identify dependencies before modifying them |
| Which stacks import from the stack I'm modifying? | `aws cloudformation list-imports --export-name <name>` | Breaking exports breaks dependent stacks |
| What SSM parameters already exist in the target path? | `aws ssm get-parameters-by-path --path /foundation/` | Avoid duplicate parameters or incorrect lookups |
| Is there a deployed FoundationStack? | `aws cloudformation describe-stacks --stack-name FoundationStack` | Many stacks depend on foundation resources |

### Category 2: Architecture Understanding

| Question | How to Verify | Failure Mode if Skipped |
|----------|---------------|-------------------------|
| Where should SSM lookups occur? | Read design docs, check CDK best practices | App-level lookups fail at synth time |
| What scope is needed for `valueFromLookup`? | Must be Stack scope, never App scope | "App at '' should be created in the scope of a Stack" error |
| Are there circular dependencies between stacks? | Trace imports/exports in both directions | Deployment fails with circular dependency error |
| Does the design doc match the implementation? | Compare design doc Section 6 with actual code | Architectural drift causes subtle failures |

### Category 3: CDK Context Understanding

| Question | How to Verify | Impact |
|----------|---------------|--------|
| What context values are cached? | Check `cdk.context.json` | Stale context causes incorrect synth output |
| Are there hardcoded account/region values? | Grep for account IDs, region strings | Environment-specific failures |
| What happens if SSM parameters don't exist? | Test with missing parameters | Synth fails or produces invalid templates |

## Commands to Run

### Phase 0.5.1: CloudFormation State Analysis (REQUIRED)

```bash
# Set working directory
cd packages/infra

# 1. List all stacks in target account
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE \
  --query 'StackSummaries[*].[StackName,StackStatus,CreationTime]' \
  --output table

# 2. List all CloudFormation exports
aws cloudformation list-exports \
  --query 'Exports[*].[Name,ExportingStackId,Value]' \
  --output table

# 3. For each export, check what imports it (repeat for each export)
aws cloudformation list-imports --export-name <EXPORT_NAME>

# 4. Check specific stack details
aws cloudformation describe-stacks --stack-name <STACK_NAME> \
  --query 'Stacks[0].[StackName,StackStatus,Outputs]'
```

### Phase 0.5.2: SSM Parameter State Analysis (REQUIRED for SSM work)

```bash
# 1. List all SSM parameters in the foundation path
aws ssm get-parameters-by-path \
  --path "/foundation/" \
  --recursive \
  --query 'Parameters[*].[Name,Type,LastModifiedDate]' \
  --output table

# 2. Check specific parameter existence
aws ssm get-parameter --name "/foundation/identity/oidc-issuer" 2>&1 || echo "Parameter not found"

# 3. Verify parameter values match expectations
aws ssm get-parameter --name "/foundation/network/vpc-id" --query 'Parameter.Value' --output text
```

### Phase 0.5.3: CDK Synth Analysis (REQUIRED)

```bash
# IMPORTANT: Run CDK commands SEQUENTIALLY, not in parallel
# Each synth creates 2-5GB temp folders that can exhaust disk space

# 1. Clean previous synth output
rm -rf cdk.out

# 2. Run basic synth (catches most architectural errors)
npx cdk synth --all 2>&1 | tee /tmp/cdk-synth-output.txt

# 3. Check for specific error patterns
grep -E "(Error|error|FAILED|failed)" /tmp/cdk-synth-output.txt

# 4. If SSM lookups exist, test with context overrides
npx cdk synth --all \
  -c ssm:account=ACCOUNT_ID:parameterName=/foundation/identity/oidc-issuer=https://dummy.example.com \
  2>&1 | tee /tmp/cdk-synth-with-context.txt

# 5. Verify no cross-stack imports in consuming stacks (if migrating to SSM)
grep -l "Fn::ImportValue" cdk.out/*.template.json || echo "No cross-stack imports found"
```

### Phase 0.5.4: CDK Diff Analysis (REQUIRED before deployment)

```bash
# 1. Run diff for all stacks
npx cdk diff --all 2>&1 | tee /tmp/cdk-diff-output.txt

# 2. Check for destructive changes
grep -E "(destroy|replace|will be)" /tmp/cdk-diff-output.txt

# 3. Count resources being modified
grep -c "^\[" /tmp/cdk-diff-output.txt || echo "0 changes"
```

## Exit Criteria Before RED Phase

**ALL of the following MUST be true before proceeding to TDD RED phase:**

### Mandatory Checklist

- [ ] **CFN-1:** CloudFormation stack list retrieved and documented
- [ ] **CFN-2:** All relevant exports identified and their consumers listed
- [ ] **CFN-3:** No unintended breaking changes to exports identified
- [ ] **SSM-1:** SSM parameter existence verified (or confirmed they need creation)
- [ ] **SSM-2:** SSM lookup scope confirmed (Stack, not App)
- [ ] **CDK-1:** `cdk synth --all` succeeds (or fails with EXPECTED error)
- [ ] **CDK-2:** `cdk diff --all` reviewed for destructive changes
- [ ] **CDK-3:** No App-level SSM lookups in the codebase
- [ ] **ARCH-1:** Design document exists and matches proposed implementation
- [ ] **ARCH-2:** Cross-stack dependencies documented in Investigation Tracker

### Blocking Conditions (STOP and resolve first)

If ANY of these are true, you MUST NOT proceed to RED phase:

1. **Synth fails with unexpected error** - Debug and fix first
2. **Breaking changes to exports** without consumer migration plan
3. **SSM lookups at App level** - Must be moved to Stack level
4. **Circular dependencies detected** - Requires architectural redesign
5. **Missing design document** for complex changes
6. **Stale CDK context** causing incorrect lookups

## What Gets Logged to Investigation Tracker

Add the following entries to the Investigation Tracker table:

### Infrastructure State Analysis Entries

```markdown
## Investigation Tracker

| Iteration | Issue | Attempted Fix | Result | Next Action |
|-----------|-------|---------------|--------|-------------|
| 0.5 | Infrastructure state analysis | Ran CFN list-stacks | Found 12 stacks deployed | Document dependencies |
| 0.5 | CloudFormation exports | Ran list-exports | 8 exports, 3 have importers | Create migration plan for exports |
| 0.5 | SSM parameters | Checked /foundation/ path | 15 parameters exist | Verify lookup scope in code |
| 0.5 | CDK synth test | Ran cdk synth --all | FAILED: App scope error | Move lookups to Stack level |
| 0.5 | SSM lookup scope | Audited valueFromLookup calls | Found 3 at App level | Task #12: Fix architecture |
| 0.5 | Cross-stack deps | Grep for Fn::ImportValue | 5 templates have imports | Document which exports they use |
| 0.5 | CDK context | Checked cdk.context.json | Context has stale VPC ID | Clear and re-synth |
```

### Minimum Required Entries

Every infrastructure task MUST log at least:

1. **Stack state analysis result** (what stacks exist)
2. **Export dependency result** (what exports are used)
3. **CDK synth result** (success or failure with reason)
4. **Architecture compliance check** (lookup scope, design doc alignment)

## Integration with TDD Plan

### Updated Iteration Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 0: REQUIREMENTS CLARIFICATION                        │
│  - Parse request, identify ambiguities                      │
│  - Ask clarifying questions                                 │
│  - Explore codebase for context                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 0.5: INFRASTRUCTURE STATE ANALYSIS  ← NEW            │
│  (MANDATORY for infrastructure work)                        │
│                                                             │
│  - Run CloudFormation state commands                        │
│  - Run SSM parameter verification                           │
│  - Run CDK synth/diff                                       │
│  - Check architecture compliance                            │
│  - Log findings to Investigation Tracker                    │
│                                                             │
│  EXIT GATE: All criteria must pass                          │
│  If blocked → STOP, create fix task, do not proceed         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  MASTER GOALS (immutable, derived from clarified spec)      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────── ITERATION N ──────────┐
         │                                 │
         │  PHASE 1: RED - Write Tests     │
         │  PHASE 2: GREEN - Implement     │
         │  PHASE 3: REFACTOR              │
         │  PHASE 4: VALIDATE              │
         │  PHASE 5: COMMIT                │
         │  PHASE 6: EVALUATE              │
         └─────────────────────────────────┘
```

## Quick Reference Card

### Minimum Commands for Infrastructure TDD

```bash
# Phase 0.5 Quick Check (run ALL before RED phase)
aws cloudformation list-exports --output table
aws ssm get-parameters-by-path --path "/foundation/" --recursive --output table
npx cdk synth --all 2>&1 | head -50
grep -r "valueFromLookup" packages/infra/bin/ packages/infra/lib/
```

### Red Flags to Watch For

| Pattern in Output | What It Means | Action |
|-------------------|---------------|--------|
| "should be created in the scope of a Stack" | SSM lookup at App level | Move to Stack constructor |
| "Export with name X not found" | Missing CloudFormation export | Check stack deployment order |
| "Circular dependency" | Stacks reference each other | Redesign with SSM parameters |
| "Parameter not found" | SSM parameter doesn't exist | Deploy FoundationStack first |
| "dummy value" in synth output | CDK using placeholder | Run synth after deployment |

### Common Fix Patterns

**App-level lookup (WRONG):**
```typescript
// infra.ts (App level)
const value = ssm.StringParameter.valueFromLookup(app, '/path');
```

**Stack-level lookup (CORRECT):**
```typescript
// Inside Stack constructor
const value = ssm.StringParameter.valueFromLookup(this, '/path');
```

## Related Skills

- **tdd-plan**: Generates TDD plans; Phase 0.5 runs BEFORE Phase 1 (RED)
- **phased-migration**: Uses worktrees for complex multi-phase migrations
- **cloudformation-cross-stack-export-prison**: Fix export dependency issues
- **cdk-temp-folder-disk-bloat**: Handle disk exhaustion from CDK synth

---

**This phase is NOT optional for infrastructure work. Skipping it leads to architectural errors that are expensive to fix.**
