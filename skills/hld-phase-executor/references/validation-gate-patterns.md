# Validation Gate Patterns

Configuration patterns for phase validation gates.

## Standard Validation Gate

Every phase includes these checks by default:

```markdown
### Default Validation

- [ ] Unit tests pass: `npm test`
- [ ] Build succeeds: `npm run build`
- [ ] Lint passes: `npm run lint`
- [ ] TypeScript compiles: `npx tsc --noEmit`
```

## Infrastructure Validation Gates

For CDK/CloudFormation phases:

### CDK Synth Gate

```markdown
### Validation: CDK Synth

- [ ] CDK synth succeeds: `npm run cdk synth`
- [ ] No CDK Nag errors: `npm run cdk:nag`
- [ ] Changeset is expected: Manual review
```

### CDK Deploy Gate

```markdown
### Validation: CDK Deploy

- [ ] Deploy to dev: `npm run cdk deploy -- --require-approval never`
- [ ] Stack outputs captured
- [ ] No rollback occurred
- [ ] Post-deploy health check: `npm run healthcheck:dev`
```

### CDK Diff Gate

```markdown
### Validation: CDK Diff

- [ ] CDK diff shows expected changes: `npm run cdk diff`
- [ ] No unexpected resource replacements
- [ ] No security group modifications (without approval)
```

## Database Validation Gates

For database migration phases:

### Schema Validation

```markdown
### Validation: Schema

- [ ] Schema migration runs: `npm run db:migrate`
- [ ] Rollback works: `npm run db:rollback && npm run db:migrate`
- [ ] Schema matches expected: `npm run db:schema:verify`
```

### Data Integrity Gate

```markdown
### Validation: Data Integrity

- [ ] Row counts match: `npm run db:verify:counts`
- [ ] Sample data validates: `npm run db:verify:sample`
- [ ] Foreign key constraints pass: `npm run db:verify:constraints`
```

### Performance Gate

```markdown
### Validation: Performance

- [ ] Query performance: `npm run db:benchmark`
- [ ] Index utilization: `npm run db:analyze:indexes`
- [ ] No full table scans on critical paths
```

## API Validation Gates

For API/service phases:

### Contract Validation

```markdown
### Validation: API Contract

- [ ] OpenAPI spec validates: `npm run api:validate`
- [ ] Breaking changes documented: Manual review
- [ ] Versioning correct: `npm run api:version:check`
```

### Integration Gate

```markdown
### Validation: Integration

- [ ] Integration tests pass: `npm run test:integration`
- [ ] Contract tests pass: `npm run test:contract`
- [ ] Smoke tests pass: `npm run test:smoke`
```

### Load Testing Gate

```markdown
### Validation: Load

- [ ] Load test passes: `npm run test:load`
- [ ] P99 latency < 200ms
- [ ] Error rate < 0.1%
- [ ] No memory leaks detected
```

## Security Validation Gates

### Code Security Gate

```markdown
### Validation: Security

- [ ] Security review: `/security-review`
- [ ] SAST scan: `/security-scanning:security-sast`
- [ ] Dependency audit: `npm audit --audit-level=high`
- [ ] No new CVEs introduced
```

### IAM Security Gate

```markdown
### Validation: IAM

- [ ] IAM policies follow least privilege
- [ ] No wildcards in resource ARNs
- [ ] No inline policies
- [ ] Service roles use conditions
```

### Secrets Gate

```markdown
### Validation: Secrets

- [ ] No secrets in code: `npm run scan:secrets`
- [ ] Secrets in Secrets Manager/SSM
- [ ] Encryption at rest enabled
- [ ] Rotation configured
```

## User Checkpoint Patterns

### Approval Checkpoint

```markdown
@phase-N-approval

Phase N: <Name> validation complete.

Results:

- Tests: PASS (47/47)
- Build: PASS
- Deploy: PASS
- Security: PASS (0 issues)

Changes Summary:

- Created: 3 new files
- Modified: 5 files
- Deleted: 0 files

Approve to proceed? (y/n)
```

### Review Checkpoint

```markdown
@phase-N-review

Phase N: <Name> ready for review.

Code Changes:

- `src/services/user.ts` - New user service
- `tests/user.test.ts` - User service tests

Please review the implementation before validation.
```

### Decision Checkpoint

```markdown
@phase-N-decision

Phase N: <Name> reached decision point.

Option A: Proceed with current approach

- Pros: Faster, simpler
- Cons: Less flexible

Option B: Refactor for extensibility

- Pros: More maintainable
- Cons: More time

Which approach?
```

## Conditional Validation

### Environment-Specific

```markdown
### Validation (per environment)

- [ ] Dev: Auto-approve
- [ ] Staging: Integration tests required
- [ ] Prod: Full regression + load test + approval
```

### Risk-Based

```markdown
### Validation (by risk level)

- [ ] Low risk (config changes): Auto-approve
- [ ] Medium risk (new features): Integration tests
- [ ] High risk (data migrations): Full validation + manual approval
```

## Validation Gate Composition

Combine gates based on phase type:

### Foundation Phase

```text
Standard Gate + CDK Synth Gate + CDK Deploy Gate
```

### Feature Phase

```text
Standard Gate + Integration Gate + Security Gate
```

### Migration Phase

```text
Standard Gate + Schema Gate + Data Integrity Gate + Performance Gate
```

### Release Phase

```text
Standard Gate + Integration Gate + Load Gate + Security Gate + User Approval
```

## Gate Failure Handling

### Retry Strategy

```markdown
On validation failure:

1. Log failure details
2. Analyze root cause
3. Generate fix plan
4. Execute fix
5. Re-run validation (max 3 retries)
6. If still failing: Escalate to user
```

### Rollback Strategy

```markdown
On unrecoverable failure:

1. Stop dependent phases
2. Rollback to last good state: `git checkout hld-phase-{N-1}-complete`
3. Notify user of rollback
4. Await manual intervention
```

### Skip Strategy (with approval)

```markdown
On known-acceptable failure:

1. Document why skip is acceptable
2. Require explicit user approval
3. Log skip in execution state
4. Add to tech debt tracker
```

## Timeout Configuration

```markdown
### Validation Timeouts

| Check             | Timeout  | Action on Timeout |
| ----------------- | -------- | ----------------- |
| Unit tests        | 5 min    | Fail              |
| Integration tests | 15 min   | Fail              |
| CDK deploy        | 30 min   | Fail + rollback   |
| Load tests        | 60 min   | Fail              |
| User approval     | 24 hours | Pause             |
```
