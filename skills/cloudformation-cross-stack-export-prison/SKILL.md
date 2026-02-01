---
name: cloudformation-cross-stack-export-prison
description: |
  Fix CloudFormation deployment failures caused by cross-stack export dependencies.
  Use when: (1) "Cannot delete export X as it is in use by Stack Y" error appears,
  (2) CDK cross-stack references block updates to producing stacks,
  (3) Fn::ImportValue creates circular deployment dependencies,
  (4) In-place migration of shared resources fails due to export locks.
  Covers CDK auto-generated exports, SSM Parameter alternatives, and stack prefix isolation.
author: Claude Code
version: 1.0.0
date: 2026-01-27
tags: [aws, cdk, cloudformation, infrastructure, deployment]
---

# CloudFormation Cross-Stack Export Dependency Prison

## Problem

CloudFormation cross-stack exports create a **deployment dependency prison**. Once Stack B
imports a value from Stack A using `Fn::ImportValue`, you cannot modify or delete that export
in Stack A until Stack B is updated to stop using it. But updating Stack B often requires
Stack A's export to still exist. This circular dependency blocks in-place migrations.

**Common error message:**
```
Cannot delete export FoundationStack:ExportsOutputFnGetAtt...
as it is in use by AuthPortalStack, ComputeStack and MCPGatewayStack
```

## Context / Trigger Conditions

This skill applies when:

1. **CDK deployment fails** with "Cannot delete export X as it is in use by Y"
2. **Resource reconstruction** is triggered (e.g., Cognito UserPool with changed attributes)
3. **Cross-stack references** exist via `Fn::ImportValue` or CDK property references
4. **CDK auto-generated exports** (like `ExportsOutputFnGetAtt...`) are being modified
5. **Multiple stacks import** from a single producing stack

### How CDK Creates Hidden Exports

CDK automatically creates CloudFormation exports when you reference a property from
another stack:

```typescript
// In FoundationStack
this.userPool = new cognito.UserPool(this, 'UserPool', { ... });

// In AuthPortalStack - this creates an automatic export!
new SomeConstruct(this, 'Auth', {
  oidcIssuer: foundationStack.userPool.userPoolProviderUrl  // <-- Creates export
});
```

This generates an export like:
```yaml
Exports:
  FoundationStack:ExportsOutputFnGetAttUserPoolProviderURLD334AC9D:
    Value: !GetAtt UserPool.ProviderURL
```

## Why In-Place Migration Fails

```
┌─────────────────────────────────────────────────────────────┐
│ Stack A has Export X                                        │
│ Stack B, C, D import X via Fn::ImportValue                  │
│                                                             │
│ You want to: Modify resource that produces X                │
│                                                             │
│ CloudFormation says:                                        │
│ "Cannot delete/modify export X - B, C, D are using it"      │
│                                                             │
│ You think: "I'll update B, C, D to use SSM instead"         │
│                                                             │
│ CloudFormation says:                                        │
│ "Cannot update B, C, D - they need export X to exist"       │
│                                                             │
│ DEADLOCK: You cannot update anything.                       │
└─────────────────────────────────────────────────────────────┘
```

## Solutions

### Solution 1: Stack Prefix for Isolated Deployment (Recommended for Testing)

Deploy entirely new stacks with a prefix to avoid conflicts:

```bash
STACK_PREFIX="feature-" npm run deploy
```

In CDK:
```typescript
const stackPrefix = process.env.STACK_PREFIX || '';

const foundationStack = new FoundationStack(app, `${stackPrefix}FoundationStack`, {
  // All resource names must also use the prefix
  appConfigApplicationName: stackPrefix ? `${stackPrefix}Platform` : 'Platform',
  ssmParameterPrefix: stackPrefix ? `/${stackPrefix}foundation` : '/foundation',
  ...
});
```

**Gotchas with prefixes:**
- AppConfig application names must include prefix
- SSM parameter paths must include prefix
- KMS key aliases must include prefix
- Any globally-named resource needs prefix handling

### Solution 2: Use SSM Parameters Instead of Exports (Prevention)

Avoid the problem by never using CloudFormation exports:

```typescript
// In FoundationStack - write to SSM
new ssm.StringParameter(this, 'OidcIssuerParam', {
  parameterName: '/foundation/oidc-issuer-url',
  stringValue: this.userPool.userPoolProviderUrl,
});

// In consuming stacks - read from SSM
const oidcIssuer = ssm.StringParameter.valueForStringParameter(
  this,  // Must be stack scope, NOT app scope!
  '/foundation/oidc-issuer-url'
);
```

**Critical:** SSM lookups must happen inside stack constructors, not at app level:
```typescript
// WRONG - will fail with "App at '' should be created in scope of a Stack"
const oidcIssuer = ssm.StringParameter.valueForStringParameter(app, '/foundation/oidc-issuer-url');

// CORRECT - inside stack constructor
class MyStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps) {
    super(scope, id, props);
    const oidcIssuer = ssm.StringParameter.valueForStringParameter(this, '/foundation/oidc-issuer-url');
  }
}
```

### Solution 3: Manual Stack Deletion and Recreation

When all else fails:
1. Delete consuming stacks (B, C, D) from CloudFormation console
2. Update producing stack (A)
3. Redeploy consuming stacks

**Warning:** This causes downtime and data loss if stacks have stateful resources.

### Solution 4: Direct Property References (CDK Best Practice)

Instead of letting CDK create exports, pass values directly through stack props:

```typescript
// Define what FoundationStack exposes
interface FoundationStackOutputs {
  readonly oidcIssuerUrl: string;
  readonly userPoolId: string;
}

// In infra.ts - pass props explicitly
const authStack = new AuthStack(app, 'AuthStack', {
  oidcIssuerUrl: foundationStack.oidcIssuerUrl,  // Direct reference, no export
  ...
});
```

This still creates exports, but gives you control over which properties are shared.

## Verification

After applying a solution:

1. Run `cdk diff` to see what changes will be made
2. Check for export modifications in the diff output
3. Deploy with `--require-approval never` only after verifying diff is safe

## Prevention Checklist

Before making infrastructure changes:

- [ ] Check if the change affects resources that have cross-stack references
- [ ] Run `aws cloudformation list-exports` to see what exports exist
- [ ] Run `aws cloudformation list-imports --export-name <name>` to see what imports an export
- [ ] Compare `.env` files between branches for configuration drift
- [ ] Consider using stack prefix for risky changes

## Notes

- CDK generates export names automatically based on construct tree paths
- Export names include hashes that change when construct IDs change
- `cdk diff` shows export changes but doesn't always indicate the cascade effect
- AWS CloudFormation has no native "migrate export" feature

## Related Patterns

- **SSM Parameter Store**: Alternative to exports for sharing values
- **Secrets Manager**: For sensitive cross-stack values
- **CloudFormation StackSets**: For multi-account deployments
- **CDK Context**: For synthesis-time value sharing (not runtime)

## References

- [AWS CloudFormation Exports Documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-stack-exports.html)
- [CDK Cross-Stack References](https://docs.aws.amazon.com/cdk/v2/guide/resources.html#resources_across_stacks)
- [SSM Parameter Store with CDK](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ssm-readme.html)
