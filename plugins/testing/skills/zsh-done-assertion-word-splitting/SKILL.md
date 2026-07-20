---
name: zsh-done-assertion-word-splitting
description: |
  Two zsh traps that make a portable Done-assertion / verification bash block
  silently return FALSE all-MISSING results (e.g. "RESOLVED: 0/N MISSING: N")
  even though every file exists and resolves fine — or make a loop over paths
  mis-parse. Use when: (1) a shell verification / done-assertion block that
  resolves reference paths reports everything missing or unresolved though the
  files are plainly there; (2) a `for x in $var` / `while read` loop over
  space- or newline-separated paths behaves differently than you expect on
  macOS; (3) every command in a shell block starts failing with "command not
  found" partway through; (4) you are about to WRITE any shell verification,
  done-assertion, or check block that will run on a zsh-default machine
  (macOS). Root causes: (a) zsh does NOT word-split unquoted variables the way
  bash does, so bash-style `for x in $var` loops behave differently; (b)
  assigning to a lowercase `path` variable CLOBBERS the command search `$PATH`,
  because zsh ties the `path` array and the `PATH` scalar together — so every
  command after `path=...` breaks. Fix: force bash (`bash -c '...'` or
  `#!/usr/bin/env bash`), quote every expansion, set `IFS` deliberately, and
  NEVER name a variable `path` (use `p` / `filepath`). Skip this for genuine
  bash-only scripts on Linux CI, or when the block already runs under an
  explicit bash shebang and names no `path` variable.
author: Claude Code
version: 1.0.0
date: 2026-07-11
---

# zsh done-assertion word-splitting & `path` clobber

## Problem

Two symptoms, both on macOS (where the default interactive and login shell is
zsh, not bash):

1. A Done-assertion / verification block that resolves a set of reference paths
   reports them ALL missing — e.g. `RESOLVED: 0/5 MISSING: 5` — even though each
   file exists and resolves fine when you check it by hand.
2. Partway through a multi-command shell block, every command suddenly fails
   with `command not found` (`grep`, `cat`, `git`, `deno`, ...), as if the
   environment fell apart.

Both trace back to the same thing: running a bash-shaped script under zsh.

## Trigger conditions

- The block is a portable "does the work exist?" check: resolving reference
  paths, counting RESOLVED vs MISSING, or looping over a list of files.
- It runs on macOS or any machine whose default shell is zsh (`echo $0` prints
  `-zsh`, or `$ZSH_VERSION` is set).
- The loop is bash-idiomatic: `for x in $var; do ...` over a space- or
  newline-separated string, or `while read` fed by an unquoted expansion.
- OR the block assigns to a lowercase `path` variable and later commands break
  with `command not found`.

## Root cause

Two independent zsh behaviors, either of which alone breaks a bash-authored
block:

**(a) zsh does not word-split unquoted parameter expansions.** In bash,
`for x in $var` splits `$var` on `$IFS` into multiple words, and a whole idiom
family (`for x in $list`, `while read` over unquoted expansions) leans on that.
zsh, by design, does NOT split unquoted scalars — `$var` expands to a single
word. So a `for x in $paths` loop that iterates N times under bash iterates
ONCE (over the whole mashed-together string) under zsh, and your per-path
resolve/exists check runs against one string that matches nothing → `MISSING: N`.

**(b) Assigning to `path` clobbers `$PATH`.** zsh ties the array parameter
`path` to the scalar `PATH` — they are two views (array vs colon-joined string)
of the same thing. So a line like `path="$ref_dir/$file"` overwrites your
command search path with a bogus value. Every external command after that —
`grep`, `cat`, `git`, `deno` — fails with `command not found`, and the block
collapses in a way that looks unrelated to the assignment that caused it.

## Solution

Author portable verification / done-assertion blocks defensively:

1. **Force bash.** Start the block with `#!/usr/bin/env bash`, or run it as
   `bash -c '...'`. Don't rely on the ambient shell being bash — on macOS it
   isn't.
2. **Quote every expansion and split deliberately.** To iterate a list, drive
   it from a real newline-delimited source and set `IFS`:

   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   resolved=0 missing=0
   while IFS= read -r filepath; do
     if [ -e "$filepath" ]; then
       resolved=$((resolved + 1))
     else
       missing=$((missing + 1))
     fi
   done < paths.txt
   echo "RESOLVED: $resolved MISSING: $missing"
   ```

3. **Never name a variable `path`** (or `PATH`). Use `p`, `filepath`, `ref`, or
   `target`. This trap bites hardest because the failure surfaces far from the
   assignment that caused it.

## Verification

- Run the block once under `zsh -c '...'` and once under `bash -c '...'` — a
  portable block gives the SAME counts in both. A block that only works under
  bash is the bug.
- `echo "$PATH"` at the end of the block still prints a sane search path; if it
  prints one of your file paths, a `path=` assignment clobbered it.

## Notes

- This recurred across two milestones of a real build: a done-assertion that
  resolved reference paths reported `0/N` resolved on a macOS/zsh machine while
  the files were plainly present. Forcing bash + renaming the `path` variable
  fixed both symptoms.
- The `path`/`PATH` tie is zsh-specific — bash has no such linkage, which is
  exactly why a block authored and tested under bash passes review and then
  fails on someone's Mac.
- Related: `git-rebase-continue-editor-noninteractive` and
  `cron-block-generation-gotchas` cover the same family of "runs fine in one
  shell or context, breaks silently in another." When in doubt about
  portability, test the block under the shell it will actually run in.
