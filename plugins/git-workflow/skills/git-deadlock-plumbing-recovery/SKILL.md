---
name: git-deadlock-plumbing-recovery
description: |
  Diagnose and recover git operations that HANG / DEADLOCK at ~0% CPU on macOS
  (APFS) — git commit, git reset, git gc/repack, git push, and even git status
  never returning. Use when: (1) a git write op "takes forever" / never finishes;
  (2) `ps` shows the git process in interruptible sleep (STAT S/SN) with CPU TIME
  frozen across samples; (3) a stale 0-byte `.git/index.lock` is present;
  (4) `git push` stalls in "Counting objects" / `git repack -ad` hangs with an
  empty pack dir; (5) `git count-objects -v` shows thousands of loose objects and
  `packs: 0`; (6) the volume is near-full (`df` ~95%+); (7) `.git/index` went
  missing after an interrupted git op. Covers the plumbing-commit workaround
  (write-tree → commit-tree → update-ref) that bypasses the hanging working-tree
  refresh and hooks, index recovery via read-tree, and the real fixes.
author: Claude Code
version: 1.0.0
date: 2026-06-13
---

# Git Operations Hang / Deadlock — Plumbing Recovery

## Problem

Routine git operations stall indefinitely and never return: `git commit`,
`git reset`, `git gc`, `git repack`, `git push`, even `git status`. The process
is not crashing or erroring — it is parked, blocked on I/O, consuming ~0% CPU.

## Context / Trigger Conditions

Suspect this when one or more hold:

- A git command appears to "take forever" / hangs with no output.
- `ps -axo pid,stat,etime,time,command | grep '[g]it'` shows the git writer with
  **STAT `S` or `SN`** (interruptible sleep) and **CPU TIME frozen** when sampled
  twice a few seconds apart (no growth ⇒ blocked, not computing).
  (Filter out `gitstatusd` and false matches like "Logi**t**ech".)
- A **0-byte `.git/index.lock`** exists and its mtime does not advance.
- `git push` stalls inside **"Counting objects"**; `git repack -a -d` also hangs
  and leaves the pack dir empty. Both use `git pack-objects`.
- `git count-objects -vH` shows **thousands of loose objects, `packs: 0`**.
- `df -h /System/Volumes/Data` (macOS) shows the volume **near-full (~95%+)**.
- After an interrupted/killed git op, **`.git/index` is missing** (only a 0-byte
  `index.lock` remains).

## Root Cause

Filesystem I/O contention. `git pack-objects` must read every loose object, and
the index-refresh `stat()` scan must walk the whole working tree — both stall on a
pressured / near-full APFS volume. It is frequently **triggered by a single large
commit/add** (e.g. vendoring a big data directory) that simultaneously balloons
the loose-object count and the working-tree scan. Note: absolute free space can
look fine (e.g. 19 GB free) yet git still stalls — **percent-full + APFS
contention matters more than raw bytes** for this symptom. A hanging pre-commit /
commit-msg hook is a separate possible cause of `git commit` specifically.

## Solution

### 1. Confirm it's a deadlock, not slow work

```bash
ps -axo pid,stat,etime,time,command | grep '[g]it' | grep -v gitstatusd
sleep 4
ps -axo pid,stat,etime,time,command | grep '[g]it' | grep -v gitstatusd  # TIME unchanged ⇒ stuck
git count-objects -vH        # thousands loose / packs: 0
df -h /System/Volumes/Data   # near-full?
```

SSH to the remote being fine confirms the hang is **local** (pack-objects/refresh),
not the network.

### 2. Clear the stuck process + stale lock

```bash
kill <pid>        # the parked git writer; kill -9 if needed. NEVER kill gitstatusd.
rm -f .git/index.lock
```

If git ran inside an agent/subprocess, stop that owner first so it can't race you.

### 3. If `.git/index` is missing, rebuild it WITHOUT scanning the working tree

```bash
git read-tree HEAD      # repopulates the index from HEAD's tree; no working-tree scan
```

Do **not** use `git reset` to recover — it refreshes the index by scanning the
working tree and will re-hang.

### 4. Create the commit straight from the index via plumbing

This is the key workaround. It bypasses both the hanging working-tree refresh and
all hooks (`commit-tree` runs no hooks):

```bash
tree=$(git write-tree)                                   # tree from the index, no WT scan
commit=$(git commit-tree "$tree" -p HEAD -m "your message")
git update-ref refs/heads/<branch> "$commit"             # move the branch
```

Stage changes with index-only ops that don't scan the working tree
(`git rm --cached`, `git update-index`) where possible.

### 5. Always bound git with `timeout`

Wrap every git call (`timeout 120 git ...`). If it exits 124, **escalate / change
approach** — do not retry the same command in a loop.

### 6. Verify WITHOUT `git status` (it scans and can re-hang)

```bash
git rev-parse HEAD
git rev-parse origin/main
git rev-list --left-right --count origin/main...HEAD   # ahead/behind
git log --oneline -3
```

### 7. Fix the root cause (so future ops don't stall)

- **Free disk space**: `uv cache clean`, `brew cleanup`, `pip cache purge`,
  `docker system prune` (**never** `--volumes`).
- **Stop vendoring large data dirs into git** — gitignore data, track only source.
  If a huge commit is what won't push, **reverting it makes its objects
  unreachable**, so the next push packs only a small reachable set and succeeds.
- Once there's headroom, `git gc` / `git repack -ad` to consolidate loose objects
  (→ 0 loose), making future ops fast.

## Verification

- The plumbing commit appears: `git log --oneline -3` shows your new commit on top
  of the previous HEAD; `git diff --cached --stat` is empty (index == new HEAD).
- After the root-cause fix, `git gc` and `git push` complete within their timeouts;
  `git count-objects -v` shows `packs: 1` and few/zero loose objects.

## Example

Symptom: `git commit` for a 2,922-file vendored data dir parked in `SN` at 0% CPU
for 14 min, holding a 0-byte stale `index.lock`; `.git/index` later went missing;
`git push` then stalled in "Counting objects"; `count-objects` showed 3,213 loose /
0 packs on a 96%-full volume.
Recovery that worked: killed the parked PID, `rm -f .git/index.lock`,
`git read-tree HEAD` to rebuild the index, then
`tree=$(git write-tree); commit=$(git commit-tree "$tree" -p HEAD -m "...");
git update-ref refs/heads/main "$commit"` — commit landed instantly. The push
remained blocked until disk headroom was freed / the large data dir was dropped
from tracking (its objects then unreachable, leaving only a tiny pack to push).

## Notes

- `gitstatusd` (powerlevel10k / zsh git prompt) runs read-only and is NOT the
  culprit; never kill it during recovery.
- Related state-confusion gotcha: if **every tracked path shows as a staged
  deletion AND also appears untracked**, that's an accidental `git rm -r --cached .`
  — the working tree is byte-identical to HEAD, so re-adding (or `git reset`) is a
  no-op versus HEAD, not real data loss.
- A missing `.git/index` is recoverable (it's a cache rebuilt from HEAD), not data
  loss; commit objects and the working tree are unaffected.

## References

- Git plumbing: `git-write-tree`, `git-commit-tree`, `git-update-ref`,
  `git-read-tree`, `git-count-objects` — <https://git-scm.com/docs>
