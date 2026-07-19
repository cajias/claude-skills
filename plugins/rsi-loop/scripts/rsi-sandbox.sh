#!/usr/bin/env bash
# rsi-sandbox.sh — build an inner-agent sandbox from a task directory.
# Part of the immutable rsi-loop harness.
#
# Usage: rsi-sandbox.sh <task-dir> <sandbox-dir>
#
# Copies ONLY the public materials (task.md, score.py, public/) into the
# sandbox. The private/ split never enters the sandbox — this structural
# separation, not the deny hook, is the primary wall between inner agents
# and held-out data. The script fails loudly if a private/ path somehow
# ends up in the sandbox.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: rsi-sandbox.sh <task-dir> <sandbox-dir>" >&2
  exit 2
fi

TASK_DIR="$1"
SANDBOX="$2"

for req in task.md score.py public; do
  if [[ ! -e "$TASK_DIR/$req" ]]; then
    echo "rsi-sandbox: task dir missing $req: $TASK_DIR" >&2
    exit 2
  fi
done

# Idempotent: clear any prior sandbox so a re-run (e.g. after an inner-agent
# failure) starts clean — no nested public/public and no stale nodes/ leaking
# a previous generation's solutions into a fresh run.
rm -rf "$SANDBOX"
mkdir -p "$SANDBOX/nodes"
cp "$TASK_DIR/task.md" "$TASK_DIR/score.py" "$SANDBOX/"
cp -R "$TASK_DIR/public" "$SANDBOX/public"

# Belt and braces: verify no private material leaked into the sandbox.
if find "$SANDBOX" -name "*private*" -print -quit | grep -q .; then
  echo "rsi-sandbox: FATAL — private material found in sandbox, aborting" >&2
  rm -rf "$SANDBOX"
  exit 1
fi

# Record a checksum manifest of the immutable inputs the inner agent is scored
# against. We do NOT chmod them read-only: agents run as the same uid (often
# root), which bypasses permission bits — read-only would give false assurance.
# Instead the manifest lets the OUTER harness DETECT tampering (see
# rsi-check-integrity.sh) and reject a step whose scorer/data was altered.
# The manifest covers private/ IF it is ever present. A sandbox never contains
# one (that is the private-read wall), so this is a no-op here — but it keeps the
# manifest builder honest so any other manifest-anchored dir that DOES hold a
# private split has it covered rather than silently unverified.
( cd "$SANDBOX" && find score.py task.md public $([ -e private ] && echo private) \
    -type f -exec sha256sum {} + | LC_ALL=C sort > .integrity.sha256 )

echo "sandbox ready: $SANDBOX (task.md, score.py, public/, nodes/; .integrity.sha256 recorded)"
