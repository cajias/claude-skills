---
name: parallel-subagent-git-worktree-race
description: |
  Fix/avoid HEAD+index corruption when running parallel Claude Code subagents
  (Agent tool) that each mutate git (checkout/rebase/reset) in what you THOUGHT
  were isolated worktrees. Use when: (1) you spawned 2+ agents with
  isolation:"worktree" to rebase/merge/commit different branches concurrently;
  (2) an agent reports "I am NOT in an isolated worktree" — `git rev-parse
  --git-dir` and `--git-common-dir` both point at the same `.git`, `git worktree
  list` shows a SINGLE worktree, and `--show-toplevel` is the main checkout;
  (3) a rebase suddenly appears to be running on the WRONG branch, or the reflog
  shows a branch reset/checkout you didn't issue during your run; (4) two agents'
  `git checkout` calls swap HEAD/index underneath each other. Covers detection,
  the serialize-to-one-owner recovery, and a ref-recheck guard pattern.
author: Claude Code
version: 1.0.0
date: 2026-06-19
---

# Parallel Subagent Git Worktree Race

## Problem

The Claude Code Agent tool's `isolation: "worktree"` option is supposed to give
each spawned agent its own git worktree (separate working dir + HEAD + index,
shared object store). In practice it can **silently fail to create a separate
worktree** — the agents end up running in the _same_ (main) checkout. When two
such agents each run `git checkout <their-branch>` and `git rebase`, they share
one HEAD and one index: agent B's checkout switches HEAD out from under agent A,
so A's subsequent `git rebase origin/main` rebases the WRONG branch, conflict
markers from one task land in the other, and pushes/aborts can clobber the
other agent's work. This corrupts both tasks even though each agent's own
commands look correct in isolation.

Cause of the fallback is not always visible to the agent (a likely trigger is
the sandbox denying `git worktree add`, per the using-git-worktrees skill's
"sandbox fallback: work in place"). Do not assume the option worked.

## Context / Trigger Conditions

- You spawned 2+ agents with `isolation: "worktree"` to do git-mutating work
  (rebase, merge, commit, reset, branch creation) on DIFFERENT branches at once.
- An agent reports any of:
  - `git rev-parse --git-dir` == `git rev-parse --git-common-dir` (both `.git`)
    AND `git worktree list` shows only ONE worktree AND `git rev-parse
--show-toplevel` is the main repo path → it is NOT isolated.
  - A `git rebase` is in progress on a branch the agent never checked out.
  - The branch reflog shows a `checkout:`/`reset:`/`rebase` entry at a timestamp
    the agent didn't act, i.e. another process moved the ref mid-run.
- Symptoms in the working tree: unexpected conflict files, HEAD on a surprising
  branch, "interactive rebase already in progress" when you started none.

## Solution

1. **Freeze.** Tell every git-mutating agent to STOP immediately — no
   `git rebase --abort`/`--continue`, no checkout/reset/commit/push — and to
   report the exact commands it ran + current `git status`. A wrong recovery
   move is worse than pausing. (`TaskStop` may not accept the agent's
   `name@session` id; coordinate via `SendMessage` instead.)
2. **Serialize to a single owner.** Pick ONE agent to be the sole owner of the
   working tree. Explicitly RELEASE all others ("cease all git activity
   permanently; stay idle; decline any prompt to resume git"). You cannot rely
   on killing them — a released-but-alive agent can still wake and re-point a
   branch, so the owner must be defended by the guard below.
3. **Recover a clean baseline (owner only):** `git rebase --abort` if one is in
   progress; `git checkout -f <safe-branch>`; `git fetch origin --prune`; then
   reset each target branch to its remote with
   `git checkout -B <branch> origin/<branch>` (this discards any unverified work
   a runaway agent committed — usually what you want). Verify `git status` clean
   and local refs == origin refs before proceeding.
4. **Redo the work one branch at a time** in the single owner. Do NOT
   re-parallelize in the same tree.
5. **Arm a ref-recheck guard** around every mutation: capture
   `git rev-parse <branch>` immediately BEFORE and AFTER each step (and before
   any push). If the ref is anything other than what the owner's own command
   set, HALT and report — another agent woke up. This is what catches a late
   wakeup before it corrupts the redo.

## Prevention

- For genuinely parallel git-mutating agents, **verify real isolation** inside
  each agent first (run the `git rev-parse --git-dir` vs `--git-common-dir` +
  `git worktree list` check) and bail to the orchestrator if not isolated —
  rather than trusting `isolation: "worktree"`.
- If isolation can't be guaranteed, **serialize from the start**: one owner does
  branch A fully, then branch B. Read-only review/inspection agents are safe to
  parallelize as long as they use `git show origin/<branch>:<path>` and
  `git diff origin/main...origin/<branch>` and never checkout or touch the index.

## Verification

- `git worktree list` shows distinct paths per agent IF you intended isolation.
- After serialized recovery: each branch's `git diff --stat origin/main...HEAD`
  shows only its own intended change; tests/lint green; the ref-recheck guard
  never tripped (or tripped and you halted before damage).

## Example

Two agents asked to rebase `feat/x` and `fix/y` with `isolation:"worktree"`.
Agent for `feat/x` reports: `--git-dir` and `--git-common-dir` both `.git`,
`git worktree list` shows one worktree; reflog shows `fix/y` was reset at a time
it didn't act → shared-tree race confirmed. Orchestrator: STOP both → release
the `fix/y` agent → make the `feat/x` agent sole owner → it aborts the stray
rebase, resets both branches to origin, rebases `feat/x` (push), then `fix/y`
(push), re-checking `git rev-parse` before each mutation. Both land cleanly;
the released agent's unverified commit is intentionally discarded.

## Notes

- Read-only git (`show`, `diff`, `log`, `rev-parse`, `cat-file`, `fetch`) is
  concurrency-safe in a shared tree; only HEAD/index/worktree-mutating commands
  race. Reviews and inspections can stay parallel.
- Working-tree file contents reflect whatever branch HEAD currently points at —
  in a contested tree that's unreliable; inspect specific revs with
  `git show <ref>:<path>` instead of reading files.
- `--force-with-lease` to push a rebased PR branch is safe when the lease is
  against the untouched `origin/<branch>`; it does not protect against a peer
  agent rewriting your LOCAL ref, which is why the ref-recheck guard exists.
- Related: using-git-worktrees (native vs fallback worktree creation),
  gh-pr-merge-in-worktrees, git-deadlock-plumbing-recovery.
