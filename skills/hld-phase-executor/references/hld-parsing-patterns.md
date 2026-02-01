# HLD Parsing Patterns

Detailed patterns for parsing various High-Level Design document formats.

## Supported HLD Formats

### Format 1: Markdown with Phase Headers

The most common format uses H2 headers for phases:

```markdown
# HLD: Project Name

## Phase 1: Foundation
### Description
Set up foundational infrastructure.

### Dependencies
- Depends on: none

### Deliverables
- [ ] Create VPC
- [ ] Create subnets
- [ ] Configure NAT gateway

### Validation Criteria
- CDK synth passes
- VPC deployed successfully
- Network connectivity verified

### Deployment Command
`npm run deploy:foundation`
```

**Parsing strategy:**
1. Split on `## Phase` pattern
2. Extract phase number from header
3. Parse each section by `###` subheaders
4. Convert deliverables to checkboxes array
5. Parse dependencies as comma-separated list

### Format 2: Numbered List Format

Simpler format for linear dependencies:

```markdown
# Migration Plan

1. **Create new infrastructure**
   - Deliverables: VPC, subnets, security groups
   - Validation: CDK synth passes
   - Deploy: `npm run deploy:infra`

2. **Migrate database** (depends on: 1)
   - Deliverables: RDS instance, migration scripts
   - Validation: Database accessible, data migrated
   - Deploy: `npm run deploy:database`
```

**Parsing strategy:**
1. Match numbered list items with bold headers
2. Extract deliverables from sub-bullets
3. Parse parenthetical dependencies
4. Default to linear dependency if not specified

### Format 3: Table Format

Structured format with explicit columns:

```markdown
# HLD: Feature Rollout

| Phase | Name | Depends On | Deliverables | Validation |
|-------|------|-----------|--------------|------------|
| 1 | API Design | - | OpenAPI spec, types | Spec validates |
| 2 | Backend | 1 | Endpoints, DB | Tests pass |
| 3 | Frontend | 2 | UI components | E2E tests |
| 4 | Launch | 2, 3 | Feature flags | Canary OK |
```

**Parsing strategy:**
1. Parse markdown table headers
2. Map columns to phase attributes
3. Split "Depends On" column on commas
4. Handle "-" as no dependencies

### Format 4: YAML Front Matter

HLD with structured metadata:

```markdown
---
project: Database Migration
phases:
  - name: Create Tables
    id: 1
    depends_on: []
    deploy_cmd: npm run deploy:tables
  - name: Dual Write
    id: 2
    depends_on: [1]
    deploy_cmd: npm run deploy:dual-write
---

## Phase 1: Create Tables

Detailed description of phase 1...

## Phase 2: Dual Write

Detailed description of phase 2...
```

**Parsing strategy:**
1. Extract YAML front matter
2. Parse phase metadata from YAML
3. Match phase content by name/id
4. Merge metadata with content

## Dependency Extraction

### Explicit Dependencies

Look for patterns:
- `Depends on: Phase 1, Phase 2`
- `depends on: 1, 2`
- `(depends on: Phase 1)`
- `Prerequisites: Phase 1`
- `Blocked by: Phase 1`
- `Requires: Foundation phase`

### Implicit Dependencies

When dependencies not stated:
- Assume linear dependency (Phase N depends on Phase N-1)
- Look for resource references ("uses VPC from Phase 1")
- Check for interface mentions ("implements API from Phase 2")

### Parallel Phases

Identify phases that can run in parallel:
- Same dependency set
- No resource conflicts
- Explicit "can run in parallel with" notation

## Deliverable Extraction

### Checkbox Format
```markdown
- [ ] Create user table
- [ ] Add indexes
- [x] Already completed item (ignore)
```

### Bullet Format
```markdown
- Create user table
- Add indexes
```

### Numbered Format
```markdown
1. Create user table
2. Add indexes
```

### Prose Format
```markdown
This phase creates the user table and adds indexes for query performance.
```

**For prose:** Extract noun phrases as deliverables using pattern matching.

## Validation Criteria Extraction

### Explicit Criteria
```markdown
### Validation Criteria
- All tests pass
- Deployment succeeds
- No errors in logs
```

### Command-Based
```markdown
### Validation
Run: `npm test && npm run deploy:check`
```

### Implicit Criteria

If no validation specified, apply defaults:
1. Unit tests pass (`npm test`)
2. Build succeeds (`npm run build`)
3. Lint passes (`npm run lint`)
4. Deployment command succeeds (if provided)

## Edge Cases

### Missing Phase Numbers

If phases use names only:
1. Assign sequential numbers
2. Use names for dependency resolution
3. Normalize to "Phase N: Name" format

### Circular Dependencies

Detect during parsing:
```
Phase A -> Phase B -> Phase C -> Phase A  (INVALID)
```

Report to user with the cycle path.

### Self-Dependencies

Invalid:
```
Phase 1 depends on: Phase 1
```

Remove self-references and warn user.

### Unknown Dependencies

```
Phase 2 depends on: Phase X (not defined)
```

Fail parsing and report undefined phase.

## Output Format

Normalized phase structure:

```json
{
  "phases": [
    {
      "number": 1,
      "name": "Foundation",
      "description": "Set up foundational infrastructure",
      "dependencies": [],
      "deliverables": [
        "Create VPC",
        "Create subnets",
        "Configure NAT gateway"
      ],
      "validationCriteria": [
        "CDK synth passes",
        "VPC deployed successfully"
      ],
      "deploymentCommand": "npm run deploy:foundation",
      "status": "pending"
    }
  ],
  "dependencyGraph": {
    "1": [],
    "2": [1],
    "3": [1],
    "4": [2, 3]
  }
}
```

## Validation During Parsing

Before accepting HLD:
- [ ] At least one phase exists
- [ ] At least one phase has no dependencies (entry point)
- [ ] No circular dependencies
- [ ] All referenced phases exist
- [ ] Each phase has at least one deliverable
- [ ] Phase numbers/names are unique
