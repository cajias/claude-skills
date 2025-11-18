# GitHub Issue Grooming Skill

## Objective

Organize GitHub repository issues with proper milestones, native relationships, and clean labeling structure.

## Prerequisites

Before starting, ensure:
1. GitHub CLI (`gh`) is installed and authenticated
2. You have write/admin access to the target repository
3. Issues exist with dependency information in their descriptions (e.g., "Depends on:", "Blocks:", "Parent Issue:")

## Step-by-Step Workflow

### Phase 1: Discovery and Analysis

**Use sub-agents to fetch data concurrently:**

1. **Fetch all issues:**
   ```bash
   gh issue list --repo OWNER/REPO --limit 1000 --json number,title,body,milestone,labels,state
   ```

2. **Fetch existing milestones:**
   ```bash
   gh api repos/OWNER/REPO/milestones --jq '.[] | {number: .number, title: .title, state: .state}'
   ```

3. **Analyze issue structure:**
   - Identify phase structure from epic/parent issues
   - Map issues to phases based on labels, descriptions, or numbering
   - Extract dependency relationships from issue bodies

### Phase 2: Milestone Setup

**Create milestones for identified phases:**

1. **Create missing milestones:**
   ```bash
   gh api repos/OWNER/REPO/milestones -X POST -f title="PHASE_NAME"
   ```

2. **Fetch milestone numbers:**
   ```bash
   gh api repos/OWNER/REPO/milestones --jq '.[] | {number: .number, title: .title}'
   ```

3. **Create phase-to-milestone mapping:**
   - Document which milestone number corresponds to each phase
   - This mapping will be used for issue assignment

### Phase 3: Issue Organization

**Use sub-agents to update issues by phase concurrently:**

For each phase, perform these operations in parallel:

1. **Assign issues to milestones:**
   ```bash
   gh issue edit ISSUE_NUM --repo OWNER/REPO --milestone MILESTONE_NUM
   ```

2. **Add dependency checkboxes to issue bodies:**
   - Parse existing body
   - Add tasklist section: "- [ ] #DEPENDENCY_ISSUE"
   - Update issue body with new content

### Phase 4: Native Relationship Setup

**Set GitHub's native blocked-by relationships using GraphQL API:**

**IMPORTANT:** Use the GraphQL API, not comments or labels.

1. **Get issue global IDs:**
   ```bash
   gh api graphql -f query='
   query {
     repository(owner: "OWNER", name: "REPO") {
       issue(number: ISSUE_NUM) {
         id
       }
     }
   }' --jq '.data.repository.issue.id'
   ```

2. **Set blocking relationships:**
   ```bash
   gh api graphql -f issueId="BLOCKED_ISSUE_ID" -f blockingIssueId="BLOCKING_ISSUE_ID" -f mutation='
   mutation($issueId: ID!, $blockingIssueId: ID!) {
     addBlockedBy(input: {issueId: $issueId, blockingIssueId: $blockingIssueId}) {
       blockedIssue { number title }
       blockingIssue { number title }
     }
   }'
   ```

**Key Points:**
- Use `addBlockedBy` mutation (there is no `addBlocks` mutation)
- To make Issue A block Issue B, set B as blocked by A
- Relationships are bidirectional and automatically synchronized
- Requires global node IDs (base64 encoded), not issue numbers

### Phase 5: Label Cleanup

**Remove redundant labels now that milestones and relationships are in place:**

1. **Identify redundant labels:**
   - Phase labels (phase-1, phase-2, etc.) → Use milestones instead
   - Dependency labels (blocked, depends-on) → Use native relationships instead
   - Status labels that duplicate milestone information

2. **Remove labels from issues:**
   ```bash
   gh issue edit ISSUE_NUM --repo OWNER/REPO --remove-label "LABEL_NAME"
   ```

3. **Delete label definitions:**
   ```bash
   gh label delete "LABEL_NAME" --repo OWNER/REPO --yes
   ```

## Concurrent Processing Strategy

**Use sub-agents for parallel execution:**

When processing large repositories, launch multiple sub-agents to work concurrently:

- **Phase 1**: One agent per data source (issues, milestones)
- **Phase 2**: One agent to create all milestones
- **Phase 3-4**: One agent per phase (e.g., 5 agents for 5 phases)
- **Phase 5**: One agent per label type to remove

This approach significantly reduces processing time for repositories with many issues.

## Error Handling

**Common issues and solutions:**

1. **GraphQL mutation fails:**
   - Verify you're using global node IDs, not issue numbers
   - Check repository permissions
   - Ensure both issues exist

2. **Milestone assignment fails:**
   - Verify milestone number exists
   - Check issue isn't in a different repository

3. **Rate limiting:**
   - GitHub GraphQL API: 5,000 points/hour
   - Each query/mutation costs points
   - Space out requests if hitting limits

## Verification

After completing the workflow, verify:

1. **Milestones created:**
   ```bash
   gh api repos/OWNER/REPO/milestones
   ```

2. **Issue relationships:**
   - Visit any issue in GitHub UI
   - Check sidebar for "Blocked by" section
   - Verify relationships are visible

3. **Labels removed:**
   ```bash
   gh label list --repo OWNER/REPO
   ```

4. **Issues assigned to milestones:**
   ```bash
   gh issue list --repo OWNER/REPO --json number,milestone
   ```

## Best Practices

1. **Always use native GitHub features over workarounds:**
   - Native relationships > Comments mentioning "blocks"
   - Milestones > Phase labels
   - Project boards > Label-based tracking

2. **Work concurrently when possible:**
   - Use sub-agents for independent operations
   - Process phases in parallel
   - Batch read operations, serialize writes

3. **Preserve existing information:**
   - Keep dependency information in issue bodies even after setting native relationships
   - Maintain component/category labels that aren't redundant
   - Don't remove labels that serve unique purposes

4. **Document the process:**
   - Comment on epic issues with summary of changes
   - Note milestone structure in project documentation
   - Track which relationships were added

## Example Output

After running this skill, a repository should have:

```
✓ 5 phase-based milestones created
✓ 48 issues assigned to appropriate milestones
✓ 112 native "blocked by" relationships established
✓ 5 redundant phase labels removed from all issues
✓ 5 redundant label definitions deleted
✓ Complete dependency graph visible in GitHub UI
```

## Dependencies

- **GitHub CLI**: v2.0.0 or higher
- **GraphQL API access**: Included with GitHub authentication
- **Permissions**: Write or Admin access to target repository

## Related Skills

- Project board setup
- Issue template creation
- GitHub Actions workflow design
