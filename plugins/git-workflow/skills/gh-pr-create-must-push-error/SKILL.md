---
name: gh-pr-create-must-push-error
description: |
  Fix for "aborted: you must first push the current branch to a remote, or
  use the --head flag" from `gh pr create` when the branch IS already
  pushed. Use when: (1) `git push -u origin <branch>` succeeded moments
  earlier, (2) `git branch -vv` shows upstream tracking is set, (3) `gh pr
  create` still rejects with the must-push message. Workaround: pass
  `--head <branch>` explicitly.
author: Claude Code
version: 1.0.0
date: 2026-04-19
---

# gh pr create "must first push" False Error

## Problem

`gh pr create` reports:

```text
aborted: you must first push the current branch to a remote, or use the --head flag
```

even though the branch has just been pushed successfully and `git branch -vv`
shows correct upstream tracking.

## Context / Trigger Conditions

- `git push -u origin <branch>` completed without error moments ago
- `git remote -v` shows the expected remote
- `git branch -vv` shows `[origin/<branch>]` upstream tracking
- Remote URL uses SSH (`git@github.com:...`) — more likely but not required
- Typically seen when pushing a freshly-created branch in the same session

`gh` appears to consult a cache of remote ref state that hasn't refreshed
between the push and the immediate `gh pr create` call.

## Solution

Pass `--head <branch-name>` explicitly:

```bash
gh pr create --head fix/my-branch --title "..." --body "..."
```

This bypasses the stale "is this branch pushed?" check and uses the named
branch directly. The PR is created against the default base branch unless
`--base` is also passed.

## Verification

The command returns the PR URL (e.g., `https://github.com/owner/repo/pull/42`)
instead of the abort message.

## Example

```bash
# Push just succeeded
git push -u origin fix/frontmatter-schema-alignment
# => * [new branch] fix/frontmatter-schema-alignment -> fix/frontmatter-schema-alignment

# Immediate PR create fails
gh pr create --title "feat: ..." --body "..."
# => aborted: you must first push the current branch to a remote, or use the --head flag

# With --head: succeeds
gh pr create --head fix/frontmatter-schema-alignment --title "feat: ..." --body "..."
# => https://github.com/owner/repo/pull/4
```

## Notes

- Alternative workarounds reported in issues: wait a few seconds and retry,
  or run `git fetch` before `gh pr create`. `--head` is the fastest and
  most reliable.
- This is not the same as the "no commits between" error — that one means
  the branch really does match the base. Read the exact error text.
- If `--head` _also_ fails with a different error (e.g., "could not determine
  base branch"), pass `--base main` explicitly too.

## References

- [gh-cli issue #1718](https://github.com/cli/cli/issues/1718) — tracks this
  class of race condition, with `--head` as the documented workaround
