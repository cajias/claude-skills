---
name: cdk-test-optimization
description: |
  Fix extremely slow AWS CDK tests (30+ minutes for a single test file). Use when:
  (1) CDK tests take 30+ minutes to run,
  (2) Each test creates `new cdk.App()` in beforeEach,
  (3) Tests trigger Docker image builds repeatedly,
  (4) Jest shows tests running but no progress for minutes,
  (5) Disk fills up during test runs (see also: cdk-temp-folder-disk-bloat).
  Solution: Use beforeAll to share CDK synthesis across tests.
author: Claude Code
version: 1.0.0
date: 2026-01-26
---

# CDK Test Optimization: beforeAll vs beforeEach

## Problem

CDK unit tests using `beforeEach` to create a new `cdk.App()` for each test are
extremely slow (30+ minutes for ~36 tests). Each test triggers:

1. Fresh CDK App instantiation
2. Full construct tree creation
3. Docker image bundling for Lambda/Fargate assets
4. Complete CDK synthesis to CloudFormation

This multiplies test time by the number of tests.

## Context / Trigger Conditions

Symptoms:

- Single test file takes 30+ minutes
- Jest shows tests running but progress stalls for minutes between tests
- Disk usage spikes during tests (see: cdk-temp-folder-disk-bloat skill)
- `ps aux` shows multiple esbuild/docker processes per test

Pattern to look for in test files:

```typescript
beforeEach(() => {
  app = new cdk.App();  // BAD: Creates new app for EACH test
  stack = new cdk.Stack(app, 'TestStack', {...});
  // Creates constructs...
  template = Template.fromStack(stack);  // Triggers synthesis
});

it('test 1', () => { /* assertions */ });
it('test 2', () => { /* assertions */ });  // Repeats all setup!
```

## Solution

### Step 1: Identify Tests That Share Configuration

Group tests by the configuration they need. Most assertion-only tests can share
a single synthesized template.

### Step 2: Convert beforeEach to beforeAll

```typescript
// BEFORE (slow - 36 builds)
describe('MyConstruct', () => {
  beforeEach(() => {
    app = new cdk.App();
    stack = new cdk.Stack(app, 'TestStack', {...});
    new MyConstruct(stack, 'Test', {...});
    template = Template.fromStack(stack);
  });

  it('test 1', () => { template.hasResource(...) });
  it('test 2', () => { template.hasResource(...) });
});

// AFTER (fast - 1 build)
describe('MyConstruct', () => {
  let template: Template;

  beforeAll(() => {  // Runs ONCE
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'TestStack', {...});
    new MyConstruct(stack, 'Test', {...});
    template = Template.fromStack(stack);
  });

  it('test 1', () => { template.hasResource(...) });
  it('test 2', () => { template.hasResource(...) });
});
```

### Step 3: Separate Tests Needing Different Configs

If some tests need different configuration, use nested describe blocks:

```typescript
describe('MyConstruct', () => {
  describe('with default config', () => {
    let template: Template;

    beforeAll(() => {
      // Setup for default config - runs once
    });

    it('test 1', () => {...});
    it('test 2', () => {...});
  });

  describe('with custom certificate', () => {
    let template: Template;

    beforeAll(() => {
      // Setup with certificate - runs once
    });

    it('test 3', () => {...});
  });
});
```

### Step 4: Consider Removing CDK Unit Tests Entirely

For maximum speed, consider:

1. **Keep only lightweight tests**: Interface tests, pure logic tests
2. **Remove CDK synthesis tests**: Template assertions, resource counting
3. **Verify via integration tests**: Real deployments catch real issues

This is appropriate when:

- Integration tests exist and cover the constructs
- CDK synth tests are mostly "does it create an ECS cluster" type assertions
- Test speed is critical (TDD workflows, CI pipelines)

## Verification

After refactoring:

- Test file should complete in 2-5 minutes instead of 30+
- Only one set of Docker/esbuild bundling messages per describe block
- Disk usage during tests should be much lower

## Example

Real-world result from refactoring `fargate-data-plane.test.ts`:

| Metric     | Before      | After      |
| ---------- | ----------- | ---------- |
| Time       | 30+ minutes | 4 minutes  |
| CDK synths | 36          | 2          |
| Disk usage | 20+ GB temp | ~2 GB temp |

The test file had 36 tests, each doing `beforeEach(() => new cdk.App())`.
Refactored to 2 `beforeAll` blocks (default config + custom certificate config).

## Notes

- **State isolation**: Tests sharing `beforeAll` must not mutate shared state.
  Template assertions are read-only, so this is safe for most CDK tests.
- **Error isolation**: If `beforeAll` fails, all tests in that describe block fail.
  This is usually desirable for CDK tests (if synthesis fails, assertions are meaningless).
- **Nested describes**: Use nested describe blocks for different configurations
  rather than conditional logic in beforeAll.
- **Alternative**: For projects with many configurations to test, consider
  snapshot testing or removing CDK unit tests entirely in favor of integration tests.

## See Also

- **cdk-temp-folder-disk-bloat**: Companion skill for when CDK tests fill up disk
- AWS CDK Testing: <https://docs.aws.amazon.com/cdk/v2/guide/testing.html>

## References

- Jest beforeAll vs beforeEach: <https://jestjs.io/docs/setup-teardown>
- CDK assertions library: <https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.assertions-readme.html>
