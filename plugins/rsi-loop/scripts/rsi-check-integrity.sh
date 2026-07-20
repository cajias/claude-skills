#!/usr/bin/env bash
# rsi-check-integrity.sh — detect tampering of a task's immutable harness.
# Part of the immutable rsi-loop harness.
#
# Usage: rsi-check-integrity.sh <task-dir>
#
# Exit 0 = the scorer / task spec / instance data match their trusted baseline;
# exit 1 = tampered (or unverifiable). This is the writer-gap defense that
# actually holds: inner agents run as the same uid as the harness (often root),
# so OS read-only bits cannot PREVENT a write — but we can DETECT one and refuse
# to trust a score derived from a tampered scorer.
#
# Trust anchor, in order of preference:
#   1. git — if the task dir is tracked, the RAW working bytes of each immutable
#      spec file are hashed (git hash-object --no-filters) and compared to its
#      HEAD blob. This compares CONTENT, not `git status`, so it catches an edit
#      hidden with skip-worktree / assume-unchanged (which silence status but do
#      not change what score.py reads); --no-filters plus an injected-.gitattributes
#      check defeats a clean-filter that would otherwise re-emit the original blob
#      from tampered bytes. Residual: a same-uid agent that can `git commit` the tamper moves
#      HEAD and would pass — HEAD is only as trustworthy as "no one moved it";
#      inner agents are mitigated because they run in sandboxes, not this repo.
#   2. .integrity.sha256 — a checksum manifest written when the dir was
#      provisioned (by rsi-sandbox.sh, or rsi-init for a run battery).
# If neither exists the harness cannot be verified — treated as a hard failure,
# because scoring against an unverifiable scorer is exactly what this guards.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: rsi-check-integrity.sh <task-dir>" >&2
  exit 2
fi
TASK_DIR="$1"
if [[ ! -d "$TASK_DIR" ]]; then
  echo "rsi-integrity: no such task dir: $TASK_DIR" >&2
  exit 2
fi

# Immutable pathspecs (some may be absent, e.g. a sandbox has no private/).
SPECS=(score.py task.md public private)

if git -C "$TASK_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail=""
  # (a) Untracked additions, deletions, or staged changes under the immutable
  #     specs — `git status` still surfaces these (skip-worktree does not hide an
  #     untracked NEW file, only edits to a tracked one).
  changed="$(git -C "$TASK_DIR" status --porcelain -- "${SPECS[@]}" 2>/dev/null || true)"
  [[ -n "$changed" ]] && fail="${fail}${changed}"$'\n'
  # (b) Content of every TRACKED spec file vs its HEAD blob, compared directly by
  #     hashing the RAW working bytes — this ignores the index, so it detects an
  #     edit hidden with `git update-index --skip-worktree`/`--assume-unchanged`,
  #     which silence `git status`. `--no-filters` is essential: without it,
  #     `git hash-object` applies gitattributes clean filters, so an agent could
  #     install a clean filter that re-emits the original blob from tampered
  #     working bytes and pass this check. --no-filters hashes what is actually on
  #     disk (what score.py reads), which is the property that must hold.
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    head="$(git -C "$TASK_DIR" rev-parse "HEAD:./$f" 2>/dev/null || echo MISSING)"
    if [[ -f "$TASK_DIR/$f" ]]; then
      work="$(git -C "$TASK_DIR" hash-object --no-filters "$f" 2>/dev/null || echo ERR)"
    else
      work="ABSENT"
    fi
    [[ "$head" != "$work" ]] && fail="${fail}    content differs: $f"$'\n'
  done < <(git -C "$TASK_DIR" ls-files -- "${SPECS[@]}" 2>/dev/null)
  # (c) An injected .gitattributes (in the task dir, tracked-but-modified or
  #     untracked) can only be there to redirect clean/smudge filters at the
  #     harness — treat any non-pristine .gitattributes as tampering. (Belt and
  #     braces on top of --no-filters, which already neutralises the filter.)
  ga="$(git -C "$TASK_DIR" status --porcelain -- .gitattributes 2>/dev/null || true)"
  [[ -n "$ga" ]] && fail="${fail}    suspicious .gitattributes: $ga"$'\n'
  if [[ -n "$fail" ]]; then
    echo "rsi-integrity: FAIL — immutable harness tampered vs git HEAD:" >&2
    printf '%s' "$fail" | sed 's/^/    /' >&2
    exit 1
  fi
  echo "rsi-integrity: OK (git-clean, content-verified) $TASK_DIR" >&2
  exit 0
fi

if [[ -f "$TASK_DIR/.integrity.sha256" ]]; then
  if ( cd "$TASK_DIR" && sha256sum --quiet -c .integrity.sha256 ) >/dev/null 2>&1; then
    echo "rsi-integrity: OK (manifest) $TASK_DIR" >&2
    exit 0
  fi
  echo "rsi-integrity: FAIL — checksum mismatch vs .integrity.sha256 in $TASK_DIR" >&2
  exit 1
fi

echo "rsi-integrity: FAIL — no git and no .integrity.sha256; harness unverifiable in $TASK_DIR" >&2
exit 1
