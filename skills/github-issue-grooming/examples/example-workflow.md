# Example Workflow: mcp-lite Repository

This example demonstrates the complete GitHub issue grooming workflow applied to the `cajias/mcp-lite` repository.

## Repository Context

- **Repository**: cajias/mcp-lite
- **Total Issues**: 48
- **Structure**: 5 phases with parent issues and sub-tasks
- **Initial State**: Issues had dependency information in bodies, but no milestones or native relationships

## Workflow Execution

### Step 1: Discovery

**Concurrent data gathering using 2 sub-agents:**

Agent 1 - Fetch issues:
```bash
gh issue list --repo cajias/mcp-lite --limit 1000 --json number,title,body,milestone,labels,state
```

Agent 2 - Fetch milestones:
```bash
gh api repos/cajias/mcp-lite/milestones --jq '.[] | {number: .number, title: .title, state: .state}'
```

**Results:**
- 48 open issues identified
- 1 existing milestone found (Phase 4)
- 5 phases identified from issue structure

### Step 2: Milestone Creation

**Created missing milestones:**

```bash
gh api repos/cajias/mcp-lite/milestones -X POST -f title="Phase 1: Core Infrastructure"
gh api repos/cajias/mcp-lite/milestones -X POST -f title="Phase 2: MCP Server Management"
gh api repos/cajias/mcp-lite/milestones -X POST -f title="Phase 3: HTTP API Layer"
gh api repos/cajias/mcp-lite/milestones -X POST -f title="Phase 5: Testing & Polish"
```

**Milestone Mapping:**
| Phase | Milestone Number | Title |
|-------|------------------|-------|
| Phase 1 | 2 | Core Infrastructure |
| Phase 2 | 3 | MCP Server Management |
| Phase 3 | 4 | HTTP API Layer |
| Phase 4 | 1 | Dashboard UI (existing) |
| Phase 5 | 5 | Testing & Polish |

### Step 3: Issue Organization

**Concurrent assignment using 5 sub-agents (one per phase):**

**Phase 1 Agent** - Processed issues #1, 6-14:
```bash
gh issue edit 1 --repo cajias/mcp-lite --milestone 2
gh issue edit 6 --repo cajias/mcp-lite --milestone 2
# ... continued for all Phase 1 issues
```

**Phase 2 Agent** - Processed issues #2, 15-21:
```bash
gh issue edit 2 --repo cajias/mcp-lite --milestone 3
# ... continued for all Phase 2 issues
```

*Similar for Phases 3-5*

**Results:**
- Phase 1: 10 issues → Milestone 2
- Phase 2: 8 issues → Milestone 3
- Phase 3: 9 issues → Milestone 4
- Phase 4: 10 issues → Milestone 1
- Phase 5: 11 issues → Milestone 5

### Step 4: Native Relationships

**Set 112 blocking relationships using GraphQL API:**

**Example: Setting Issue #7 blocked by Issue #6**

1. Get global IDs:
```bash
# Get Issue #6 ID
ID6=$(gh api graphql -f query='query {
  repository(owner: "cajias", name: "mcp-lite") {
    issue(number: 6) { id }
  }
}' --jq '.data.repository.issue.id')
# Returns: I_kwDON8xAbM6cPqrs

# Get Issue #7 ID
ID7=$(gh api graphql -f query='query {
  repository(owner: "cajias", name: "mcp-lite") {
    issue(number: 7) { id }
  }
}' --jq '.data.repository.issue.id')
# Returns: I_kwDON8xAbM6cPqrt
```

2. Create relationship:
```bash
gh api graphql -f issueId="$ID7" -f blockingIssueId="$ID6" -f mutation='
mutation($issueId: ID!, $blockingIssueId: ID!) {
  addBlockedBy(input: {issueId: $issueId, blockingIssueId: $blockingIssueId}) {
    blockedIssue { number title }
    blockingIssue { number title }
  }
}'
```

**Relationship Summary by Phase:**

- **Phase 1**: 10 relationships
  - #7 blocked by #6
  - #8 blocked by #7
  - #9 blocked by #6
  - #10 blocked by #7
  - #11 blocked by #7
  - #12 blocked by #7, #11 (2 blockers)
  - #13 blocked by #11
  - #14 blocked by #7, #8 (2 blockers)

- **Phase 2**: 16 relationships
  - #2 blocked by #1
  - #15 blocked by #1
  - #16 blocked by #15
  - #17 blocked by #15
  - #18 blocked by #16, #17
  - #19 blocked by #16, #17
  - #20 blocked by #18, #8
  - #21 blocked by #15, #16, #17, #18, #19, #20 (6 blockers)

- **Phase 3**: 20 relationships
- **Phase 4**: 28 relationships
- **Phase 5**: 38 relationships

**Total**: 112 native blocking relationships established

### Step 5: Label Cleanup

**Identified redundant labels:**
- `phase-1` through `phase-5` (now replaced by milestones)

**Removed from all 48 issues:**
```bash
# Phase 1 issues
gh issue edit 1 --repo cajias/mcp-lite --remove-label "phase-1"
gh issue edit 6 --repo cajias/mcp-lite --remove-label "phase-1"
# ... all Phase 1 issues

# Phase 2 issues
gh issue edit 2 --repo cajias/mcp-lite --remove-label "phase-2"
# ... all Phase 2 issues

# Continued for phases 3-5
```

**Deleted label definitions:**
```bash
gh label delete "phase-1" --repo cajias/mcp-lite --yes
gh label delete "phase-2" --repo cajias/mcp-lite --yes
gh label delete "phase-3" --repo cajias/mcp-lite --yes
gh label delete "phase-4" --repo cajias/mcp-lite --yes
gh label delete "phase-5" --repo cajias/mcp-lite --yes
```

**Labels removed:**
- 48 phase label assignments removed from issues
- 5 label definitions deleted from repository

## Final Results

### Before
- ❌ 1 milestone, 47 issues without milestones
- ❌ No native issue relationships
- ❌ Dependency tracking only in comments/bodies
- ❌ Phase information duplicated in labels
- ❌ No clear dependency visualization

### After
- ✅ 5 phase-based milestones
- ✅ All 48 issues assigned to appropriate milestones
- ✅ 112 native "blocked by" relationships
- ✅ Dependency graph visible in GitHub UI
- ✅ Clean label structure (26 labels, no redundancy)
- ✅ Ready for GitHub Projects board visualization

## Verification

**Check milestones:**
```bash
gh api repos/cajias/mcp-lite/milestones
```

**Check issue #15 relationships:**
Visit: https://github.com/cajias/mcp-lite/issues/15
- Sidebar shows "Blocked by #1"
- Native GitHub relationship visible

**Check labels:**
```bash
gh label list --repo cajias/mcp-lite --json name
# phase-1 through phase-5 no longer present
```

## Performance Metrics

- **Total time**: ~5 minutes (with concurrent sub-agents)
- **API calls**: ~200 (fetches + mutations)
- **Issues processed**: 48
- **Relationships created**: 112
- **Labels cleaned**: 53 (48 assignments + 5 definitions)

## Key Learnings

1. **Concurrent processing is essential**: Processing 5 phases in parallel reduced time from ~15 minutes to ~5 minutes

2. **GraphQL IDs are required**: Cannot use issue numbers directly in `addBlockedBy` mutations

3. **Native features are superior**: GitHub UI automatically shows relationship graphs, dependency chains, and blocks completion tracking

4. **Labels should be semantic, not structural**: Keep component labels (api, frontend), remove phase labels (replaced by milestones)

5. **Document as you go**: The dependency information in issue bodies remains valuable even after setting native relationships
