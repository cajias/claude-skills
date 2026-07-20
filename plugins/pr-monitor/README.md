# PR Monitor Plugin

Automated GitHub pull request monitoring for Claude Code. Automatically resumes Claude when new
commits are detected.

## Overview

This plugin provides:

- **Stop Hook**: Automatically checks PRs when Claude would idle
- **PR Monitor Skill**: Instructions for setting up and managing PR monitoring
- **Auto-Resume**: Claude automatically continues when new commits detected

## Features

- 🔄 **Automatic PR monitoring** - No manual checking needed
- ⚡ **Auto-resume on updates** - Claude continues when new commits pushed
- 🎯 **Multi-PR support** - Monitor multiple PRs simultaneously
- 🧹 **Auto-cleanup** - Stops monitoring when PR is merged/closed
- 📊 **Smart detection** - Compares commit SHAs to detect changes

## Installation

### Via Plugin Manager (Recommended)

```bash
claude plugin marketplace add cajias/claude-skills
claude plugin install pr-monitor@claude-skills
```

After installation, restart Claude Code for the hook to activate.

### Manual Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/cajias/claude-skills.git
   cd claude-skills
   ```

2. Copy to Claude plugins directory:

   ```bash
   cp -r plugins/pr-monitor ~/.claude/plugins/
   ```

3. Restart Claude Code

## Usage

### Quick Start

Ask Claude to monitor a PR:

```text
Monitor PR #2 in the current repository for new commits
```

Claude will:

1. Verify the PR exists
2. Get current commit SHA
3. Create monitoring state file
4. Automatically resume when new commits are detected

### Manual Setup

```bash
# Navigate to repository
cd /path/to/repository

# Get current PR commit
CURRENT_SHA=$(gh pr view 2 --json headRefOid --jq '.headRefOid')

# Create state file
cat > ~/.claude/pr-monitor/claude_monitor_pr_$(basename $(pwd))_2 <<EOF
$(pwd)
2
$CURRENT_SHA
EOF
```

### Stop Monitoring

Ask Claude:

```text
Stop monitoring PR #2
```

Or manually:

```bash
rm ~/.claude/pr-monitor/claude_monitor_pr_REPO_PR
```

## How It Works

### Architecture

```text
User works on tasks
       ↓
Claude finishes task → Would normally stop
       ↓
Stop Hook triggers → Checks ~/.claude/pr-monitor/claude_monitor_pr_* files
       ↓
Queries GitHub API → Compares commit SHAs
       ↓
If new commits → Returns {"decision": "block"}
       ↓
Claude auto-resumes → Reviews changes and provides feedback
```

### State File Format

Files stored in `~/.claude/pr-monitor/claude_monitor_pr_<repo-name>_<pr-number>`:

```text
Line 1: /path/to/repository
Line 2: PR_NUMBER
Line 3: LAST_COMMIT_SHA
```

Example:

```text
/home/user/Projects/claude-skills
2
a19ca15f67612f2ed5501d5cb2a65f1b7c1f94d7
```

### Hook Behavior

The Stop hook:

- Runs when Claude Code would naturally stop/idle
- Checks all state files in `~/.claude/pr-monitor/claude_monitor_pr_*`
- Queries GitHub for each monitored PR
- Compares current commit SHA with last known SHA
- If different:
  - Updates state file with new SHA
  - Returns `{"decision": "block", "reason": "..."}`
  - Claude auto-resumes with that reason as prompt

## Requirements

- **GitHub CLI (gh)**: v2.0.0 or higher
  - Install: <https://cli.github.com/>
  - Must be authenticated: `gh auth login`
- **jq**: For JSON parsing
  - macOS: `brew install jq`
  - Linux: `apt-get install jq`
- **Claude Code**: Latest version

## Configuration

The Stop hook auto-registers from `hooks/hooks.json` on install. No `settings.json` edits are
needed.

Disable for specific project:

```json
{
  "disableAllHooks": true
}
```

## Limitations

### Polling-Based

- Not real-time push notifications
- Checks happen when Claude stops, not continuously
- May have delays between commit and detection

### Requires Claude Running

- Monitoring only active during Claude Code session
- Stops when you quit Claude Code
- No background daemon

### API Rate Limits

- Stop hook queries GitHub each time it runs
- Multiple monitored PRs = more API calls
- GitHub API limit: 5,000 requests/hour
- Be mindful of rate limits with many PRs

### Repository Constraints

- Repo must exist on the local filesystem — no auto-clone
- State file line 1 must be a valid absolute path
- If the path is gone when the hook runs, the state file is deleted and monitoring stops

## Troubleshooting

### Hook Not Triggering

**Check plugin installed:**

```bash
ls -la ~/.claude/plugins/pr-monitor
```

**Check hooks registered:**

```bash
cat ~/.claude/plugins/pr-monitor/hooks/hooks.json
```

**Check the script is executable:**

```bash
ls -l ~/.claude/plugins/pr-monitor/scripts/Stop.sh
# Should show: -rwxr-xr-x
```

**Test hook manually:**

```bash
echo '{"stop_hook_active": false}' | bash ~/.claude/plugins/pr-monitor/scripts/Stop.sh

# With trace output when the above is silent:
echo '{"stop_hook_active": false}' | bash -x ~/.claude/plugins/pr-monitor/scripts/Stop.sh
```

If the hook still never runs: restart Claude Code completely, and check that
`.claude/settings.json` does not set `disableAllHooks: true`.

### PR Not Detected

**Verify state file exists:**

```bash
ls -la ~/.claude/pr-monitor/claude_monitor_pr_*
```

**Check state file format:**

```bash
cat ~/.claude/pr-monitor/claude_monitor_pr_REPO_PR
# Should have exactly 3 lines: repo path, PR number, last commit SHA
```

**Test GitHub CLI:**

```bash
gh pr view PR_NUMBER --json headRefOid,state,commits
```

**Check authentication:**

```bash
gh auth status
```

### State File Issues

**Not found** - check the repo name spelling in the filename and that the file is
in `~/.claude/pr-monitor/`. Note the hook deletes the state file if line 1 is not an
existing directory.

**Wrong format** - recreate it:

```bash
REPO_PATH=/path/to/repo
PR_NUMBER=123
CURRENT_SHA=$(cd "$REPO_PATH" && gh pr view "$PR_NUMBER" --json headRefOid --jq '.headRefOid')

cat > ~/.claude/pr-monitor/claude_monitor_pr_$(basename "$REPO_PATH")_${PR_NUMBER} <<EOF
$REPO_PATH
$PR_NUMBER
$CURRENT_SHA
EOF
```

**Unreadable** - `chmod 644 ~/.claude/pr-monitor/claude_monitor_pr_*`

### GitHub API Issues

**Rate limit exceeded:**

```bash
gh api rate_limit   # resets hourly
```

**Authentication expired:** re-run `gh auth login`.

**Permission denied:** confirm you can reach the repo at all with
`gh repo view OWNER/REPO`.

**Hook timing out:** check network connectivity and reduce the number of
monitored PRs — each one costs an API round-trip per stop.

### Claude Not Auto-Resuming

**Check hook output** - it must emit JSON with `"decision": "block"`:

```bash
echo '{"stop_hook_active": false}' | bash ~/.claude/plugins/pr-monitor/scripts/Stop.sh
```

**Verify the SHA actually changed:**

```bash
gh pr view PR_NUMBER --json headRefOid --jq '.headRefOid'
sed -n '3p' ~/.claude/pr-monitor/claude_monitor_pr_REPO_PR
```

**Check the PR is still open** - a merged or closed PR blocks once, then
deletes its own state file:

```bash
gh pr view PR_NUMBER --json state --jq '.state'
```

### Multiple Triggers

**List all monitors:**

```bash
ls -la ~/.claude/pr-monitor/claude_monitor_pr_*
```

**Remove specific monitor:**

```bash
rm ~/.claude/pr-monitor/claude_monitor_pr_REPO_PR
```

**Clear all monitors:**

```bash
rm ~/.claude/pr-monitor/claude_monitor_pr_*
```

## Security Considerations

- Hook executes with your user privileges
- Reads PR state files from `~/.claude/pr-monitor`
- Uses `gh` CLI with your GitHub authentication
- Does NOT modify code or create commits
- Read-only access to repositories

**Best Practices:**

- Review hook script before installation
- Monitor only trusted repositories
- Clean up state files when done
- Don't store sensitive data in state files

## Examples

### Monitor Current Repository PR

```bash
# Ask Claude:
"Monitor PR #5 in this repository"

# Claude creates:
# ~/.claude/pr-monitor/claude_monitor_pr_myrepo_5
```

### Monitor External Repository PR

```bash
# Clone it first — the hook needs a local path
gh repo clone owner/repo
cd repo

# Then ask Claude:
"Monitor PR #123 in this repository"
```

### Monitor Multiple PRs

```bash
# Ask Claude:
"Monitor PRs #1, #2, and #3 in this repository"

# Claude creates:
# ~/.claude/pr-monitor/claude_monitor_pr_myrepo_1
# ~/.claude/pr-monitor/claude_monitor_pr_myrepo_2
# ~/.claude/pr-monitor/claude_monitor_pr_myrepo_3
```

### Stop All Monitoring

```bash
# Ask Claude:
"Stop monitoring all PRs"

# Or manually:
rm ~/.claude/pr-monitor/claude_monitor_pr_*
```

## Advanced Usage

### Custom State File Location

State files live in `~/.claude/pr-monitor/`, set by the `STATE_DIR` variable near
the top of `Stop.sh`. To move them, edit that variable — the script creates the
directory and scans it for `claude_monitor_pr_*`.

### Batch Monitoring Setup

```bash
#!/bin/bash
# monitor-prs.sh /path/to/repo 1 2 3
REPO_PATH=$1
shift

cd "$REPO_PATH"
REPO_NAME=$(basename "$REPO_PATH")

for pr in "$@"; do
  CURRENT_SHA=$(gh pr view "$pr" --json headRefOid --jq '.headRefOid')
  cat > ~/.claude/pr-monitor/claude_monitor_pr_${REPO_NAME}_${pr} <<EOF
$REPO_PATH
$pr
$CURRENT_SHA
EOF
  echo "✓ Monitoring PR #$pr"
done
```

## FAQ

**How quickly are new commits detected?** Only when Claude Code would otherwise
stop or idle — not in real time. Each monitored PR adds roughly 1-3 seconds to
that check.

**Can I monitor private repos?** Yes, if `gh` is authenticated with read access
and the repo is cloned locally.

**Does it work with GitHub Enterprise?** Yes, once `gh` is pointed at your
instance: `gh auth login --hostname github.enterprise.com`.

**How many PRs at once?** No hard limit, but each costs an API call per check
against a 5,000 requests/hour budget. 5-10 is a comfortable ceiling.

**Can I change the notification text?** Yes — edit the `"reason"` string in
`scripts/Stop.sh`.

**Does it work offline?** No. It needs the GitHub API, and fails quietly without it.

**What happens when the PR merges or closes?** The hook blocks once with a
state-change notice, then deletes the state file and stops monitoring.

**Can I monitor draft PRs?** Yes — the hook does not distinguish draft from ready.

## Development

### Plugin Structure

```text
pr-monitor/
├── .claude-plugin/
│   └── plugin.json           # Metadata
├── hooks/
│   └── hooks.json            # Hook registration
├── scripts/
│   └── Stop.sh               # Stop hook script
├── skills/
│   └── pr-monitor/
│       └── SKILL.md          # Skill instructions
└── README.md                 # This file
```

### Testing

Test the hook manually:

```bash
# Create test state file
cat > ~/.claude/pr-monitor/claude_monitor_pr_test_1 <<EOF
/path/to/test/repo
1
abc123def456
EOF

# Test hook
echo '{"stop_hook_active": false}' | bash scripts/Stop.sh

# Clean up
rm ~/.claude/pr-monitor/claude_monitor_pr_test_1
```

### Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## License

MIT License - see the repository LICENSE.

## Author

cajias

## Documentation

- 📋 [**PR Monitor Skill**](./skills/pr-monitor/SKILL.md) - Detailed skill instructions
- 🔧 [**Stop Hook Script**](./scripts/Stop.sh) - Hook implementation

## Support

- **Issues**: <https://github.com/cajias/claude-skills/issues>
- **Documentation**: <https://code.claude.com/docs/en/hooks.md>
- **GitHub CLI**: <https://cli.github.com/manual/>

## Related

- [GitHub Issue Grooming Skill](../../skills/github-issue-grooming/)
- [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide.md)
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins.md)

## Changelog

### v1.0.0 (2025-11-20)

- Initial release
- Stop hook for PR monitoring
- PR monitor skill
- Multi-PR support
- Auto-cleanup on merge/close
