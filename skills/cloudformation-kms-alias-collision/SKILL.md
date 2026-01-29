---
name: cloudformation-kms-alias-collision
description: |
  Fix CloudFormation deployment failures caused by KMS alias collisions. Use when:
  (1) CDK deploy fails with "AWS::EarlyValidation::ResourceExistenceCheck" error,
  (2) Multiple CDK stacks create KMS keys with similar aliases,
  (3) Deployment fails before changeset execution due to resource existence check.
  Covers diagnosing KMS alias conflicts and resolving them in CDK stacks.
author: Claude Code
version: 1.0.0
date: 2026-01-25
---

# CloudFormation KMS Alias Collision Resolution

## Problem

CloudFormation deployment fails during the Early Validation phase with
`AWS::EarlyValidation::ResourceExistenceCheck` error when a KMS alias already
exists in the account from another stack or previous deployment.

## Context / Trigger Conditions

- CDK deploy fails before changeset execution
- Error message contains `AWS::EarlyValidation::ResourceExistenceCheck`
- Error references a KMS Key or Alias resource
- Multiple stacks define similar KMS keys (e.g., for shared encryption purposes)
- Stack was working but fails after another stack with similar resources was deployed

Example error:
```
❌ Deployment failed: Error: The stack named DataStack failed creation,
it may need to be manually deleted from the AWS console: ROLLBACK_COMPLETE:
Resource with ID [CorrelationTokenKmsKey] failed with reason:
AWS::EarlyValidation::ResourceExistenceCheck
```

## Solution

### Step 1: Identify the Conflicting Alias

List existing KMS aliases to find the conflict:

```bash
aws kms list-aliases --query 'Aliases[?contains(AliasName, `your-alias-pattern`)]'
```

Example:
```bash
aws kms list-aliases --query 'Aliases[?contains(AliasName, `mat-correlation-token`)]'
```

### Step 2: Determine the Source

Check which stack created the existing alias:
- Look at the `TargetKeyId` from the alias listing
- Find the key in CloudFormation stacks using:

```bash
aws cloudformation describe-stack-resources \
  --stack-name YourStackName \
  --query 'StackResources[?ResourceType==`AWS::KMS::Key`]'
```

### Step 3: Resolve the Conflict

**Option A: Use a Unique Alias Name** (Recommended for new resources)

Change the alias name to be unique per stack:

```typescript
// Before: Conflicting alias
key.addAlias('mat-correlation-token');

// After: Stack-specific alias
key.addAlias('mat-dataplane-correlation-token');
```

**Option B: Share the Existing Key** (For truly shared resources)

If the key should be shared, import it instead of creating:

```typescript
const existingKey = kms.Key.fromKeyArn(this, 'SharedKey',
  'arn:aws:kms:us-east-1:123456789:key/abc-123');
```

**Option C: Remove Alias from Conflicting Stack**

If the original stack shouldn't have the alias, remove it there first.

### Step 4: Deploy

After making changes, deploy again:

```bash
cdk deploy DataStack
```

## Verification

- Deployment completes without Early Validation errors
- Both stacks deploy successfully with their respective KMS keys
- List aliases to confirm both exist:

```bash
aws kms list-aliases --query 'Aliases[?starts_with(AliasName, `alias/mat-`)]'
```

## Example

In this real case, two CDK stacks were creating KMS keys:

1. **MCPGatewayStack** (auth-service-construct): Created `alias/mat-correlation-token`
2. **DataStack**: Tried to create the same alias for a shared correlation token key

Resolution was to rename DataStack's alias:

```typescript
// packages/infra/lib/data/data-stack.ts
private createCorrelationTokenKmsKey(): kms.Key {
  const key = new kms.Key(this, 'CorrelationTokenKmsKey', {
    description: 'KMS key for encrypting Correlation Tokens',
    enableKeyRotation: true,
    removalPolicy: RemovalPolicy.RETAIN,
  });

  // Use a different alias to avoid conflict with existing auth-service key
  // Note: Consider migrating to use this shared key in a future iteration
  key.addAlias('mat-dataplane-correlation-token');

  return key;
}
```

## Notes

- **Early Validation**: CloudFormation's Early Validation phase checks for resource
  existence before creating changesets, catching conflicts early
- **Alias Uniqueness**: KMS aliases must be unique within an account (not just a stack)
- **Alias Names**: Aliases are automatically prefixed with `alias/` by AWS
- **Migration Path**: If resources should be shared, plan a migration to consolidate
  onto a single key, then remove the duplicate
- **RemovalPolicy.RETAIN**: Keys with RETAIN policy stay after stack deletion,
  potentially causing future conflicts

## Related Issues

- IAM role/policy name conflicts (similar pattern)
- S3 bucket name conflicts (must be globally unique)
- SSM parameter name conflicts (namespace-based)

## References

- [AWS KMS Key Aliases](https://docs.aws.amazon.com/kms/latest/developerguide/alias-manage.html)
- [CDK KMS Module](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_kms-readme.html)
- [CloudFormation Early Validation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stack-failure-options.html)
