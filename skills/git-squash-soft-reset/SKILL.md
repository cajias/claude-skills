---
name: git-squash-soft-reset
description: |
  Squash multiple git commits into one using soft reset - a non-interactive
  alternative to rebase. Use when: (1) you need to squash commits without an
  editor, (2) interactive rebase hangs or requires manual intervention, (3) CI/CD
  or automated contexts where git rebase -i won't work, (4) you want the fastest
  way to combine all branch commits into one. Covers soft reset technique, force
  push safety, and pre-commit hook bypass.
author: Claude Code
version: 1.0.0
date: 2026-01-27
---

# Git Squash via Soft Reset

## Problem

Interactive rebase (`git rebase -i`) requires an editor and manual intervention,
making it unsuitable for automated contexts or when you simply want to combine
all commits on a branch into one quickly.

## Context / Trigger Conditions

- Need to squash many commits (5+) into one before merging
- `git rebase -i` opens an editor that can't be automated
- Working in a CI/CD pipeline or scripted environment
- Want to clean up commit history before PR merge
- Interactive rebase hangs or times out

## Solution

### Step 1: Ensure Clean Working Directory

```bash
git status  # Should show no uncommitted changes
```

### Step 2: Soft Reset to Target Branch

```bash
# Reset to the branch you want to squash onto (usually main/master)
git reset --soft origin/main

# This moves HEAD back but keeps ALL changes staged
# All commits since origin/main are now uncommitted but staged
```

### Step 3: Create Single Commit

```bash
git commit -m "feat: comprehensive commit message describing all changes"
```

If pre-commit hooks fail due to network issues (common with CI validation hooks):

```bash
git commit --no-verify -m "feat: comprehensive commit message"
```

### Step 4: Force Push (Safely)

```bash
# Use --force-with-lease for safety (fails if remote changed)
git push --force-with-lease origin your-branch-name

# Only use --force if you're certain no one else pushed
git push --force origin your-branch-name
```

## Verification

```bash
# Verify single commit on branch
git log --oneline main..HEAD
# Should show only ONE commit

# Verify all changes are included
git diff origin/main --stat
# Should show all expected file changes
```

## Example

**Before:** 12 commits on feature branch

```text
76c02678 fix(mcp-client): use proper types
44c1fb0f fix: remove pnpm-lock.yaml
edf814e2 chore: strengthen ESLint rules
8d15084a refactor: extract handlers
39ae5f50 chore: retry CI
... (7 more commits)
```

**Commands:**

```bash
git reset --soft origin/main
git commit -m "feat(mcp-multiplexer): complete MCP protocol implementation

Key changes:
- Implement tool-level authorization
- Refactor handler.ts into focused modules
- Use proper MCP SDK types
- Fix prototype pollution vulnerability"

git push --force-with-lease origin feat/issue-82-complete-mcp-v2
```

**After:** Single clean commit

```text
13499270 feat(mcp-multiplexer): complete MCP protocol implementation
```

## Notes

- **--force-with-lease** is safer than **--force** - it fails if someone else pushed to the
  branch, preventing accidental overwrites
- **--no-verify** bypasses pre-commit hooks - use when hooks fail for environmental reasons
  (network timeouts, missing tools) but the code is known to be valid
- This technique preserves all file changes but loses individual commit messages - consider
  including a summary of key changes in the new commit message
- Works with any target branch, not just main: `git reset --soft origin/develop`
- To squash only the last N commits: `git reset --soft HEAD~N`

## Comparison with Alternatives

| Method               | Interactive | Preserves Messages | Speed  |
| -------------------- | ----------- | ------------------ | ------ |
| `git reset --soft`   | No          | No                 | Fast   |
| `git rebase -i`      | Yes         | Configurable       | Slow   |
| `git merge --squash` | No          | No                 | Medium |

## Related

- See also: git-advanced-workflows skill for rebasing techniques
