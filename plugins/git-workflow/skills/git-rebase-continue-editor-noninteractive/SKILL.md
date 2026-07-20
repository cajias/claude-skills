---
name: git-rebase-continue-editor-noninteractive
description: |
  Fix for `git rebase --continue` failing in non-interactive shells with
  the misleading error `"there was a problem with the editor 'nano'"`
  / `"could not commit staged changes"`. Use when:
  (1) you ran `git rebase --continue` after manually resolving a merge
  conflict via `git add`, in a non-interactive context (CI workflow,
  agent dispatch, ctx_execute, headless script), and the rebase
  silently aborted instead of completing;
  (2) the error output suggests using `-m`/`-F` but `git rebase
  --continue` rejects those flags;
  (3) `git status` shows the conflict-resolved files staged but
  uncommitted, `git branch --show-current` is empty (detached HEAD),
  and the rebase metadata under `.git/rebase-merge/` (or
  `.git/worktrees/<wt>/rebase-merge/` for a worktree) is still present;
  (4) you're scripting bulk-rebases across multiple PR branches and
  one of them stalls on a manually-resolved conflict.
  Root cause is `git rebase --continue` unconditionally opening
  `$GIT_EDITOR` to confirm the commit message; there is no `--no-edit`
  flag for `git rebase`. Fix is one env-var prefix:
  `GIT_EDITOR=true git rebase --continue`.
author: Claude Code
version: 1.0.0
date: 2026-05-09
---

# git rebase --continue editor in non-interactive shells

## Problem

You're rebasing a branch in a non-interactive shell (CI runner, agent
dispatch, `ctx_execute`, scripted automation). A conflict fires.
You resolve it, `git add` the files, and run `git rebase --continue`.
Instead of completing the rebase, git prints:

```text
error: there was a problem with the editor 'nano'
Please supply the message using either -m or -F option.
error: could not commit staged changes.
```

The error message is **misleading**:

- The `-m` / `-F` hint applies to `git commit`, not `git rebase
--continue` — passing them to rebase is rejected.
- "Problem with the editor" suggests an editor config bug, but the
  real issue is that no editor can run in a non-interactive shell
  (no TTY).

The branch is now in a half-finished rebase state: HEAD points to
the parent commit, the resolved files are staged but uncommitted,
and `.git/rebase-merge/` (the rebase state directory) is still
present. Re-running `git rebase --continue` produces the same error.
Running `git rebase --abort` works but throws away the manual
conflict resolution.

## Trigger conditions

Any of these:

- Output contains literally `there was a problem with the editor` and
  `could not commit staged changes`.
- `git status` after the failed continue shows the resolved files
  staged (`A file_A`, `M file_B`) and no merge markers.
- `git branch --show-current` returns nothing (detached HEAD).
- `ls .git/rebase-merge/` (or for a worktree:
  `ls .git/worktrees/<wt>/rebase-merge/`) shows the rebase state
  directory still exists.
- Context is a non-interactive shell: CI workflow, GitHub Actions
  step, agent-dispatched bash, `ctx_execute(language: "shell", ...)`,
  `subprocess.run(...)` from Python, etc.

## Root cause

`git rebase --continue` is implemented as: commit the resolved
conflict, then move to the next commit in the rebase plan. The commit
step opens the editor (`$GIT_EDITOR` → `$EDITOR` → fallback to
`vi`/`nano`) so you can edit the commit message before it lands. In an
interactive shell this is convenient; in a non-interactive shell, the
editor process can't acquire a TTY and exits non-zero. Git treats that
as "user aborted the commit" and bails.

There is **no `--no-edit` flag for `git rebase --continue`** (unlike
`git merge --no-edit` or `git revert --no-edit`). The
canonical workaround is to set `$GIT_EDITOR` to a no-op binary that
accepts the prefilled commit message without modification.

## Solution

Prefix the command with `GIT_EDITOR=true`:

```bash
GIT_EDITOR=true git rebase --continue
```

`true` is the standard Unix command that exits 0 immediately. Git
invokes it as if it were an editor, the editor "completes
successfully" with no edits, and git uses the prefilled commit message
as-is.

Alternatives that also work:

```bash
EDITOR=true git rebase --continue        # GIT_EDITOR overrides EDITOR
GIT_EDITOR=cat git rebase --continue     # cat also exits 0 quickly
```

**DO NOT** use `GIT_SEQUENCE_EDITOR=true` — that's for the _interactive_
rebase TODO list (`git rebase -i`), not for the per-commit message
editor. Setting only `GIT_SEQUENCE_EDITOR` won't help here.

If you need to keep editing the commit message manually but the
prefilled message is fine, just `GIT_EDITOR=true` it.

## Verification

```bash
# Reproduce
git rebase origin/main || true
# (resolve conflicts, git add the resolved files)
git rebase --continue
# Without fix: "problem with the editor 'nano'", staged changes
# uncommitted.

# Apply fix
GIT_EDITOR=true git rebase --continue
# With fix: the commit lands with the prefilled message; rebase
# proceeds to the next commit or completes.

# Confirm clean state
git status            # should show "nothing to commit, working tree clean"
git branch --show-current   # should print the branch name
ls .git/rebase-merge/ 2>&1   # No such file or directory  (rebase done)
```

## Example — bulk-rebase script (the canonical use case)

```bash
#!/bin/bash
set -euo pipefail   # pipefail is critical — see Notes

for branch in feat/A feat/B feat/C; do
  cd "<worktree-for-$branch>"
  git fetch origin --quiet
  if GIT_EDITOR=true git rebase origin/main; then
    git push --force-with-lease
  else
    # Fall through to manual resolution path
    echo "MANUAL: resolve conflicts in $branch then run:"
    echo "  GIT_EDITOR=true git rebase --continue"
    echo "  git push --force-with-lease"
  fi
  cd -
done
```

For an _interactive_ manual resolution flow (a human resolves the
conflict but the script continues programmatically), the pattern is:

```bash
# After human resolves and git-adds the conflict:
GIT_EDITOR=true git rebase --continue
git push --force-with-lease
```

## Notes

- **Pair with `set -o pipefail`**: if your script pipes git output
  through `tail`, `head`, or `grep`, the pipe's exit code is the LAST
  command's by default — so `git rebase ... | tail -10` returns 0
  even when the rebase failed. Without `set -o pipefail`, your
  conflict-detection branch silently fails and the script continues
  past a broken rebase. Always:

  ```bash
  set -euo pipefail
  ```

- This is the same root cause that makes `git commit` (no `-m`) fail
  in non-interactive shells. The fix is the same:
  `GIT_EDITOR=true git commit` (using the prepared message, e.g.
  via `git commit --reuse-message=HEAD@{1}`).
- `git pull --rebase` hits this if it has to pause for a conflict
  and you continue without an interactive shell. Same fix.
- `git cherry-pick --continue` after manual conflict resolution has
  the SAME trap — the `--no-edit` flag exists for `cherry-pick` but
  only suppresses the message editor on the FIRST commit; on
  `--continue`, you still need `GIT_EDITOR=true`. (Or equivalently:
  pass `-x --no-edit` upfront and ensure no conflicts.)
- The skill `cron-block-generation-gotchas` covers the same family
  of "tool runs fine interactively, breaks silently from cron" issues
  for cron-installed scripts. If you're scripting git from cron,
  always test under `env -i` first.

## References

- `git rebase` docs:
  <https://git-scm.com/docs/git-rebase>
- `git commit` editor selection
  (`$GIT_EDITOR` → `core.editor` → `$EDITOR` → `$VISUAL` → `vi`):
  <https://git-scm.com/docs/git-commit#_editor>
- `git config` `core.editor`:
  <https://git-scm.com/docs/git-config#Documentation/git-config.txt-coreeditor>
- Concrete origin: bulk-rebasing 5 open PR branches against a
  freshly-updated main in `cajias/nautilus-competition` (2026-05-09).
  Four branches rebased clean; one (`feat/makefile`) had a `README.md`
  conflict between newly-merged `## Parallel runs` and the branch's
  `### Make targets`. Manual resolution via Edit + git add succeeded;
  `git rebase --continue` from `ctx_execute` shell failed with the
  editor error; `GIT_EDITOR=true git rebase --continue` succeeded
  immediately and `gh pr view 7` flipped from CONFLICTING/DIRTY to
  MERGEABLE/CLEAN.
