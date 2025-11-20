# How to Use PR Monitor Plugin for Automated Pull Request Monitoring

## Overview

The PR Monitor plugin enables automated monitoring of GitHub pull requests with automatic resumption of Claude Code when new commits are detected. This guide provides detailed instructions for installation, usage, and troubleshooting.

## What This Plugin Does

**Problem it solves:** Manually checking PRs for updates is tedious and easy to miss. You want Claude to automatically notify you and resume work when collaborators push new commits.

**Solution:** A Stop hook that checks monitored PRs when Claude would idle, automatically resuming with a notification when new commits are detected.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ User enables PR monitoring                                   │
│ Creates state file: /tmp/claude_monitor_pr_<repo>_<pr>      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Claude Code finishes current task → Would normally stop     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stop Hook Triggers                                           │
│ - Checks for state files in /tmp/claude_monitor_pr_*        │
│ - Queries GitHub API for each monitored PR                  │
│ - Compares current commit SHA with last known SHA           │
└────────────────────────┬────────────────────────────────────┘
                         │
                  ┌──────┴──────┐
                  │             │
        No Changes│             │New Commits
                  ▼             ▼
         ┌────────────┐   ┌──────────────────────────────┐
         │ Allow Stop │   │ Block Stop                    │
         │ Exit 0     │   │ Return {"decision": "block"}  │
         └────────────┘   └──────────┬───────────────────┘
                                     │
                                     ▼
                          ┌──────────────────────────────┐
                          │ Claude Auto-Resumes          │
                          │ - Reviews PR changes         │
                          │ - Provides feedback          │
                          │ - Updates state file         │
                          └──────────────────────────────┘
```

## Installation

### Method 1: Via Claude Plugin Manager (Recommended)

```bash
claude plugin install https://github.com/cajias/claude-skills/tree/main/plugins/pr-monitor
```

**Then restart Claude Code:**
- Quit Claude Code completely
- Relaunch Claude Code
- Hook will be active on restart

### Method 2: Manual Installation

```bash
# 1. Clone the repository
git clone https://github.com/cajias/claude-skills.git
cd claude-skills

# 2. Copy plugin to Claude plugins directory
mkdir -p ~/.claude/plugins/pr-monitor
cp -r plugins/pr-monitor/* ~/.claude/plugins/pr-monitor/

# 3. Verify installation
ls -la ~/.claude/plugins/pr-monitor/

# Expected output:
# .claude-plugin/plugin.json
# hooks/hooks.json
# scripts/Stop.sh (executable)
# skills/pr-monitor/SKILL.md
# README.md

# 4. Restart Claude Code
```

## Prerequisites

Before using the plugin:

1. **GitHub CLI (`gh`)** - Version 2.0.0 or higher
   ```bash
   # Install
   brew install gh  # macOS
   # or
   sudo apt-get install gh  # Linux

   # Authenticate
   gh auth login

   # Verify
   gh auth status
   ```

2. **jq** - For JSON parsing
   ```bash
   # Install
   brew install jq  # macOS
   # or
   sudo apt-get install jq  # Linux

   # Verify
   jq --version
   ```

3. **Repository Access** - Read access to repositories you want to monitor

## Usage

### Quick Start: Ask Claude

The simplest way to start monitoring:

```
Monitor PR cajias/claude-skills#2 in this repository for new commits
```

Claude will:
1. Verify PR exists
2. Get current commit SHA
3. Create monitoring state file
4. Confirm monitoring is active

### Manual Setup (Advanced)

If you want to set up monitoring manually:

```bash
# 1. Navigate to repository
cd /path/to/repository

# 2. Get current PR commit SHA
CURRENT_SHA=$(gh pr view PR_NUMBER --json headRefOid --jq '.headRefOid')

# 3. Get repository path and name
REPO_PATH=$(pwd)
REPO_NAME=$(basename "$REPO_PATH")

# 4. Create state file
cat > /tmp/claude_monitor_pr_${REPO_NAME}_${PR_NUMBER} <<EOF
$REPO_PATH
$PR_NUMBER
$CURRENT_SHA
EOF

# 5. Verify
cat /tmp/claude_monitor_pr_${REPO_NAME}_${PR_NUMBER}
```

### State File Format

State files are stored in `/tmp/claude_monitor_pr_<repo-name>_<pr-number>`

**Format (3 lines):**
```
Line 1: /absolute/path/to/repository
Line 2: PR_NUMBER
Line 3: LAST_COMMIT_SHA
```

**Example:**
```
/Users/cajias/Projects/claude-skills
2
a19ca15f67612f2ed5501d5cb2a65f1b7c1f94d7
```

## Monitoring Multiple PRs

You can monitor multiple PRs simultaneously:

```bash
# Ask Claude:
"Monitor PRs cajias/claude-skills#1, cajias/claude-skills#2, and cajias/claude-skills#3 in this repository"
```

Each PR is monitored independently.

## Stopping Monitoring

### Ask Claude

```
Stop monitoring PR cajias/claude-skills#2
```

### Manual Removal

```bash
# Stop specific PR monitoring
rm /tmp/claude_monitor_pr_<repo-name>_<pr-number>

# Stop all PR monitoring
rm /tmp/claude_monitor_pr_*
```

## Troubleshooting

### Hook Not Triggering

1. **Verify plugin installed:**
   ```bash
   ls -la ~/.claude/plugins/pr-monitor/
   ```

2. **Check hook script is executable:**
   ```bash
   ls -l ~/.claude/plugins/pr-monitor/scripts/Stop.sh
   # Should show: -rwxr-xr-x (executable)
   ```

3. **Test hook manually:**
   ```bash
   echo '{"stop_hook_active": false}' | ~/.claude/plugins/pr-monitor/scripts/Stop.sh
   ```

### PR Changes Not Detected

1. **Verify state file format:**
   ```bash
   cat /tmp/claude_monitor_pr_<repo-name>_<pr-number>
   # Should have exactly 3 lines:
   # Line 1: Repository path
   # Line 2: PR number
   # Line 3: Last commit SHA
   ```

2. **Check if state file exists:**
   ```bash
   ls -la /tmp/claude_monitor_pr_*
   ```

3. **Verify PR is accessible:**
   ```bash
   cd /path/to/repository
   gh pr view PR_NUMBER --json headRefOid,state,commits
   ```

4. **Test GitHub CLI authentication:**
   ```bash
   gh auth status
   # Should show: ✓ Logged in to github.com
   ```

5. **Check for errors in hook execution:**
   ```bash
   # Test hook manually with verbose output
   echo '{"stop_hook_active": false}' | bash -x ~/.claude/plugins/pr-monitor/scripts/Stop.sh
   ```

### State File Issues

1. **State file not found:**
   - Ensure you created the state file correctly
   - Check spelling of repo name in filename
   - Verify file is in `/tmp` directory

2. **Incorrect format:**
   ```bash
   # Recreate state file with correct format
   REPO_PATH=/path/to/repo
   PR_NUMBER=123
   CURRENT_SHA=$(cd "$REPO_PATH" && gh pr view "$PR_NUMBER" --json headRefOid --jq '.headRefOid')
   
   cat > /tmp/claude_monitor_pr_$(basename "$REPO_PATH")_${PR_NUMBER} <<EOF
   $REPO_PATH
   $PR_NUMBER
   $CURRENT_SHA
   EOF
   ```

3. **Permissions issues:**
   ```bash
   # Ensure state file is readable
   chmod 644 /tmp/claude_monitor_pr_*
   ```

### GitHub API Issues

1. **Rate limit exceeded:**
   ```bash
   # Check rate limit status
   gh api rate_limit
   
   # Output shows remaining requests
   # Wait if limit exceeded (resets hourly)
   ```

2. **Authentication expired:**
   ```bash
   # Re-authenticate
   gh auth login
   
   # Select GitHub.com
   # Choose authentication method
   # Follow prompts
   ```

3. **Permission denied:**
   ```bash
   # Verify you have access to the repository
   gh repo view OWNER/REPO
   
   # If access denied, request access from repo owner
   ```

### Hook Execution Issues

1. **Hook not running:**
   - Restart Claude Code completely
   - Verify hooks are enabled in settings
   - Check `.claude/settings.json` for `disableAllHooks: false`

2. **Multiple stop triggers:**
   ```bash
   # List all monitored PRs
   ls -la /tmp/claude_monitor_pr_*
   
   # Remove unwanted monitors
   rm /tmp/claude_monitor_pr_<repo>_<pr>
   ```

3. **Hook timing out:**
   - Check network connectivity
   - Verify GitHub API is accessible
   - Reduce number of monitored PRs

### Claude Not Auto-Resuming

1. **Check hook output:**
   ```bash
   # Run hook manually to see output
   echo '{"stop_hook_active": false}' | ~/.claude/plugins/pr-monitor/scripts/Stop.sh
   
   # Should output JSON with "decision": "block" when new commits exist
   ```

2. **Verify commit SHA changed:**
   ```bash
   # Get current SHA from GitHub
   gh pr view PR_NUMBER --json headRefOid --jq '.headRefOid'
   
   # Compare with SHA in state file
   cat /tmp/claude_monitor_pr_<repo>_<pr> | sed -n '3p'
   ```

3. **Check PR state:**
   ```bash
   # Verify PR is still open
   gh pr view PR_NUMBER --json state --jq '.state'
   # Should show: OPEN
   ```

## Advanced Usage

### Custom State File Location

By default, state files are stored in `/tmp`. To use a custom location:

```bash
# Modify the Stop.sh script to look in a different directory
# Edit ~/.claude/plugins/pr-monitor/scripts/Stop.sh
# Change: monitor_files=$(find /tmp -name "claude_monitor_pr_*" -type f 2>/dev/null || true)
# To: monitor_files=$(find /custom/path -name "claude_monitor_pr_*" -type f 2>/dev/null || true)
```

### Monitoring External Repositories

```bash
# Clone repository first
gh repo clone OWNER/REPO
cd REPO

# Then set up monitoring
REPO_PATH=$(pwd)
PR_NUMBER=123
CURRENT_SHA=$(gh pr view $PR_NUMBER --json headRefOid --jq '.headRefOid')

cat > /tmp/claude_monitor_pr_$(basename "$REPO_PATH")_${PR_NUMBER} <<EOF
$REPO_PATH
$PR_NUMBER
$CURRENT_SHA
EOF
```

### Integration with CI/CD

The PR Monitor can work alongside CI/CD pipelines:

1. **Trigger monitoring after CI passes:**
   - Wait for CI to complete
   - Then enable PR monitoring
   - Claude reviews after automated tests pass

2. **Monitor specific branches:**
   - Filter PRs by branch name
   - Only monitor PRs targeting main/master
   - Ignore WIP or draft PRs

### Batch Monitoring Setup

```bash
#!/bin/bash
# monitor-prs.sh - Set up monitoring for multiple PRs

REPO_PATH=$1
shift
PR_NUMBERS=("$@")

for pr in "${PR_NUMBERS[@]}"; do
  echo "Setting up monitoring for PR #$pr..."
  
  cd "$REPO_PATH"
  CURRENT_SHA=$(gh pr view "$pr" --json headRefOid --jq '.headRefOid')
  REPO_NAME=$(basename "$REPO_PATH")
  
  cat > /tmp/claude_monitor_pr_${REPO_NAME}_${pr} <<EOF
$REPO_PATH
$pr
$CURRENT_SHA
EOF
  
  echo "✓ Monitoring enabled for PR #$pr"
done

echo "All PRs now monitored."
```

Usage:
```bash
bash monitor-prs.sh /path/to/repo 1 2 3 4 5
```

## Security Considerations

### What the Plugin Can Access

- **Read access**: Repository contents, PR data, commit history
- **Network access**: GitHub API (via `gh` CLI)
- **File system**: Reads/writes state files in `/tmp`
- **Execution privileges**: Runs with your user permissions

### What the Plugin Cannot Do

- Modify code or create commits
- Push changes to repositories
- Delete branches or PRs
- Access private data outside monitored repos
- Run in the background (only active during Claude sessions)

### Best Practices

1. **Review before installing:**
   ```bash
   # Review the hook script before using
   cat ~/.claude/plugins/pr-monitor/scripts/Stop.sh
   ```

2. **Monitor trusted repositories only:**
   - Only monitor repos you have legitimate access to
   - Avoid monitoring sensitive or private repos unnecessarily

3. **Clean up regularly:**
   ```bash
   # Remove old state files
   rm /tmp/claude_monitor_pr_*
   ```

4. **Protect state files:**
   ```bash
   # State files may contain repo paths
   # Don't share or commit state files
   # They're in /tmp and world-readable by default
   ```

5. **Audit monitoring:**
   ```bash
   # Regularly check what's being monitored
   ls -la /tmp/claude_monitor_pr_*
   ```

## Limitations

### Polling-Based Detection

- **Not real-time**: Checks only when Claude stops, not continuously
- **Detection delay**: May take time between commit push and detection
- **No push notifications**: Relies on polling, not webhooks

### Session-Dependent

- **Requires Claude running**: Monitoring only active during Claude Code session
- **Stops when quit**: No background daemon or service
- **No persistence**: Must recreate monitors after system restart

### State Persistence

- **Temporary storage**: State files in `/tmp` cleared on reboot
- **Manual recreation**: Need to recreate monitoring after restart
- **No backup**: State files not backed up or synced

### API Rate Limits

- **GitHub API limits**: 5,000 requests/hour for authenticated users
- **Multiple PRs impact**: Each monitored PR = API calls per check
- **Hook frequency**: More stops = more API calls
- **Best practice**: Monitor only necessary PRs to conserve rate limit

### Repository Constraints

- **Local repositories only**: Repo must exist on local filesystem
- **Path must be valid**: State file contains absolute path
- **No auto-clone**: Must clone repo before monitoring

## Examples

### Example 1: Monitor Current Repository PR

**Scenario**: You're working on `claude-skills` and want to monitor PR #2

```bash
# In repository directory
cd ~/Projects/claude-skills

# Ask Claude:
"Monitor PR #2 in this repository for new commits"

# Claude executes:
REPO_PATH=$(pwd)  # /Users/cajias/Projects/claude-skills
PR_NUMBER=2
CURRENT_SHA=$(gh pr view 2 --json headRefOid --jq '.headRefOid')

cat > /tmp/claude_monitor_pr_claude-skills_2 <<EOF
$REPO_PATH
$PR_NUMBER
$CURRENT_SHA
EOF

# Verification:
cat /tmp/claude_monitor_pr_claude-skills_2
# Output:
# /Users/cajias/Projects/claude-skills
# 2
# a19ca15f67612f2ed5501d5cb2a65f1b7c1f94d7
```

### Example 2: Monitor Multiple PRs

**Scenario**: Monitor PRs #1, #2, and #3 simultaneously

```bash
cd ~/Projects/claude-skills

# Ask Claude:
"Monitor PRs #1, #2, and #3 in this repository"

# Creates three state files:
ls -la /tmp/claude_monitor_pr_*
# /tmp/claude_monitor_pr_claude-skills_1
# /tmp/claude_monitor_pr_claude-skills_2
# /tmp/claude_monitor_pr_claude-skills_3
```

### Example 3: Monitor External Repository

**Scenario**: Monitor PR #456 in `facebook/react`

```bash
# Clone repository
gh repo clone facebook/react
cd react

# Set up monitoring
REPO_PATH=$(pwd)
PR_NUMBER=456
CURRENT_SHA=$(gh pr view 456 --json headRefOid --jq '.headRefOid')

cat > /tmp/claude_monitor_pr_react_456 <<EOF
$REPO_PATH
$PR_NUMBER
$CURRENT_SHA
EOF

# Verify
cat /tmp/claude_monitor_pr_react_456
```

### Example 4: Stop Monitoring Specific PR

**Scenario**: Stop monitoring PR #2 but keep others active

```bash
# Remove specific state file
rm /tmp/claude_monitor_pr_claude-skills_2

# Verify others still monitored
ls -la /tmp/claude_monitor_pr_*
# /tmp/claude_monitor_pr_claude-skills_1
# /tmp/claude_monitor_pr_claude-skills_3
```

### Example 5: Stop All Monitoring

**Scenario**: Clean up all monitoring

```bash
# Ask Claude:
"Stop monitoring all PRs"

# Or manually:
rm /tmp/claude_monitor_pr_*

# Verify
ls -la /tmp/claude_monitor_pr_*
# Output: No such file or directory
```

## FAQs

### Q: How quickly does Claude detect new commits?

**A:** Detection happens when Claude Code would naturally stop/idle. The timing depends on:
- When you finish your current task
- When Claude would normally stop
- Hook execution time (~1-3 seconds per PR)

This is **not real-time**. There may be delays between commit push and detection.

### Q: Can I monitor PRs from private repositories?

**A:** Yes, as long as:
- You have read access to the repository
- GitHub CLI (`gh`) is authenticated with appropriate permissions
- The repository is cloned locally

### Q: What happens if I restart my computer?

**A:** State files in `/tmp` are typically cleared on reboot. You'll need to:
1. Recreate monitoring state files
2. Re-authenticate `gh` if needed
3. Restart Claude Code

Consider moving state files to a persistent location if needed.

### Q: Can I monitor PRs in repositories I don't own?

**A:** Yes, you can monitor any PR in any public repository or private repository where you have read access. The GitHub CLI must be authenticated and have the necessary permissions.

### Q: Does this work with GitHub Enterprise?

**A:** Yes, if:
- GitHub CLI is configured for your Enterprise instance
- You're authenticated: `gh auth login --hostname github.enterprise.com`
- API endpoints are accessible

### Q: How many PRs can I monitor simultaneously?

**A:** Technical limit: As many as you want, but practical considerations:
- Each PR adds ~1-3 seconds to hook execution
- More PRs = more GitHub API calls
- API rate limit: 5,000 requests/hour
- Recommended: 5-10 PRs maximum for best performance

### Q: Can I customize the notification message?

**A:** Yes, edit the `Stop.sh` script:

```bash
# Edit ~/.claude/plugins/pr-monitor/scripts/Stop.sh
# Find the line:
# "reason": "New commits detected in PR #${pr_number}..."

# Customize the message as needed
```

### Q: Does this work offline?

**A:** No, the plugin requires:
- Internet connectivity
- Access to GitHub API
- GitHub CLI authentication

It will fail gracefully if offline.

### Q: What if the PR is closed or merged?

**A:** The hook detects this and:
1. Sends notification about PR state change
2. Automatically removes the state file
3. Stops monitoring that PR

### Q: Can I monitor draft PRs?

**A:** Yes, draft PRs can be monitored just like regular PRs. The hook doesn't distinguish between draft and ready PRs.

## Contributing

Contributions welcome! To improve this plugin:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

**Areas for contribution:**
- Enhanced notification messages
- Additional hook types (PreToolUse, PostToolUse)
- Support for other version control systems
- Persistent state storage
- Web dashboard for monitoring
- Webhook integration for real-time notifications

## Related Documentation

- [Plugin README](./README.md) - Main plugin documentation
- [PR Monitor Skill](./skills/pr-monitor/SKILL.md) - Detailed skill instructions
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks.md) - Hook system documentation
- [GitHub CLI Manual](https://cli.github.com/manual/) - gh CLI reference

## Support

- **Issues**: [GitHub Issues](https://github.com/cajias/claude-skills/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cajias/claude-skills/discussions)
- **Documentation**: [Claude Code Docs](https://code.claude.com/docs)

## License

MIT License - See [LICENSE](../../LICENSE) file for details

## Changelog

### v1.0.0 (2025-11-20)

- Initial release
- Stop hook for automated PR monitoring
- Multi-PR support
- Auto-cleanup on merge/close
- Comprehensive documentation

---

**Author**: cajias  
**Repository**: https://github.com/cajias/claude-skills  
**Plugin Path**: `/plugins/pr-monitor/`
