# git-squash-soft-reset

Squash multiple git commits into one using soft reset - a non-interactive
alternative to rebase. Use when: (1) you need to squash commits without an
editor, (2) interactive rebase hangs or requires manual intervention, (3) CI/CD
or automated contexts where git rebase -i won't work, (4) you want the fastest
way to combine all branch commits into one. Covers soft reset technique, force
push safety, and pre-commit hook bypass.
