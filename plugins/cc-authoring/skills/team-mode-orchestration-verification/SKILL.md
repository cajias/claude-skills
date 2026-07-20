---
name: team-mode-orchestration-verification
description: |
  Verify teammate work in Claude Code team mode when main-thread TaskList appears
  empty or teammates go idle without sending SendMessage replies. Use when: (1)
  you've created a team via TeamCreate and TaskCreate but `TaskList` returns "No
  tasks found" from the main thread, (2) a teammate sends only idle_notification
  after being dispatched with work, (3) you need to confirm a teammate actually
  completed their assigned task without trusting only their self-report. Covers
  the file-based team task list at ~/.claude/tasks/<team-name>/ and the "ground
  truth first, protocol state second" verification pattern used for debugging
  silent teammate completions.
author: Claude Code
version: 1.0.0
date: 2026-04-08
---

# Team Mode Orchestration: Verifying Teammate Work

## Problem

When orchestrating subagents in Claude Code's team mode (via `TeamCreate` + `Agent` with `team_name`), two recurring issues can make it look like work wasn't done when it actually was:

1. **Main-thread `TaskList` returns empty** for team-scoped tasks — even though `TaskCreate` succeeded.
2. **Teammates complete work but skip the `SendMessage` reply**, sending only `{"type":"idle_notification"}` — making it look like they stopped mid-task.

Both cases produce the same user-visible symptom: **"nothing happened" appearances despite successful execution**. The trap is reacting to protocol state (empty TaskList, missing reply) instead of verifying ground truth. The wrong reaction is re-dispatching the task; the right reaction is checking whether the work artifact exists on disk first.

## Context / Trigger Conditions

Apply this skill when ANY of the following occur:

- You called `TeamCreate` + `TaskCreate` and `TaskList` returns `"No tasks found"` from the main thread, even though `TaskCreate` reported success
- A teammate was dispatched with work but has sent only `idle_notification` messages with no `SendMessage` content
- You're about to re-dispatch a task because the previous teammate appeared to do nothing
- You want to confirm a teammate's self-reported success before creating downstream tasks
- A teammate's turn ended suspiciously quickly (e.g., two idle notifications <30s apart with no intervening plain-text message)

## Solution

### Core principle: always check ground truth before trusting protocol state

The authoritative sources of "did the work happen" are, in strict order of reliability:

1. **Filesystem artifacts** — does the file exist? Is the directory there? Is the git commit present?
2. **External system state** — is the GitHub fork created (`gh repo view`)? Is the tag pushed to origin? Is the database row present?
3. **Team task list files** — `ls ~/.claude/tasks/<team-name>/` — these JSON files are the actual task state for the team
4. **Teammate self-report** — only trust AFTER 1–3 corroborate

**Main-thread `TaskList` is NOT on this list.** It queries the non-team task list and will not reflect team-scoped tasks no matter how many you created via `TaskCreate` after `TeamCreate`.

### Diagnostic commands

When a teammate appears to have stopped silently:

```bash
# 1. See the team task list directly (JSON files, one per task)
ls ~/.claude/tasks/<team-name>/

# 2. See the team config (members, state, lead agent)
cat ~/.claude/teams/<team-name>/config.json

# 3. Verify the specific filesystem artifact the teammate was supposed to produce
ls -la /path/to/expected/output
test -d /path/to/expected/output && echo "EXISTS"
```

### For git-based teammate tasks (fork/clone/commit), verify git state

```bash
cd /path/to/clone && git remote -v                    # correct origin?
cd /path/to/clone && git branch --show-current         # correct branch?
cd /path/to/clone && git branch -a                     # branch pushed to remote?
cd /path/to/clone && git tag -l                        # tags created?
cd /path/to/clone && git rev-parse HEAD                # HEAD SHA captured?
gh repo view <owner>/<repo> --json nameWithOwner,parent  # fork exists on GitHub?
```

If all checks pass, the work is **done** regardless of whether the teammate sent a reply. Do not re-dispatch. Proceed to the next task.

### Preventing the SendMessage omission on future dispatches

`SendMessage` after task completion is a **soft protocol convention**, not a system enforcement. Teammates can mark tasks completed and go idle without sending a reply, and the system will not flag it. To prevent silent completions, brief teammates explicitly in their spawn prompt:

> **Critical protocol note:** When you finish, you MUST send a SendMessage to team-lead with a plain-text summary BEFORE going idle. Do not skip this step — it is how team-lead gets your results to relay to the user.

Cite prior failures in the brief so new teammates don't repeat them:

> Your predecessor teammate completed their work correctly but forgot to send a SendMessage reply. Do not repeat this mistake.

This is cheap and effective — teammates have no memory of other teammates' failures, so the orchestrator is the only place that pattern-memory lives until you bake it into the dispatch brief.

## Verification

After applying this skill, you should be able to answer all three of these with "yes":

1. **Did I check filesystem/external-state ground truth** before deciding whether to re-dispatch?
2. **Did I avoid re-dispatching completed work** (saving redundant execution and preventing collisions)?
3. **Did I re-brief any future teammate** with explicit SendMessage protocol instructions?

## Example

**Scenario:** Dispatched `explorer-1` (Explore agent) to fork a GitHub repo, clone it locally, create a feature branch, and push a tag. Teammate sent two back-to-back `idle_notification` messages 8 seconds apart with no content.

**Wrong reaction:**

> "Something went wrong — let me re-dispatch the task with a clearer brief."

Re-dispatching would duplicate the work, possibly collide with the existing local clone, and waste a teammate turn.

**Right reaction:**

```bash
# Step 1: Does the clone directory exist?
ls -la ~/Projects/workspace/nautilus-trader-streamlit
# → Directory exists with full repo contents ✓

# Step 2: Verify git state in the clone
cd ~/Projects/workspace/nautilus-trader-streamlit
git remote -v                      # → origin → fork (not upstream) ✓
git branch --show-current           # → integration/workspace-setup ✓
git branch -a                       # → feature branch pushed to origin ✓
git tag -l                          # → upstream-pinned exists ✓
git rev-parse HEAD                  # → SHA captured ✓

# Step 3: Verify GitHub-side fork creation
gh repo view <user>/nautilus_trader_streamlit --json parent,url
# → fork exists with correct parent upstream ✓
```

**Conclusion:** Work was fully completed. Teammate just skipped the SendMessage reply. The correct next action is:

1. Create the next task in the DAG (don't re-dispatch this one)
2. Brief the next teammate with an explicit SendMessage protocol note citing this teammate's omission as a prior failure to avoid
3. Optionally, capture a memory note documenting the TaskList visibility scoping behavior so future orchestration sessions don't repeat the investigation

## Notes

- **The `TaskList` scoping behavior appears undocumented** as of 2026-04-08. Plan around it; don't expect it to change.
- **Idle notifications are not failures.** A teammate sending `idle_notification` after finishing work is _normal_ — it means their turn ended. The failure signal is a _missing work artifact_, not an idle notification.
- **Never re-dispatch without first verifying ground truth.** Re-dispatch is destructive when the work is partially or fully done — you risk git collisions, duplicate external state (e.g., double-forked repos), and confused teammates.
- **If ground truth shows the work is incomplete**, then re-dispatch is appropriate — but include a note about the partial state so the new teammate can clean up or resume.
- **This skill complements `superpowers:dispatching-parallel-agents`** — that skill covers dispatch patterns; this one covers verification of what was dispatched.
- **SendMessage is not the only coordination mechanism.** Teammates can also update task descriptions via `TaskUpdate`, which is often more reliable than plain-text messages for structured handoffs.

## References

- Team mode tool documentation: `TeamCreate` tool description (in-session)
- Relevant memory note: `~/.claude/projects/<encoded-project-path>/memory/feedback_team_task_list_visibility.md`
- Related skill: `superpowers:dispatching-parallel-agents` (sibling concern, dispatch side)
