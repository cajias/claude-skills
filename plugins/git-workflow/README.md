# git-workflow

Reference skills for git and GitHub CLI failures that look like broken tooling
but are really known quirks. Each one bundles the diagnosis and the exact
workaround discovered while shipping real work, so the next encounter costs a
lookup instead of another debugging session. Skills surface automatically via
Claude Code's semantic matching when you hit their trigger conditions.

## Skills

| Skill                                       | Purpose                                                                           |
| ------------------------------------------- | --------------------------------------------------------------------------------- |
| `gh-pr-create-must-push-error`              | `gh pr create` rejects an already-pushed branch; pass `--head <branch>`           |
| `gh-pr-merge-in-worktrees`                  | `gh pr merge --delete-branch` looks failed in a worktree though the merge landed  |
| `git-deadlock-plumbing-recovery`            | Recover git hangs at ~0% CPU on macOS/APFS via write-tree/commit-tree/update-ref  |
| `git-rebase-continue-editor-noninteractive` | `git rebase --continue` editor error; prefix with `GIT_EDITOR=true`               |
| `git-squash-merge-tree-hash-diagnosis`      | Diagnose a branch "N commits ahead" after a squash merge using tree-hash equality |
| `parallel-subagent-git-worktree-race`       | Detect and recover HEAD/index corruption when parallel subagents share one `.git` |

## Install

```bash
cp -r plugins/git-workflow ~/.claude/plugins/
```
