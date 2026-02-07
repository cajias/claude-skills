---
name: pr-monitor
description: Monitor GitHub pull requests and automatically resume when new commits are detected
version: 1.0.0
---

# PR Monitoring Skill

## Objective

Set up automated monitoring of GitHub pull requests that triggers Claude Code to auto-resume and
review changes when new commits are detected.

## Prerequisites

Before starting, ensure:

1. GitHub CLI (`gh`) is installed and authenticated
2. You have read access to the target repository
3. The pr-monitor plugin is installed (includes Stop hook)

## When to Use

Use this skill when:

- You want to continuously monitor a PR for updates
- You need to provide automated feedback on new commits
- You're waiting for someone to push changes to a PR
- You want Claude to automatically review PR updates

## Step-by-Step Workflow

### Phase 1: Identify PR to Monitor

**Get PR information:**

1. **If user provides PR URL**, extract repo and PR number:

   ```bash
   # Example URL: https://github.com/owner/repo/pull/123
   # Extract: owner/repo and PR number 123
   ```

2. **If user provides repo and PR number**, verify PR exists:

   ```bash
   gh pr view PR_NUMBER --repo OWNER/REPO --json number,title,state,headRefOid
   ```

3. **If in a git repository**, list open PRs:

   ```bash
   gh pr list --json number,title,headRefOid --limit 20
   ```

### Phase 2: Setup Monitoring State

**Create state file for the Stop hook to monitor:**

1. **Get repository path:**

   ```bash
   # If already in repo
   REPO_PATH=$(pwd)

   # If remote repo, clone first
   gh repo clone OWNER/REPO
   cd REPO
   REPO_PATH=$(pwd)
   ```

2. **Get current commit SHA:**

   ```bash
   CURRENT_SHA=$(gh pr view PR_NUMBER --json headRefOid --jq '.headRefOid')
   ```

3. **Create monitoring state file:**

   ```bash
   # Format: /tmp/claude_monitor_pr_<repo-name>_<pr-number>
   # Extract repo name from path
   REPO_NAME=$(basename "$REPO_PATH")
   STATE_FILE="/tmp/claude_monitor_pr_${REPO_NAME}_${PR_NUMBER}"

   # Write state file with 3 lines: repo_path, pr_number, last_sha
   cat > "$STATE_FILE" <<'EOF'
   $REPO_PATH
   $PR_NUMBER
   $CURRENT_SHA
   EOF
   ```

4. **Confirm monitoring active:**

   ```bash
   echo "✓ Monitoring enabled for PR #$PR_NUMBER"
   echo "✓ State file: $STATE_FILE"
   echo "✓ Current commit: ${CURRENT_SHA:0:8}"
   cat "$STATE_FILE"
   ```

### Phase 3: Initial Review (Optional)

**If requested, perform initial review of current PR state:**

1. **Get PR details:**

   ```bash
   gh pr view PR_NUMBER --json title,body,commits,files
   ```

2. **View recent changes:**

   ```bash
   gh pr diff PR_NUMBER
   ```

3. **Provide initial feedback:**
   - Analyze the current state
   - Comment on PR if appropriate
   - Document baseline for future comparisons

### Phase 4: Wait for Updates

**The Stop hook will now automatically monitor the PR:**

When Claude Code would normally stop:

1. Stop hook checks state file
2. Queries GitHub for PR status
3. Compares current SHA with last_sha
4. If different, auto-resumes with new commit notification

**You can continue working on other tasks** - monitoring happens automatically in the background.

### Phase 5: Auto-Resume on New Commits

**When new commits are detected, Claude will automatically:**

1. **Resume with notification:**
   - Message: "New commits detected in PR #X. Current commit: abcd1234. There are now Y total
     commits. Please review the new changes and provide feedback."

2. **Review new changes:**

   ```bash
   # Get updated PR information
   gh pr view PR_NUMBER --json commits,headRefOid,files

   # Get diff of new changes
   gh pr diff PR_NUMBER

   # Compare with previous state if needed
   git diff OLD_SHA NEW_SHA
   ```

3. **Provide feedback:**

   ```bash
   # Comment on PR
   gh pr comment PR_NUMBER --body "FEEDBACK_TEXT"

   # Or request changes via review
   gh pr review PR_NUMBER --comment --body "REVIEW_TEXT"
   ```

4. **Update monitoring state:**
   - State file is automatically updated by Stop hook
   - Monitoring continues for next update

### Phase 6: Stop Monitoring

**When monitoring is no longer needed:**

1. **Remove state file:**

   ```bash
   rm /tmp/claude_monitor_pr_${REPO_NAME}_${PR_NUMBER}
   ```

2. **Confirm stopped:**

   ```bash
   echo "✓ Monitoring stopped for PR #$PR_NUMBER"
   ```

**Monitoring will also auto-stop if:**

- PR is merged or closed (Stop hook detects and cleans up)
- Repository is deleted
- User manually removes state file

## Error Handling

**Common issues and solutions:**

1. **Hook not triggering:**
   - Verify plugin is installed: Check hooks are registered
   - Verify state file exists: `ls -la /tmp/claude_monitor_pr_*`
   - Test hook manually: `echo '{"stop_hook_active": false}' | bash /path/to/Stop.sh`

2. **PR not accessible:**
   - Verify `gh` is authenticated: `gh auth status`
   - Check repository permissions: `gh pr view PR_NUMBER --repo OWNER/REPO`
   - Ensure repository path is correct in state file

3. **Multiple PRs monitored:**
   - List all monitors: `ls -la /tmp/claude_monitor_pr_*`
   - View specific monitor: `cat /tmp/claude_monitor_pr_REPO_PR`
   - Stop specific monitor: `rm /tmp/claude_monitor_pr_REPO_PR`

## Limitations

1. **Polling-based, not real-time:**
   - Checks happen when Claude Code would naturally stop
   - Not true push notifications
   - May have delays between commit and detection

2. **Requires Claude Code running:**
   - Monitoring only active when Claude Code session is running
   - Stops when you quit Claude Code

3. **State files in /tmp:**
   - May be cleared on system reboot
   - Need to recreate after reboot if persistent monitoring needed

4. **GitHub API rate limits:**
   - Stop hook queries GitHub each time it runs
   - Multiple PRs = more API calls
   - Stay within rate limits (5,000 requests/hour)

## Best Practices

1. **Monitor selectively:**
   - Only monitor PRs you're actively working with
   - Stop monitoring when done
   - Clean up old state files

2. **Provide context in feedback:**
   - Reference specific commits
   - Link to relevant code sections
   - Suggest concrete improvements

3. **Use with other tools:**
   - Combine with PR review workflows
   - Integrate with project management
   - Coordinate with team notifications

## Example Usage

### Scenario: Monitor a PR from Copilot

```bash
# 1. User asks to monitor PR #2 in claude-skills repo
cd /path/to/claude-skills

# 2. Get current state
gh pr view 2 --json headRefOid,title,commits

# 3. Create monitoring state
REPO_PATH=$(pwd)
PR_NUMBER=2
CURRENT_SHA=$(gh pr view 2 --json headRefOid --jq '.headRefOid')
REPO_NAME=$(basename "$REPO_PATH")

cat > /tmp/claude_monitor_pr_${REPO_NAME}_${PR_NUMBER} <<EOF
$REPO_PATH
$PR_NUMBER
$CURRENT_SHA
EOF

# 4. Confirm
echo "✓ Now monitoring PR #2 in claude-skills"
echo "✓ Current commit: ${CURRENT_SHA:0:8}"

# 5. Wait for updates (automatic via Stop hook)
# When Copilot pushes new commits, Claude auto-resumes and reviews
```

## Verification

After enabling monitoring, verify:

1. **State file created:**

   ```bash
   ls -la /tmp/claude_monitor_pr_*
   ```

2. **State file format correct:**

   ```bash
   cat /tmp/claude_monitor_pr_REPO_PR
   # Should show 3 lines: repo_path, pr_number, sha
   ```

3. **PR accessible:**

   ```bash
   gh pr view PR_NUMBER --repo OWNER/REPO
   ```

## Related Skills

- GitHub issue grooming
- Code review automation
- CI/CD monitoring
- Project management
