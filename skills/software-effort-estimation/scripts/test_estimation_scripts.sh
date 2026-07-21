#!/usr/bin/env bash
# Regression tests for the software-effort-estimation collector scripts.
#
#   collect_git_stats.sh   — repo check is now `git rev-parse --is-inside-work-tree`
#                            (was `[ -d .git ]`, which rejected worktrees/submodules
#                            where .git is a FILE, not a directory).
#   collect_all_metrics.sh — OUTPUT_DIR is absolutized after mkdir, so sub-scripts'
#                            `cd "$REPO_PATH"` can't misplace the output.
#
# Style mirrors plugins/rsi-loop/tests/test-*.sh: a check() tally, self-contained
# mktemp dirs with a trap, nonzero exit on any failure.
#
# Robustness note: this environment may lack `bc` and/or `cloc`. collect_git_stats.sh
# calls `bc` late (after the git guard AND after writing the output file), so under
# its own `set -e` it can exit nonzero while STILL having passed the guard and written
# output. These tests therefore key on the guard's observable effect — "did output get
# written past the guard, without the 'Not a git repository' rejection" — rather than
# on the overall exit code, and only assert exit 0 when `bc` is actually present.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_STATS="$SCRIPT_DIR/collect_git_stats.sh"
ALL_METRICS="$SCRIPT_DIR/collect_all_metrics.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PASS=0
FAIL=0

check() { # $1 label, $2 expected, $3 actual
  if [[ "$2" == "$3" ]]; then
    PASS=$((PASS + 1)); printf '  ok   %s\n' "$1"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL %s (want %s, got %s)\n' "$1" "$2" "$3"
  fi
}

bool() { # echo 1 if the given test-expression args are true, else 0
  if "$@"; then echo 1; else echo 0; fi
}

HAVE_BC="$(command -v bc >/dev/null 2>&1 && echo yes || echo no)"
HAVE_CLOC="$(command -v cloc >/dev/null 2>&1 && echo yes || echo no)"
HAVE_WORKTREE="$(git worktree list >/dev/null 2>&1 && echo yes || echo no)"

# Run collect_git_stats.sh; capture exit code + stdout. Then report whether the
# git guard let execution THROUGH (output file written, no rejection message).
GS_EXIT=0
run_git_stats() { # $1 repo path, $2 output file
  bash "$GIT_STATS" "$1" "$2" >"$WORK/gs.out" 2>"$WORK/gs.err"
  GS_EXIT=$?
}
guard_passed() { # $1 output file -> echo 1 if guard passed and output was written
  if grep -q 'Not a git repository' "$WORK/gs.out"; then echo 0; return; fi
  bool test -s "$1"
}

make_repo() { # $1 dir: git init + one commit
  mkdir -p "$1"
  git -C "$1" init -q
  git -C "$1" config user.email tester@example.com
  git -C "$1" config user.name "Test"
  echo "hello" > "$1/README.md"
  git -C "$1" add -A
  git -C "$1" commit -qm "init"
}

echo "[collect_git_stats.sh — git guard]"

# 1. A normal (.git is a directory) repo is accepted by the rev-parse guard.
REPO="$WORK/repo"
make_repo "$REPO"
run_git_stats "$REPO" "$WORK/repo_stats.txt"
check "normal repo: git guard passes and output is written" 1 "$(guard_passed "$WORK/repo_stats.txt")"
check "normal repo: output file has content" 1 "$(bool test -s "$WORK/repo_stats.txt")"
if [[ "$HAVE_BC" == "yes" ]]; then
  check "normal repo: exit 0 (bc present)" 0 "$GS_EXIT"
fi

# 2. THE REGRESSION: a worktree, where .git is a FILE, is accepted too.
#    Old `[ -d .git ]` would have rejected it; `git rev-parse` passes it.
if [[ "$HAVE_WORKTREE" == "yes" ]] && git -C "$REPO" worktree add -q "$WORK/wt" >/dev/null 2>&1; then
  check "worktree: .git is a FILE (the trap the old check fell into)" 1 "$(bool test -f "$WORK/wt/.git")"
  run_git_stats "$WORK/wt" "$WORK/wt_stats.txt"
  check "worktree: git guard passes (rev-parse accepts .git-as-file)" 1 "$(guard_passed "$WORK/wt_stats.txt")"
  check "worktree: was NOT rejected as 'Not a git repository'" 0 \
    "$(grep -c 'Not a git repository' "$WORK/gs.out")"
else
  echo "  note: git worktree not feasible here — falling back to static check only"
fi

# 2b. Static guard: regardless of worktree feasibility, the script must use the
#     rev-parse check and must NOT contain the old directory-only `.git` test.
check "source uses 'git rev-parse --is-inside-work-tree'" 1 \
  "$(bool grep -q 'git rev-parse --is-inside-work-tree' "$GIT_STATS")"
check "source no longer uses the old '[ ! -d \".git\" ]' check" 0 \
  "$(grep -cF '[ ! -d ".git" ]' "$GIT_STATS")"

# 2c. Sanity: a plain non-git directory is still rejected (exit 1, no output).
NOTGIT="$WORK/notgit"
mkdir -p "$NOTGIT"
run_git_stats "$NOTGIT" "$WORK/notgit_stats.txt"
check "non-git dir: rejected (exit 1)" 1 "$GS_EXIT"
check "non-git dir: no output file written" 0 "$(bool test -e "$WORK/notgit_stats.txt")"

echo
echo "[collect_all_metrics.sh — output absolutization]"

# 3. Output must land at the LAUNCH cwd, not inside the target repo. We git init a
#    repo at $WORK/testrepo and run the master script from a DIFFERENT cwd
#    ($WORK/launch). Before the fix, sub-scripts' `cd "$REPO_PATH"` made the
#    relative OUTPUT_DIR resolve inside testrepo. collect_git_stats writes
#    git_stats.txt BEFORE its `bc` call, so git_stats.txt lands even if bc/cloc are
#    missing and the overall run aborts under set -e afterward.
TESTREPO="$WORK/testrepo"
LAUNCH="$WORK/launch"
make_repo "$TESTREPO"
mkdir -p "$LAUNCH"
( cd "$LAUNCH" && bash "$ALL_METRICS" "$TESTREPO" >"$WORK/all.out" 2>"$WORK/all.err" )
ALL_EXIT=$?

check "git_stats.txt landed at the LAUNCH cwd (absolutized)" 1 \
  "$(bool test -f "$LAUNCH/effort_estimation_output/git_stats.txt")"
check "git_stats.txt did NOT land inside the target repo" 0 \
  "$(bool test -f "$TESTREPO/effort_estimation_output/git_stats.txt")"

# Tolerate a nonzero overall exit when cloc/bc are absent (set -e aborts mid-way
# AFTER git_stats.txt is written). Only assert exit 0 when both are present.
if [[ "$HAVE_BC" == "yes" && "$HAVE_CLOC" == "yes" ]]; then
  check "collect_all_metrics: exit 0 (bc + cloc present)" 0 "$ALL_EXIT"
else
  echo "  note: bc=$HAVE_BC cloc=$HAVE_CLOC — tolerating overall exit $ALL_EXIT (partial run)"
fi

echo
echo "estimation scripts: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
