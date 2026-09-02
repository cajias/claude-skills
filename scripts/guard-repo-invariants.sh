#!/usr/bin/env bash
# PreToolUse guard for invariants this repo documents but never enforced.
#
# Reads the PreToolUse hook payload on stdin and exits 2 (block) with an
# explanation on stderr, or 0 (allow). Every rule here corresponds to a
# "never do X" already written in CLAUDE.md — the point is to make those
# sentences mechanical instead of aspirational.
#
# Rules:
#   1. No edits under plugins/rsi-loop/docs/experiments/ (frozen run evidence).
#   2. No `git commit --no-verify` (husky pre-commit is the only structural gate).
#   3. No pip / black (this repo is uv + ruff only).
#   4. No force-push to main or master.
#
# Tested by scripts/test-guard-repo-invariants.sh.
set -uo pipefail

payload=$(cat)
tool=$(jq -r '.tool_name // empty' <<<"$payload" 2>/dev/null)
[ -n "$tool" ] || exit 0

block() {
  printf 'BLOCKED by scripts/guard-repo-invariants.sh: %s\n' "$1" >&2
  exit 2
}

case "$tool" in
Edit | Write | MultiEdit)
  file=$(jq -r '.tool_input.file_path // empty' <<<"$payload" 2>/dev/null)
  [ -n "$file" ] || exit 0
  case "$file" in
  */plugins/rsi-loop/docs/experiments/*)
    block "plugins/rsi-loop/docs/experiments/ is frozen run evidence (CLAUDE.md: 'Never reformat'). Editing it invalidates the recorded run."
    ;;
  esac
  ;;
Bash)
  raw=$(jq -r '.tool_input.command // empty' <<<"$payload" 2>/dev/null)
  [ -n "$raw" ] || exit 0

  # Scan only the SHELL of the command, never heredoc bodies. A commit message
  # that merely discusses --no-verify or pip is text, not an invocation, and
  # blocking it would make the guard the first thing anyone works around.
  cmd=$(
    awk '
      # Inside a heredoc: pass nothing through until the delimiter line.
      delim != "" { if ($0 == delim) delim = ""; next }
      # Opening a heredoc: keep the line up to <<, drop the body that follows.
      match($0, /<<-?[[:space:]]*(\047|")?[A-Za-z_][A-Za-z0-9_]*(\047|")?/) {
        head = substr($0, 1, RSTART - 1)
        d = substr($0, RSTART, RLENGTH)
        gsub(/^<<-?[[:space:]]*|\047|"/, "", d)
        delim = d
        print head
        next
      }
      { print }
    ' <<<"$raw"
  )
  [ -n "${cmd//[[:space:]]/}" ] || exit 0

  # Rules apply PER INVOCATION, not to the whole blob. `grep -n x && git commit`
  # is two commands: matching `git commit` in one segment and `-n` in another
  # would flag an innocent chain. Split on newlines and shell separators.
  segments=$(sed -E 's/(&&|\|\||;|\|)/\n/g' <<<"$cmd")

  while IFS= read -r seg; do
    [ -n "${seg//[[:space:]]/}" ] || continue

    # 2. --no-verify skips husky, which runs `make validate` + lint-staged. That
    #    gate is the ONLY structural check outside CI, so bypassing it lands
    #    marketplace/version drift and unformatted files on a branch.
    if [[ $seg =~ git[[:space:]]+commit ]] &&
      [[ $seg =~ (--no-verify|[[:space:]]-n([[:space:]]|$)) ]]; then
      block "'git commit --no-verify' skips husky (make validate + lint-staged), this repo's only structural gate outside CI. Fix the failure instead."
    fi

    # 3. CLAUDE.md: "uv + ruff only (no pip, no black)".
    if [[ $seg =~ (^|[[:space:]])pip3?[[:space:]]+install ]]; then
      block "pip is not used here — this repo is uv-only (CLAUDE.md). Use 'uv add' or 'uv sync'."
    fi
    if [[ $seg =~ (^|[[:space:]])black([[:space:]]|$) ]]; then
      block "black is not used here — Python is formatted with ruff only (CLAUDE.md). Use 'uv run ruff format'."
    fi

    # 4. Force-push to main. Feature-branch force-pushes are the normal rebase
    #    workflow and must stay allowed, so this blocks only when main/master is
    #    the target: named explicitly as a ref, or implied by the current branch
    #    when no refspec is given (the silent case).
    if [[ $seg =~ git[[:space:]]+push ]] &&
      [[ $seg =~ (--force([[:space:]]|=|$)|--force-with-lease|[[:space:]]-f([[:space:]]|$)) ]]; then
      if [[ $seg =~ (^|[[:space:]]|:)(main|master)([[:space:]]|$) ]]; then
        block "force-push targeting main/master is never allowed (CLAUDE.md)."
      fi
      # No refspec given: git pushes the CURRENT branch, so the target is only
      # visible from HEAD. Everything after `git push` minus flags is [remote
      # [refspec...]]; with no refspec, this is the silent force-push-to-main.
      refs=$(sed -E 's/.*git[[:space:]]+push//' <<<"$seg" |
        tr ' ' '\n' | grep -Ev '^(-|$)' | tail -n +2)
      if [ -z "$refs" ]; then
        branch=$(git symbolic-ref --short HEAD 2>/dev/null || true)
        if [[ $branch == "main" || $branch == "master" ]]; then
          block "force-push with no refspec while on '$branch' would force-push $branch (CLAUDE.md)."
        fi
      fi
    fi
  done <<<"$segments"
  ;;
esac
exit 0
