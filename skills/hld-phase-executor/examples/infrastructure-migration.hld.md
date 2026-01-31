# HLD: Database Infrastructure Migration

**Project:** Migrate from single-table DynamoDB to multi-table design with proper indexes.

**Timeline:** 4 phases, estimated 2-3 days each

---

## Phase 1: Create New Tables
### Description
Create the new DynamoDB tables with the redesigned schema. This phase establishes the foundation for the migration without affecting the existing system.

### Dependencies
- Depends on: none

### Deliverables
- [ ] Create `UserTableV2` with composite key (PK: userId, SK: entityType)
- [ ] Create `OrderTable` with GSI for user lookups
- [ ] Create `ProductTable` with GSI for category queries
- [ ] Add DynamoDB stream on UserTableV2 for CDC
- [ ] Configure auto-scaling policies
- [ ] Set up CloudWatch alarms for throttling

### Validation Criteria
- CDK synth succeeds with no errors
- CDK Nag shows no critical findings
- Tables deploy to dev environment
- Table capacities match design spec

### Deployment Command
`npx cdk deploy DataStackV2 --require-approval never`

---

## Phase 2: Dual-Write Layer
### Description
Implement dual-write logic to write to both old and new tables. This ensures data consistency during the migration window.

### Dependencies
- Depends on: Phase 1

### Deliverables
- [ ] Create `DualWriteService` class
- [ ] Implement write operations to both tables
- [ ] Add transaction support for cross-table consistency
- [ ] Implement retry logic for partial failures
- [ ] Add metrics for write success/failure rates
- [ ] Create feature flag to enable/disable dual-write

### Validation Criteria
- Unit tests pass with 90%+ coverage
- Integration tests verify writes to both tables
- Feature flag correctly toggles behavior
- No data loss in failure scenarios
- Latency increase < 50ms

### Deployment Command
`npx cdk deploy ComputeStack --require-approval never`

---

## Phase 3: Data Backfill
### Description
Migrate historical data from the old table to the new tables. This phase runs in parallel with Phase 2.

### Dependencies
- Depends on: Phase 1

### Deliverables
- [ ] Create `BackfillScript` for historical data migration
- [ ] Implement batched processing (max 25 items per batch)
- [ ] Add progress tracking and resumability
- [ ] Create validation script to compare table counts
- [ ] Implement data integrity checks (checksums)
- [ ] Add dry-run mode for testing

### Validation Criteria
- Backfill completes without errors
- All records migrated (count matches)
- Data integrity validated (checksums match)
- Backfill is resumable after interruption
- Performance: > 1000 records/second

### Deployment Command
`npm run backfill:execute -- --env dev`

---

## Phase 4: Switch Reads
### Description
Switch read operations from old table to new tables. This is the cutover phase that completes the migration.

### Dependencies
- Depends on: Phase 2, Phase 3

### Deliverables
- [ ] Create `ReadSwitchService` with configurable source
- [ ] Implement fallback to old table on errors
- [ ] Add circuit breaker for new table failures
- [ ] Implement gradual rollout (10% -> 50% -> 100%)
- [ ] Create rollback script for emergency
- [ ] Update API responses to new schema format

### Validation Criteria
- All read operations succeed from new tables
- Fallback correctly triggers on errors
- Circuit breaker prevents cascade failures
- End-to-end tests pass
- No user-facing errors during rollout
- P99 latency < 100ms

### Deployment Command
`npx cdk deploy ComputeStack --require-approval never && npm run rollout:reads -- --percentage 100`

---

## Phase 5: Cleanup (Optional)
### Description
Remove dual-write code and decommission old table. Only execute after Phase 4 is stable for 7 days.

### Dependencies
- Depends on: Phase 4
- Minimum wait: 7 days after Phase 4 completion

### Deliverables
- [ ] Remove `DualWriteService` code
- [ ] Remove feature flags
- [ ] Archive old table data to S3
- [ ] Delete old table
- [ ] Update documentation
- [ ] Remove unused IAM policies

### Validation Criteria
- All tests pass without dual-write code
- Old table archived successfully
- No references to old table remain
- Documentation updated

### Deployment Command
`npx cdk deploy --all --require-approval never`

---

## Cross-Phase Resources

| Resource | Created In | Used By | Type |
|----------|-----------|---------|------|
| UserTableV2 | Phase 1 | Phase 2, 3, 4 | DynamoDB |
| OrderTable | Phase 1 | Phase 2, 3, 4 | DynamoDB |
| ProductTable | Phase 1 | Phase 2, 3, 4 | DynamoDB |
| DualWriteService | Phase 2 | Phase 2, 5 | Lambda |
| BackfillScript | Phase 3 | Phase 3 | Script |
| ReadSwitchService | Phase 4 | Phase 4, 5 | Lambda |

## Rollback Plan

| Phase | Rollback Action | Time to Rollback |
|-------|----------------|------------------|
| Phase 1 | Delete new tables | 5 minutes |
| Phase 2 | Disable dual-write flag | 1 minute |
| Phase 3 | Re-run backfill | 30 minutes |
| Phase 4 | Switch reads to old table | 1 minute |
| Phase 5 | Restore from S3 archive | 2 hours |

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Data integrity | 100% | Checksum validation |
| Read latency | P99 < 100ms | CloudWatch metrics |
| Write latency | P99 < 50ms increase | CloudWatch metrics |
| Error rate | < 0.01% | CloudWatch metrics |
| Migration time | < 4 hours | Backfill duration |
