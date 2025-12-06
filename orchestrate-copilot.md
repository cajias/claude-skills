# GitHub Copilot Orchestration Skill

This skill enables Claude Code to orchestrate GitHub Copilot (@copilot) to work on GitHub issues,
manage pull requests, and coordinate a development workflow.

## Overview

You act as a project orchestrator that assigns issues to @copilot, monitors its work, reviews PRs,
and manages the development pipeline. @copilot does the actual coding work, while you provide
direction, review, and quality control.

## Key Principles

1. **@copilot responds to PR/issue comments, NOT reviews**
   - Use `gh pr comment` or `gh issue comment` with @copilot mentions
   - PR reviews (CHANGES_REQUESTED) do NOT trigger @copilot workflows
   - Always follow up reviews with a comment tagging @copilot

2. **Keep PRs in draft until ready for user review**
   - Only mark PR as "ready for review" when all criteria are met
   - User provides final approval and merge decision
   - Use `gh pr ready <number>` to remove draft status

3. **Use TodoWrite for progress tracking**
   - Track each phase of the orchestration workflow
   - Update status as you complete tasks

## Workflow Steps

### 1. Identify Unblocked Issues

Check the issue dependency graph to find issues that are ready to work on:

```bash
# List open issues
gh issue list --state open --json number,title,assignees

# Check specific issue details
gh issue view <number> --json title,body,assignees
```

### 2. Assign Issues to @copilot

Assign unblocked issues and add a prompting comment:

```bash
# Assign the issue
gh issue edit <number> --add-assignee "@copilot"

# Add prompting comment with context
gh issue comment <number> --body "@copilot Please start working on this issue.

<Provide context about completed dependencies>
<Reference any relevant files or systems now available>
<Mention if this can be worked on in parallel with other issues>

Please implement as specified in the acceptance criteria."
```

**Example:**

```bash
gh issue edit 5 --add-assignee "@copilot"
gh issue comment 5 --body "@copilot Please start working on this issue.

Issues #3 (configuration system) and #4 (embedded resources) are now complete.

You now have access to:
- \`internal/config/\` - Config loading system
- \`internal/resources/\` - Embedded templates

Please implement the Docker Compose integration."
```

### 3. Monitor for PR Creation

Watch for @copilot to create PRs:

```bash
# Check recent workflow runs
gh run list --limit 5 --json databaseId,status,displayTitle,createdAt

# List open PRs
gh pr list --state open --json number,title,isDraft,author
```

Workflow names to watch for:

- "Running Copilot"
- "Addressing comment on PR #X"

### 4. Review PRs Against Acceptance Criteria

When @copilot creates a PR, review it thoroughly:

```bash
# Get PR details
gh pr view <number> --json files,additions,deletions,commits

# Read changed files
gh pr diff <number> --name-only

# Check specific files
gh api repos/<owner>/<repo>/pulls/<number>/files --jq '.[] | select(.filename == "path/to/file") | .patch'
```

**Review checklist:**

- [ ] All acceptance criteria from the issue are met
- [ ] Tests are included and passing
- [ ] Code follows project conventions
- [ ] No security vulnerabilities introduced
- [ ] Documentation updated if needed

Use the Task tool with subagent_type "general-purpose" for complex reviews:

```text
Task: Review PR #<number> for issue #<issue_number>
Prompt: Review PR #<number> against acceptance criteria from .github/ISSUES_BREAKDOWN.md
- Check each criterion: PASS/FAIL
- Verify tests exist and are comprehensive
- Identify any missing items
Return: Detailed review with specific feedback
```

### 5. Request Changes (If Needed)

If PR doesn't meet criteria, provide specific feedback via COMMENT:

```bash
# Do NOT use gh pr review --request-changes (doesn't trigger @copilot)
# Instead, use gh pr comment:

gh pr comment <number> --body "@copilot <Issue summary>

## Issues to Fix

### 1. <Issue title> ❌
<Specific description of what's wrong>
<Exact fix needed>

### 2. <Issue title> ❌
<Specific description>

## What's Working Well ✅
<Positive feedback on what was done correctly>

Please address these issues and push the fixes."
```

**Example:**

```bash
gh pr comment 18 --body "@copilot Good progress! However, there are issues to address:

## Issues to Fix

### 1. Missing Test Case ❌
The acceptance criteria specifies: \"Test with missing values (should use defaults)\"
Please add a test that verifies defaults are applied when config fields are empty.

### 2. Duplicate Template Files ❌
Templates exist in TWO locations:
- \`internal/resources/docker-compose.template.yml\`
- \`resources/docker-compose.template.yml\`

Action: Remove the duplicate in \`resources/\` OR document why both exist

## What's Working Well ✅
- Template rendering is correct
- Embed directives properly implemented
- Existing tests pass

Please fix and push updates."
```

### 6. Wait for @copilot Response

Monitor for @copilot to push fixes:

```bash
# Check for new workflow runs
gh run list --limit 3 --json status,displayTitle,createdAt

# Check PR for new commits
gh pr view <number> --json commits,updatedAt --jq '{commits: (.commits | length), updatedAt}'
```

### 7. Re-review After Changes

Once @copilot pushes fixes, verify all issues are resolved:

```bash
# Check what changed in latest commit
gh pr view <number> --json commits --jq '.commits[-1] | {message: .messageHeadline, date: .committedDate}'

# Review the fixes
gh pr diff <number>
```

### 8. Approve and Mark Ready

When PR meets all criteria:

```bash
# Add approval comment
gh pr comment <number> --body "Excellent work @copilot! All issues addressed.

## Verification ✅
<List of what was verified>

The PR now meets all acceptance criteria. Ready for final review!"

# Mark as ready for review (removes draft status)
gh pr ready <number>
```

**Important:** Only mark as ready when you're confident the user can approve and merge.

### 9. Handle Merge Conflicts

If a PR has merge conflicts:

#### Option A: Ask @copilot to resolve

```bash
gh pr comment <number> --body "@copilot This PR has merge conflicts with main.

Please update your branch:
1. Fetch latest main
2. Merge main into your branch
3. Resolve conflicts in <file>
4. Ensure code compiles
5. Push resolved changes"
```

#### Option B: Resolve manually (if @copilot struggles)

```bash
# Fetch branches
git fetch origin main
git fetch origin <pr-branch>

# Create local branch
git checkout -b resolve-conflicts origin/<pr-branch>

# Merge main
git merge origin/main
# Resolve conflicts in editor

# Commit and push
git add <resolved-files>
git commit -m "Resolve merge conflicts with main"
git push origin resolve-conflicts:<pr-branch>
```

### 10. User Reviews and Merges

After marking PR as ready:

- User sees the PR without draft badge
- User does final review
- User merges when satisfied

Your job is complete when the PR is ready for user review.

## Common Patterns

### Assigning Multiple Issues in Parallel

```bash
# Assign all unblocked issues at once
gh issue edit 5 --add-assignee "@copilot"
gh issue edit 11 --add-assignee "@copilot"
gh issue edit 14 --add-assignee "@copilot"

# Add comments to each
gh issue comment 5 --body "@copilot Please start on this..."
gh issue comment 11 --body "@copilot Please start on this..."
gh issue comment 14 --body "@copilot Please start on this..."
```

@copilot will typically work on them sequentially or based on complexity.

### Monitoring Multiple Active PRs

```bash
# Check all open PRs at once
gh pr list --json number,title,isDraft,reviewDecision,mergeable

# Check specific PRs for conflicts
gh pr view 17 --json mergeable,mergeStateStatus
gh pr view 18 --json mergeable,mergeStateStatus
```

### Updating Epic Issue with Progress

```bash
gh issue comment 1 --body "## Progress Update

**Completed Issues:**
- ✅ #2: <title> (PR #16) - MERGED
- ✅ #3: <title> (PR #17) - MERGED

**In Progress:**
- 🔄 #5: Assigned to @copilot
- 🔄 #11: Assigned to @copilot

**Overall Progress:** X/15 issues completed (Y%)"
```

## Troubleshooting

### @copilot Not Responding

**Symptom:** Workflow doesn't start after comment
**Solution:**

- Verify you used `gh pr comment` or `gh issue comment` (not `gh pr review`)
- Check that you mentioned `@copilot` in the comment
- Wait 30-60 seconds for workflow to trigger
- Check workflow runs: `gh run list --limit 5`

### PR Still Has Conflicts After @copilot "Fixes"

**Symptom:** mergeable: false after merge attempt
**Solution:**

- Check merge status: `gh pr view <number> --json mergeable,mergeStateStatus`
- Resolve manually (see step 9)
- Understand what conflicted and why

### Review Comments Not Being Addressed

**Symptom:** @copilot created PR but ignores review feedback
**Solution:**

- Reviews don't trigger @copilot - use comments instead
- Post comment with `@copilot` mention summarizing review feedback
- Be very specific about what needs to change

## Best Practices

1. **Be Specific in Feedback**
   - Don't just say "fix the tests"
   - Say "Add a test for X that verifies Y behavior"
   - Include code examples when helpful

2. **Acknowledge Good Work**
   - Always include "What's Working Well" section
   - Positive reinforcement helps context

3. **Use Task Tool for Complex Reviews**
   - Large PRs benefit from subagent analysis
   - Can review multiple aspects in parallel
   - Returns structured feedback

4. **Track Progress with TodoWrite**
   - Update after each major step
   - Helps you remember where you are
   - User can see progress if they ask "status"

5. **Keep User Informed**
   - Mark PRs ready only when truly ready
   - Update epic issue periodically
   - Provide clear status when asked

## Example Complete Workflow

```bash
# 1. Assign issue
gh issue edit 5 --add-assignee "@copilot"
gh issue comment 5 --body "@copilot Please implement Docker Compose integration..."

# 2. Wait for PR (monitor workflows)
gh run list --limit 3

# 3. Review when PR appears
gh pr view 19 --json files,commits
# Use Task tool for detailed review

# 4. Request changes if needed
gh pr comment 19 --body "@copilot Issues to fix: ..."

# 5. Wait for fixes
gh run watch <run-id>

# 6. Re-review
gh pr diff 19

# 7. Approve and mark ready
gh pr comment 19 --body "All criteria met! ✅"
gh pr ready 19

# 8. Update tracking
# TodoWrite: mark task complete
# Issue comment: update epic with progress
```

## Integration with Your Workflow

When a user asks you to orchestrate @copilot:

1. **Initial Setup**
   - Understand the issue structure and dependencies
   - Identify which issues are unblocked
   - Set up TodoWrite tracking

2. **Assignment Phase**
   - Assign unblocked issues to @copilot
   - Add clear, contextual comments
   - Start monitoring for PRs

3. **Review Loop**
   - Review PRs against acceptance criteria
   - Request changes via comments (not reviews)
   - Iterate until all criteria met

4. **Completion Phase**
   - Mark PR as ready for user review
   - Update epic issue with progress
   - Assign next unblocked issues

5. **Conflict Resolution**
   - Resolve merge conflicts when they occur
   - Ensure PR is mergeable before marking ready

Remember: You are the **orchestrator**, @copilot is the **implementer**, and the user is
the **decision maker** for final merges.
