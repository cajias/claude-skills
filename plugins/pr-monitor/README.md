# PR Monitor Plugin

Automated GitHub pull request monitoring for Claude Code. Automatically resumes Claude when new
commits are detected.

> 📖 **New to this plugin?** See the [Complete Usage Guide](./USAGE-GUIDE.md) for step-by-step
> instructions, troubleshooting, and examples.

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

**Test hook manually:**

```bash
echo '{"stop_hook_active": false}' | bash ~/.claude/plugins/pr-monitor/scripts/Stop.sh
```

### PR Not Detected

**Verify state file exists:**

```bash
ls -la ~/.claude/pr-monitor/claude_monitor_pr_*
```

**Check state file format:**

```bash
cat ~/.claude/pr-monitor/claude_monitor_pr_REPO_PR
# Should have 3 lines
```

**Test GitHub CLI:**

```bash
gh pr view PR_NUMBER --json headRefOid,commits
```

**Check authentication:**

```bash
gh auth status
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
# Ask Claude:
"Monitor PR #123 in owner/repo"

# Claude:
# 1. Clones repo (if not local)
# 2. Creates state file
# 3. Enables monitoring
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
├── README.md                 # This file
└── USAGE-GUIDE.md            # Detailed usage guide and troubleshooting
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

- 📘 [**Complete Usage Guide**](./USAGE-GUIDE.md) - Comprehensive how-to guide with examples
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
- Comprehensive usage guide with troubleshooting and examples
