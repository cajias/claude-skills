# bash-subagent-write-limitation

Fix for Task tool subagents with subagent_type=Bash being unable to write files when
PreToolUse hooks block write operations. Use when: (1) dispatching parallel Bash agents
to implement code in worktrees, (2) agents report "Permission to use Bash has been
auto-denied", (3) agents can read files but all write/touch/cp/dd commands fail.
Solution: write files from the parent session using Write/Edit tools, then optionally
dispatch Bash agents only for validation (lint, test, typecheck).
