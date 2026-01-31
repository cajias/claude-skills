---
name: infrastructure-gap-analysis
description: |
  Extended gap analysis template for infrastructure/CDK work with categories E-H.
  Use when: (1) Analyzing CDK/CloudFormation implementation completeness,
  (2) After each TDD iteration on infrastructure code,
  (3) Before declaring infrastructure work "complete".
  Covers: Deployment Validation (E), Runtime Behavior (F), Cross-Component Integration (G),
  Infrastructure Validation (H).
author: Claude Code
version: 1.0.0
date: 2026-01-27
tags: [aws, cdk, cloudformation, infrastructure, gap-analysis, tdd]
---

# Extended Gap Analysis Template: Infrastructure Work

## Overview

This template extends the standard gap analysis categories to include validation dimensions that catch architectural and runtime issues **before deployment**.

### Original Categories (A-D)
- **Category A**: Critical Gaps (Blocking Deployment)
- **Category B**: Implementation Gaps (Functionality Missing)
- **Category C**: Quality/Security Gaps
- **Category D**: Test Coverage Gaps

### Extended Categories (E-H)
- **Category E**: Deployment Validation
- **Category F**: Runtime Behavior
- **Category G**: Cross-Component Integration
- **Category H**: Infrastructure Validation

---

## CATEGORY E: Deployment Validation

### What Questions It Answers

1. **Can the infrastructure actually be deployed?**
   - Does `cdk synth` complete successfully?
   - Does CloudFormation template generation succeed?
   - Are all required parameters/context values available?

2. **Is the deployment order correct?**
   - Are stack dependencies properly declared?
   - Will stacks deploy in the right sequence?
   - Are there circular dependencies?

3. **Are environment-specific configurations valid?**
   - Do dev/staging/prod configurations exist and differ appropriately?
   - Are account IDs and regions correctly specified?
   - Are environment variables set for synthesis?

4. **Will the deployment succeed on first attempt?**
   - Are all external dependencies (SSM parameters, secrets, VPCs) available?
   - Are bootstrap resources in place?
   - Are IAM permissions sufficient for deployment?

### Verification Commands

```bash
# 1. Basic synthesis (catches scope/context errors)
cd packages/infra
npx cdk synth --all 2>&1 | tee /tmp/cdk-synth.log

# 2. Synthesis with specific context (tests parameter resolution)
npx cdk synth --all \
  -c dataPlane=fargate \
  -c environment=dev \
  2>&1 | tee /tmp/cdk-synth-context.log

# 3. Check template output exists
ls -la cdk.out/*.template.json

# 4. Validate CloudFormation templates
for template in cdk.out/*.template.json; do
  aws cloudformation validate-template \
    --template-body file://$template \
    --region us-east-1 || echo "FAILED: $template"
done

# 5. Check for synthesis-time lookups (potential blockers)
grep -r "valueFromLookup\|fromLookup" packages/infra/lib/ packages/infra/bin/

# 6. Verify stack dependencies
npx cdk list --all --long 2>&1 | grep -E "depends|stack"

# 7. Diff against deployed stacks (if applicable)
npx cdk diff --all 2>&1 | tee /tmp/cdk-diff.log
```

### What "Complete" Means

| Criterion | Pass Condition |
|-----------|----------------|
| Synthesis | `cdk synth --all` exits with code 0 |
| Templates | All expected `.template.json` files generated in `cdk.out/` |
| Validation | All CloudFormation templates pass `validate-template` |
| Context | All context parameters have defaults or documented requirements |
| Lookups | All synthesis-time lookups are in Stack scope (not App scope) |
| Dependencies | No circular dependencies; clear deployment order |
| Diff | Changes match expected modifications (no unexpected drift) |

### Warning Signs

| Warning Sign | What It Indicates |
|--------------|-------------------|
| `App at '' should be created in the scope of a Stack` | Synthesis-time lookup called at App level instead of Stack level |
| `Cannot read property 'X' of undefined` | Missing required prop or uninitialized dependency |
| `Circular dependency between stacks` | Stack A depends on B, and B depends on A |
| `Export X cannot be deleted` | CloudFormation export is still in use by another stack |
| `SSM parameter not found` | Parameter doesn't exist or lookup is at wrong scope |
| `No template generated for X` | Stack was skipped due to condition or error |
| `Context key required but not provided` | Missing `-c` flag or `cdk.context.json` entry |

### Gap Documentation Template

```markdown
| ID | Gap | Current State | Expected State | Severity |
|----|-----|---------------|----------------|----------|
| E-1 | Synthesis fails with scope error | SSM lookups in App scope | SSM lookups in Stack constructors | **CRITICAL** |
| E-2 | Missing context parameters | No default for dataPlane | Default to 'eks' or require explicit | HIGH |
| E-3 | Template validation fails | Invalid intrinsic function | Valid CloudFormation | HIGH |
```

---

## CATEGORY F: Runtime Behavior

### What Questions It Answers

1. **Will the deployed resources function correctly?**
   - Do Lambda functions have correct environment variables?
   - Are container images using correct entrypoints?
   - Are timeout and memory settings appropriate?

2. **Will inter-service communication work?**
   - Are security groups configured for required traffic?
   - Are IAM roles scoped correctly for runtime operations?
   - Are VPC endpoints available for AWS services?

3. **Are health checks properly configured?**
   - Do ALB health checks match application health endpoints?
   - Are ECS task health checks configured?
   - Are Kubernetes readiness/liveness probes correct?

4. **Will the system behave correctly under load?**
   - Are auto-scaling policies configured?
   - Are throttling limits appropriate?
   - Are connection pools and timeouts set correctly?

### Verification Commands

```bash
# 1. Extract Lambda environment variables from template
cat cdk.out/ComputeStack.template.json | \
  jq '.Resources | to_entries[] | select(.value.Type == "AWS::Lambda::Function") |
      {name: .key, env: .value.Properties.Environment.Variables}'

# 2. Verify security group ingress/egress rules
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Type == "AWS::EC2::SecurityGroup") |
      {name: .key, ingress: .value.Properties.SecurityGroupIngress, egress: .value.Properties.SecurityGroupEgress}'

# 3. Check IAM role policies for overly broad permissions
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Type == "AWS::IAM::Policy") |
      .value.Properties.PolicyDocument.Statement[] | select(.Resource == "*" or .Action == "*")'

# 4. Verify health check configurations
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Type == "AWS::ElasticLoadBalancingV2::TargetGroup") |
      {name: .key, healthCheck: .value.Properties.HealthCheckPath}'

# 5. Check timeout and memory settings
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Type == "AWS::Lambda::Function") |
      {name: .key, timeout: .value.Properties.Timeout, memory: .value.Properties.MemorySize}'

# 6. Verify container definitions (Fargate)
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Type == "AWS::ECS::TaskDefinition") |
      .value.Properties.ContainerDefinitions[] | {name: .Name, image: .Image, port: .PortMappings}'
```

### What "Complete" Means

| Criterion | Pass Condition |
|-----------|----------------|
| Environment Variables | All required env vars present with valid values (not placeholders) |
| Security Groups | Required ports open; no overly permissive rules (0.0.0.0/0 ingress) |
| IAM Policies | No `*` in Resource unless justified; least privilege verified |
| Health Checks | Path matches actual endpoint; interval/timeout appropriate |
| Timeouts | Lambda timeouts < API Gateway timeout; reasonable for workload |
| Container Images | Real ECR images, not placeholder (amazonlinux) |

### Warning Signs

| Warning Sign | What It Indicates |
|--------------|-------------------|
| `public.ecr.aws/amazonlinux` in task definition | Placeholder image, not actual application |
| `resources: ['*']` in IAM policy | Overly permissive IAM |
| `healthCheckPath: '/'` without verification | May not match actual health endpoint |
| Security group with `0.0.0.0/0` ingress | Publicly accessible without explicit intent |
| Lambda timeout > 15 minutes | Possible misunderstanding of Lambda limits |
| Missing environment variable | Runtime failures due to undefined config |
| `undefined` or `null` in template values | Props not properly resolved at synth time |

### Gap Documentation Template

```markdown
| ID | Gap | Current State | Expected State | Severity |
|----|-----|---------------|----------------|----------|
| F-1 | Placeholder container images | amazonlinux:2023 | service-mcp-proxy ECR image | **HIGH** |
| F-2 | Overly broad IAM permissions | execute-api:* | Scoped to specific API Gateway | MEDIUM |
| F-3 | Health check mismatch | ALB checks /health, app serves /healthz | Both use same path | HIGH |
```

---

## CATEGORY G: Cross-Component Integration

### What Questions It Answers

1. **Do components share data correctly?**
   - Are DynamoDB table names/ARNs passed correctly between stacks?
   - Are KMS key permissions granted to consumers?
   - Are S3 bucket policies allowing required cross-account access?

2. **Are API contracts honored?**
   - Do producer APIs match consumer expectations?
   - Are shared interfaces (TypeScript) consistent?
   - Are SSM parameter paths correct and documented?

3. **Is the data flow complete?**
   - Can Stack B read what Stack A writes?
   - Are EventBridge rules routing to correct targets?
   - Are SQS/SNS subscriptions properly configured?

4. **Are cross-stack references minimized?**
   - How many `Fn::ImportValue` references exist?
   - Are SSM parameters used for decoupling instead?
   - Can stacks be deployed independently?

### Verification Commands

```bash
# 1. Count cross-stack references (should be minimized)
for template in cdk.out/*.template.json; do
  echo "=== $template ==="
  grep -c "Fn::ImportValue" $template || echo "0"
done

# 2. List all SSM parameters written
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Type == "AWS::SSM::Parameter") |
      {name: .key, path: .value.Properties.Name, type: .value.Properties.Type}'

# 3. Verify SSM parameter paths match consumers
# In Stack A (writes):
grep -r "putParameter\|StringParameter" packages/infra/lib/ | grep -E "'/[^']+'"
# In Stack B (reads):
grep -r "valueFromLookup\|fromString" packages/infra/lib/ | grep -E "'/[^']+'"

# 4. Check EventBridge rules and targets
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Type == "AWS::Events::Rule") |
      {name: .key, pattern: .value.Properties.EventPattern, targets: .value.Properties.Targets}'

# 5. Verify interface consistency
# Check that SharedResources interface matches actual usage
grep -r "SharedResources" packages/infra/lib/ --include="*.ts" | head -20

# 6. List stack outputs/exports
for template in cdk.out/*.template.json; do
  echo "=== $template ==="
  cat $template | jq '.Outputs // empty'
done
```

### What "Complete" Means

| Criterion | Pass Condition |
|-----------|----------------|
| Cross-Stack Refs | `Fn::ImportValue` count < 5 per stack (prefer SSM) |
| SSM Parameters | All written parameters have matching consumers |
| Interface Contracts | TypeScript interfaces match runtime usage |
| Event Routing | EventBridge rules have valid targets |
| Stack Independence | Each stack can be synthesized independently |
| Data Flow | Write paths match read paths exactly |

### Warning Signs

| Warning Sign | What It Indicates |
|--------------|-------------------|
| `Export X is already used by Y` | Tight coupling; can't update without cascade |
| Mismatched SSM paths (`/foundation/vpc-id` vs `/foundation/network/vpc-id`) | Consumer won't find producer's value |
| Missing `grantRead()` calls | Consumer lacks permission to access producer's data |
| Circular stack dependencies | Architecture needs redesign |
| Interface field missing | Runtime will fail on undefined property access |
| EventBridge target returns `null` | Lambda ARN not resolved correctly |

### Gap Documentation Template

```markdown
| ID | Gap | Current State | Producer | Consumer | Severity |
|----|-----|---------------|----------|----------|----------|
| G-1 | SSM path mismatch | Writer uses /foundation/vpc-id | FoundationStack | ComputeStack reads /network/vpc-id | **CRITICAL** |
| G-2 | Cross-stack export creates coupling | Uses Fn::ImportValue | DataStack | ComputeStack | MEDIUM |
| G-3 | Missing interface field | IDataPlane missing targetGroup | FargateDataPlane | DataPlaneRouter | HIGH |
```

---

## CATEGORY H: Infrastructure Validation

### What Questions It Answers

1. **Does the infrastructure match design specifications?**
   - Are the correct AWS resource types being created?
   - Do resource counts match expected numbers?
   - Are naming conventions followed?

2. **Are compliance requirements met?**
   - Is encryption enabled where required (KMS, at-rest, in-transit)?
   - Are logging and monitoring configured?
   - Are backup/retention policies set?

3. **Are operational concerns addressed?**
   - Are CloudWatch alarms configured?
   - Are log groups with appropriate retention?
   - Are tags applied for cost allocation?

4. **Is the infrastructure cost-appropriate?**
   - Are instance sizes reasonable for workload?
   - Are reserved capacity or savings plans applicable?
   - Are unused resources identified?

### Verification Commands

```bash
# 1. Count resources by type
for template in cdk.out/*.template.json; do
  echo "=== $template ==="
  cat $template | jq '[.Resources | to_entries[] | .value.Type] | group_by(.) | map({type: .[0], count: length})'
done

# 2. Verify encryption is enabled
# KMS usage
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Properties.KmsKeyId or .value.Properties.KMSMasterKeyId) |
      {name: .key, type: .value.Type}'

# DynamoDB encryption
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Type == "AWS::DynamoDB::Table") |
      {name: .key, encryption: .value.Properties.SSESpecification}'

# S3 encryption
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Type == "AWS::S3::Bucket") |
      {name: .key, encryption: .value.Properties.BucketEncryption}'

# 3. Check CloudWatch log groups
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Type == "AWS::Logs::LogGroup") |
      {name: .key, retention: .value.Properties.RetentionInDays}'

# 4. Verify tagging
cat cdk.out/*.template.json | \
  jq '.Resources | to_entries[] | select(.value.Properties.Tags) |
      {name: .key, type: .value.Type, tags: .value.Properties.Tags}'

# 5. Check for removal policies (important for stateful resources)
grep -r "RemovalPolicy\|removalPolicy" packages/infra/lib/ --include="*.ts"

# 6. Verify CDK Nag compliance (if configured)
npx cdk synth --all 2>&1 | grep -E "(AwsSolutions|HIPAA|NIST)" || echo "No CDK Nag findings"

# 7. Count expected vs actual resources
cat cdk.out/*.template.json | jq '[.Resources | keys | length] | add'
```

### What "Complete" Means

| Criterion | Pass Condition |
|-----------|----------------|
| Resource Types | All expected AWS resource types present in templates |
| Encryption | All data-at-rest resources have encryption enabled |
| Logging | Log groups exist for all compute resources |
| Retention | Log retention and backup policies configured |
| Tags | Required tags (Environment, Project, Owner) present |
| CDK Nag | No ERROR level findings (warnings acceptable with justification) |
| Removal Policy | Stateful resources have RETAIN or SNAPSHOT policy |

### Warning Signs

| Warning Sign | What It Indicates |
|--------------|-------------------|
| `SSESpecification: null` on DynamoDB | Table data not encrypted |
| `RetentionInDays: undefined` on LogGroup | Logs retained indefinitely (cost) |
| No CloudWatch alarms in template | No automated alerting |
| `RemovalPolicy.DESTROY` on production database | Data loss risk on stack deletion |
| Missing required tags | Cost allocation and compliance issues |
| CDK Nag `Error` suppressed without justification | Security risk ignored |
| Lambda without X-Ray tracing | Observability gap |

### Gap Documentation Template

```markdown
| ID | Gap | Resource | Current State | Expected State | Severity |
|----|-----|----------|---------------|----------------|----------|
| H-1 | DynamoDB not encrypted | AuthContextTable | SSESpecification: null | KMS encryption enabled | **HIGH** |
| H-2 | Log retention not set | MCPProxyLogGroup | Indefinite | 30 days | MEDIUM |
| H-3 | Missing alarms | FargateService | No alarms | CPU/Memory alarms | MEDIUM |
| H-4 | No WAF on ALB | DataPlaneALB | No WebACL | WAF with rate limiting | HIGH |
```

---

## Using the Extended Template

### Pre-Implementation Checklist

Before marking any implementation phase as "complete", verify:

- [ ] **Category A-D** (Original): All critical/implementation/quality/test gaps addressed
- [ ] **Category E** (Deployment): `cdk synth --all` succeeds; templates valid
- [ ] **Category F** (Runtime): Environment vars, health checks, IAM verified
- [ ] **Category G** (Integration): SSM paths match; no tight coupling
- [ ] **Category H** (Infrastructure): Encryption, logging, tags, compliance

### Automated Validation Script

Save as `scripts/gap-analysis-validation.sh`:

```bash
#!/bin/bash
set -e

echo "=== CATEGORY E: Deployment Validation ==="
cd packages/infra
npx cdk synth --all 2>&1 || { echo "FAIL: Synthesis failed"; exit 1; }
echo "PASS: Synthesis successful"

echo ""
echo "=== CATEGORY F: Runtime Behavior ==="
# Check for placeholder images
if grep -q "public.ecr.aws/amazonlinux" cdk.out/*.template.json; then
  echo "WARN: Placeholder container images detected"
fi

# Check for overly broad IAM
if cat cdk.out/*.template.json | jq -e '.Resources[].Properties.PolicyDocument.Statement[] | select(.Resource == "*")' > /dev/null 2>&1; then
  echo "WARN: Overly broad IAM permissions detected"
fi

echo ""
echo "=== CATEGORY G: Cross-Component Integration ==="
# Count cross-stack references
IMPORT_COUNT=$(grep -c "Fn::ImportValue" cdk.out/*.template.json 2>/dev/null || echo "0")
echo "Cross-stack imports: $IMPORT_COUNT"
if [ "$IMPORT_COUNT" -gt 10 ]; then
  echo "WARN: High number of cross-stack imports"
fi

echo ""
echo "=== CATEGORY H: Infrastructure Validation ==="
# Check encryption
UNENCRYPTED_TABLES=$(cat cdk.out/*.template.json | jq '[.Resources | to_entries[] | select(.value.Type == "AWS::DynamoDB::Table") | select(.value.Properties.SSESpecification == null)] | length')
if [ "$UNENCRYPTED_TABLES" -gt 0 ]; then
  echo "WARN: $UNENCRYPTED_TABLES unencrypted DynamoDB tables"
fi

echo ""
echo "=== Validation Complete ==="
```

### Integration with Gap Analysis Iterations

When creating `gap-analysis-iteration-N.md`:

```markdown
# Gap Analysis: HLD vs Implementation - Iteration N

## Executive Summary
...

## Gap Categories

### CATEGORY A: Critical Gaps
...

### CATEGORY B: Implementation Gaps
...

### CATEGORY C: Quality/Security Gaps
...

### CATEGORY D: Test Coverage Gaps
...

### CATEGORY E: Deployment Validation Gaps
| ID | Gap | Current State | Impact | Priority |
|----|-----|---------------|--------|----------|
| E-1 | ... | ... | ... | ... |

### CATEGORY F: Runtime Behavior Gaps
| ID | Gap | Current State | Impact | Priority |
|----|-----|---------------|--------|----------|
| F-1 | ... | ... | ... | ... |

### CATEGORY G: Cross-Component Integration Gaps
| ID | Gap | Current State | Impact | Priority |
|----|-----|---------------|--------|----------|
| G-1 | ... | ... | ... | ... |

### CATEGORY H: Infrastructure Validation Gaps
| ID | Gap | Current State | Impact | Priority |
|----|-----|---------------|--------|----------|
| H-1 | ... | ... | ... | ... |
```

---

## Lessons Learned: What the Extended Categories Would Have Caught

### Case Study: SSM Parameter Scope Error (TASK-6)

**What Happened:**
- SSM parameter lookups were placed in `bin/infra.ts` (App scope)
- CDK requires lookups in Stack constructors (Stack scope)
- `cdk synth` failed with "App at '' should be created in the scope of a Stack"

**Which Category Would Have Caught It:**

| Category | Would Have Caught? | How |
|----------|-------------------|-----|
| A (Critical) | No | Focused on functionality, not synthesis |
| B (Implementation) | Maybe | If explicitly checking CDK patterns |
| C (Quality) | No | Focused on security/code quality |
| D (Test Coverage) | No | Tests mock synthesis |
| **E (Deployment)** | **YES** | Running `cdk synth --all` immediately exposes this |
| F (Runtime) | No | Synthesis must succeed first |
| G (Integration) | Partial | SSM path matching, but not scope |
| H (Infrastructure) | No | Template validation, not synthesis |

**Conclusion:** Adding Category E (Deployment Validation) as a mandatory checkpoint would have caught this issue immediately after implementation, saving significant debugging time.

---

## Summary

The extended gap analysis categories ensure comprehensive validation across:

| Category | Focus | Primary Question |
|----------|-------|------------------|
| E | Deployment | Can we synthesize and deploy? |
| F | Runtime | Will it work when deployed? |
| G | Integration | Do components communicate correctly? |
| H | Infrastructure | Does it meet design and compliance requirements? |

**Key Principle:** Run Category E validation (`cdk synth --all`) after EVERY infrastructure change, before any other validation. If synthesis fails, nothing else matters.
