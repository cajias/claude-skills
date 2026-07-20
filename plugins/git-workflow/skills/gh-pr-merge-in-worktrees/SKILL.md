---
name: gh-pr-merge-in-worktrees
description: |
  Recover from `gh pr merge --delete-branch` appearing to fail inside a git
  worktree. Use when: (1) `gh pr merge 2 --delete-branch` prints
  `failed to run git: fatal: '<branch>' is already used by worktree at
  '<path>'`, (2) you suspect the PR merged anyway despite the error,
  (3) you see a merged PR with its remote branch still present on origin,
  (4) working in any multi-worktree setup where `main` is checked out in
  a sibling worktree. Explains that `gh pr merge --delete-branch` runs
  three separable steps (API merge, local delete, remote delete) and the
  middle step failing leaves the merge state inconsistent with the
  branch-cleanup state.
author: Claude Code
version: 1.0.0
date: 2026-04-15
---

# `gh pr merge --delete-branch` in Git Worktrees

## Problem

You run `gh pr merge <N> --delete-branch` from inside a git worktree (not the main checkout) and see:

```text
failed to run git: fatal: '<base-branch>' is already used by worktree at '<path>'
```

It looks like the merge failed. It didn't. **The API merge already succeeded** — only the local
branch cleanup failed, and depending on where the failure happened, the remote branch may or may not
have been deleted too.

## Why This Happens

`gh pr merge --delete-branch` is not atomic. It runs three distinct steps:

1. **API merge** — calls GitHub's merge endpoint. Always happens first. Fast.
2. **Local branch delete** — runs `git branch -D <branch>`, which requires switching off that branch
   first. gh tries to switch to the PR's base branch (e.g. `main`).
3. **Remote branch delete** — runs `git push origin --delete <branch>`.

In a worktree setup, step 2 fails if the base branch is checked out in a sibling worktree (git
refuses to double-check-out a branch). When step 2 aborts, step 3 doesn't run — so the remote branch
is still there even though the PR is merged.

## Trigger Conditions

- You're running `gh pr merge --delete-branch` from a worktree, not the main checkout
- The error message contains `fatal: '<branch>' is already used by worktree at '<path>'`
- After the command "fails," `gh pr view <N>` shows `state: MERGED` and a non-null `mergedAt`
- After the command "fails," `git ls-remote --heads origin <branch>` still returns the branch

## Solution

**1. Verify the merge actually happened:**

```bash
gh pr view <N> --json state,mergedAt,mergedBy -q '{state, merged_at: .mergedAt, merged_by: .mergedBy.login}'
```

If `state: MERGED`, the merge succeeded — don't retry it.

**2. Clean up the remote branch manually:**

```bash
git push origin --delete <branch-name>
```

**3. Leave the local branch alone (usually).** The current worktree is sitting on it. Deleting it
in-place would require checking out some other branch first, which you may not want to do. Options:

- **Leave it** — it's harmless. Next `git fetch --prune` won't remove it (only remote-tracking refs
  get pruned). It'll just sit locally.
- **Remove the whole worktree when done:** `git worktree remove <worktree-path>`. If the worktree has
  dirty files, add `--force`.
- **Switch branches in the worktree, then delete:** `git checkout <some-other-branch> && git branch -D
  <merged-branch>`. Only works if another branch exists locally that isn't checked out elsewhere.

## Verification

After cleanup, confirm:

```bash
# Merge state
gh pr view <N> --json state,mergedAt

# Remote branch is gone
git ls-remote --heads origin <branch-name>  # should return nothing

# origin/main advanced
git fetch origin && git log --oneline origin/main -3
```

## Example

Concrete session:

```bash
$ gh pr merge 2 --merge --delete-branch
failed to run git: fatal: 'main' is already used by worktree at '~/Projects/workspace/second-brain-plugins'

$ gh pr view 2 --json state,mergedAt
{"mergedAt":"2026-04-15T20:39:26Z","state":"MERGED"}
# ^ merge DID succeed

$ git ls-remote --heads origin docs/my-branch
19594fd921af7375d4fa032ae371f983b46c4fd7    refs/heads/docs/my-branch
# ^ remote branch still present

$ git push origin --delete docs/my-branch
To github.com:owner/repo.git
 - [deleted]         docs/my-branch
# ^ cleaned up
```

## Notes

- Avoid this class of failure entirely: **don't pass `--delete-branch` from a worktree**. Merge
  without it, then delete the remote branch in a separate command. This makes the three steps explicit
  and recoverable:

  ```bash
  gh pr merge <N> --merge            # step 1: API merge
  git push origin --delete <branch>  # step 3: remote cleanup
  # step 2 (local) handled separately or skipped
  ```

- GitHub's web UI has a "Delete branch" button on the merged PR page as a fallback recovery path —
  same effect as `git push origin --delete`.
- The "1 uncommitted change" warning from `gh pr create` is unrelated — that's just gh noting you have
  dirty working-tree files the PR won't include. It doesn't block PR creation or merge.
- If you hit this repeatedly, consider using `--merge-queue` or setting a repo auto-delete-branch
  setting (`Settings → General → Automatically delete head branches`) so the remote cleanup happens
  server-side after merge and isn't coupled to local git operations at all.

## References

- gh pr merge: <https://cli.github.com/manual/gh_pr_merge>
- Git worktree docs: <https://git-scm.com/docs/git-worktree>
- GitHub "auto-delete head branches": <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches>
