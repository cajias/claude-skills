---
name: git-squash-merge-tree-hash-diagnosis
description: |
  Diagnose and clean up a local branch that appears "N commits ahead of main"
  after its PR was squash-merged on GitHub, but whose work is actually fully
  integrated. Use when: (1) `git log main..HEAD` shows multiple commits but the
  matching PR is closed/merged on GitHub; (2) `git pull --ff-only` on `main`
  refuses with "Not possible to fast-forward" because local `main` accumulated
  orphan commits that were absorbed by the squash; (3) `git rebase main`
  would replay all branch commits and conflict because the squash commit's
  patch is the SUM of the branch's commits, not equivalent to any individual
  one; (4) `git log --cherry-mark --left-right main...HEAD` shows every branch
  commit as `>` (unique to HEAD) even though the work is in main; (5) you
  need to decide between "rebase + new PR" vs "delete merged branch" and the
  commit graph is misleading. The canonical signal is tree-hash equality:
  `git rev-parse HEAD^{tree}` vs `git rev-parse origin/main^{tree}` — if
  equal, every file is byte-identical and the branch is fully merged
  regardless of what the commit graph says. Covers the diagnostic, the safe
  cleanup (`git reset --hard origin/main` to drop orphan local-main commits
  whose content is in the squash), and why naïve `git rebase` is the wrong
  tool here.
author: Claude Code
version: 1.0.0
date: 2026-05-09
---

# Git squash-merge tree-hash diagnosis

## Problem

You finish a feature branch, open a PR, GitHub squash-merges it. Days later
you check the branch and see:

```text
$ git log main..HEAD --oneline | wc -l
19
```

Nineteen commits ahead of main. But the PR is closed and merged. Are these
ghost duplicates of the squash, or genuinely new post-merge work that didn't
make it into the PR?

The commit graph cannot tell you. After a squash merge, NONE of the branch's
individual commits are reachable from `main` — `main` only contains a single
new commit (the squash) whose patch is the SUM of all branch commits. So:

- `git log main..HEAD` reports all 19 as "ahead."
- `git log --cherry-mark --left-right main...HEAD` marks every branch commit
  as `>` (unique to HEAD), because no individual commit's patch matches the
  squash's combined patch.
- `git rebase main` would attempt to replay all 19 commits, hitting conflicts
  on every one because their content was already absorbed.
- `git pull --ff-only` on `main` itself may refuse if local `main` had work
  applied directly (e.g. design doc commits) that the squash also absorbed.

The naïve interpretation — "I have 19 commits to merge!" — is wrong. The
work is already in `main`. You're looking at ghosts.

## Context / Trigger Conditions

Diagnose with this skill when ALL the following hold:

- A PR for the branch was squash-merged on GitHub (verify with
  `gh pr list --head <branch> --state merged --json mergedAt,number`).
- `git log <main>..HEAD` shows ≥1 commit on the branch.
- `git rebase main` looks like it would do something, but you suspect those
  commits are duplicates.
- Optionally: local `main` is divergent from `origin/main`
  (`git pull --ff-only` refuses with "Not possible to fast-forward").

ALSO use this skill defensively before any of:

- Force-pushing a "rebased" branch that might no-op or destroy state.
- Cherry-picking commits from a branch you're unsure are merged.
- Claiming a branch has "pending work" in a status report.

## Solution

### Step 1 — Run the tree-hash check

```bash
git rev-parse HEAD^{tree}            # tree of branch tip
git rev-parse origin/main^{tree}     # tree of merged main
```

The `^{tree}` peel operator returns the SHA-1 of the tree object — a hash
of every file's content and directory structure. If two refs share a tree
hash, every file in the working copy is byte-for-byte identical. This bypasses
commit history entirely.

**If hashes match**: the branch is fully merged. Every file the branch
"adds" is already in `main`. Proceed to Step 2 (cleanup).

**If hashes differ**: there is real delta. Investigate with
`git diff origin/main..HEAD --stat` (note: two-dot, not three-dot). Three-dot
shows the merge-base diff, which is misleading after a squash; two-dot shows
literal current-state difference.

### Step 2 — Reconcile a divergent local `main`

If `git checkout main && git merge --ff-only origin/main` refuses with
"Not possible to fast-forward," local `main` has commits absent from
`origin/main`. After a squash merge this is normal — you may have committed
design docs or fixups directly to local `main` before the PR landed, and
those commits' CONTENT is in the squash even though their commit objects
are not in `origin/main`.

Verify the orphan commits' content is in `origin/main`:

```bash
# What commits does local main have that origin/main lacks?
git log origin/main..main --oneline

# For each orphan commit's files, verify they exist in origin/main:
git show <orphan-sha> --name-only
git show origin/main:<file-from-above>   # should print content, not error
```

If verified, reset local main to match origin:

```bash
git reset --hard origin/main
```

The orphan commit objects remain in the reflog (`git reflog show main`) for
~90 days — recoverable if you were wrong.

### Step 3 — Delete the merged branch

```bash
# Local: -d (lowercase) refuses if not merged. It will accept here because
# the branch IS merged to its remote tracking ref, even if not to HEAD.
git branch -d <branch>

# Remote (only if you have permission and GitHub didn't auto-delete):
git push origin --delete <branch>
```

If `git branch -d` refuses with "not fully merged," that's a sign the
tree-hash diagnosis was wrong — there's content on the branch that's NOT
in `origin/main`. Stop and investigate before forcing with `-D`.

## Verification

After cleanup, confirm:

```bash
git rev-parse main^{tree}            # local main tree
git rev-parse origin/main^{tree}     # origin main tree
# Should be equal

git branch --list <branch>           # local branch
git ls-remote origin <branch>        # remote branch
# Both should be empty
```

`git status` should be clean (modulo unrelated untracked files).

## Example (real session)

Branch: `apm-marketplace-phase-1`. PR #32 merged via squash on 2026-05-08.

```bash
$ git log main..HEAD --oneline | wc -l
19

$ git log --cherry-mark --left-right main...HEAD --oneline | head -3
> 6e33093 docs: add MD040 markdownlint gotcha
> e2b1eb8 feat: add CC plugin/APM marketplace gotchas plugin
> 2a4b0dd docs: record Phase 2 composition strategy
# All 19 marked '>' — cherry-mark says no duplicates exist.

$ gh pr list --head apm-marketplace-phase-1 --state all --json state,mergedAt
[{"mergedAt":"2026-05-08T18:53:49Z","state":"MERGED"}]
# But PR is merged. Ghosts or real work?

$ git rev-parse HEAD^{tree}
d675a082c52cb1cc03f7c7a5c931b8d9e6ba5155
$ git rev-parse origin/main^{tree}
d675a082c52cb1cc03f7c7a5c931b8d9e6ba5155
# Identical. Branch is fully merged. The 19 commits are squash-ghosts.

$ git checkout main && git merge --ff-only origin/main
fatal: Not possible to fast-forward, aborting.
# Local main has orphan commits.

$ git log origin/main..main --oneline
c394072 docs: APM marketplace Phase 1 implementation plan
354110f docs: APM marketplace + OpenProse programs design
# These orphan commits' files exist in origin/main (verified via git show).

$ git reset --hard origin/main
HEAD is now at b16afdf APM marketplace migration (Phase 1) (#32)

$ git branch -d apm-marketplace-phase-1
warning: deleting branch 'apm-marketplace-phase-1' that has been merged to
         'refs/remotes/origin/apm-marketplace-phase-1', but not yet merged to HEAD.
Deleted branch apm-marketplace-phase-1 (was 6e33093).

$ git push origin --delete apm-marketplace-phase-1
 - [deleted]         apm-marketplace-phase-1
```

The warning "merged to remote tracking ref but not to HEAD" is the
fingerprint of a squash-merged branch — git knows the remote considers it
merged (because the PR closed it) but can't see any individual commit's
patch reflected as-is in HEAD's history. That warning IS the success
signal here.

## Notes

- **Why `git rebase` is the wrong tool**: rebase replays each commit's patch
  onto the new base. Each branch commit's individual patch is NOT in
  `origin/main` (only their sum is). So rebase will try to apply each one
  and conflict against content the squash already placed there. The result
  is hours of conflict resolution that produces a no-op.

- **Why `--cherry-mark` doesn't help**: cherry-mark uses `git patch-id` to
  detect equivalent patches. A squash commit's patch-id matches none of the
  individual branch commits because their patches were combined. Cherry-mark
  is correct that no individual patch is in main; it just doesn't answer
  the question you actually have, which is "is the _content_ in main."

- **Why `git diff origin/main...HEAD` (three-dot) misleads**: three-dot
  diff shows changes from the merge-base of the two refs, not the literal
  diff between them. After a squash merge, the merge-base is the parent of
  the squash commit, so three-dot includes the entire branch's work even
  though it's now also in main. Use two-dot (`origin/main..HEAD`) for the
  literal current-state diff.

- **Tree-hash is stronger than commit-hash for "are these the same state"
  questions**. Two different commit histories can produce the same tree.
  When you want "is the working copy state equivalent," ask the tree.

- **The reflog is your safety net**. `git reset --hard` looks scary but the
  pre-reset commit stays in `git reflog show main` for ~90 days (controlled
  by `gc.reflogExpire`, default 90d). Recover with
  `git reset --hard <reflog-sha>`. This makes the cleanup safe to do
  without ceremony.

- **Related but different**: see `gh-pr-merge-in-worktrees` for the case
  where `gh pr merge --delete-branch` partially fails inside a worktree.
  That's about the merge tool's three-step sequence; this skill is about
  the post-merge state interpretation.

## References

- Git's `^{tree}` peel operator:
  <https://git-scm.com/docs/gitrevisions#Documentation/gitrevisions.txt-emltrevgtemegemHEADv1510em>
- `git diff` two-dot vs three-dot semantics:
  <https://git-scm.com/docs/git-diff#Documentation/git-diff.txt-emgitdiffemltcommitgtltcommitgt>
- GitHub squash-merge mechanics:
  <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges#squash-and-merge-your-commits>
