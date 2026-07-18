#!/usr/bin/env python3
"""PreToolUse deny hook: the rsi-loop private-split firewall.

Blocks tool calls that would let an inner agent (or anything else running in
the session) touch held-out evaluation data:

1. Reads/greps/globs of any `private/` split under an RSI task tree
   (`rsi-runs/`, `tasks/`, `holdout-tasks/`).
2. Bash commands that reference those paths or invoke a scorer with
   `--private`.
3. Writes/edits to the immutable parts of a run directory
   (`rsi-runs/<run>/tasks/`, `holdout-tasks/`, and any task `score.py`) —
   the harness/agent boundary from the AIDE² paper.

Outer-harness escape hatch: a Bash command may access the private split only
when it is explicitly marked as outer-loop harness work by starting with the
prefix `RSI_OUTER_LOOP=1 `. That prefix appears only in the outer-loop
command docs and scripts; it must never appear in a generation directory or
inner-agent prompt (the adversarial test suite asserts this).

Humans: to disarm the hook entirely (e.g. while developing the plugin
itself), launch the session with RSI_HOOK_DISARM=1 in the environment.
Agents cannot set this — hook processes inherit the session environment,
not the environment of any Bash tool call.

Threat model note (mirrors PLAN.md): this blocks accidental leakage and
naive attempts by sandboxed inner agents. It is not a security boundary
against an adversary with full session permissions.
"""
import json
import os
import re
import sys

OUTER_PREFIX = "RSI_OUTER_LOOP=1 "

# A path segment named exactly `private`, e.g. tasks/foo/private/instances.json
PRIVATE_SEGMENT = re.compile(r"(^|[/\s'\"=])private(/|$|[\s'\"])")
# ... but only inside RSI task trees; plain projects with a private/ dir are
# none of our business.
RSI_CONTEXT = re.compile(r"(rsi-runs/|(^|[/\s'\"])tasks/|holdout-tasks/)")
PRIVATE_FLAG = re.compile(r"(^|\s)--private\b")
# Glob/wildcard evasion of the literal word `private` under an RSI task tree,
# e.g. cat rsi-runs/r1/tasks/bp/p*/instances.json
RSI_GLOB = re.compile(r"(rsi-runs|holdout-tasks|(^|[/\s'\"])tasks)/[^\s'\"]*[*?\[]")

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
READ_TOOLS = {"Read", "Glob", "Grep"}
# Immutable-at-runtime paths inside a run directory.
IMMUTABLE_RUN_PATH = re.compile(r"rsi-runs/[^\s'\"]*/(tasks|holdout-tasks)(/|$)")
SCORER_PATH = re.compile(r"(tasks|holdout-tasks)/[^\s'\"]*score\.py")


def strings_of(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings_of(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings_of(v)


def deny(reason):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"rsi-loop private-split firewall: {reason}",
                }
            }
        )
    )
    sys.exit(0)


def is_private_ref(s):
    return bool(PRIVATE_SEGMENT.search(s) and RSI_CONTEXT.search(s))


def main():
    if os.environ.get("RSI_HOOK_DISARM") == "1":
        sys.exit(0)
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)  # malformed input: not ours to block

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    if tool == "Bash":
        cmd = tool_input.get("command", "")
        marked_outer = cmd.startswith(OUTER_PREFIX)
        if not marked_outer:
            if PRIVATE_FLAG.search(cmd):
                deny(
                    "private-split scoring is reserved for the outer harness. "
                    "Inner agents optimize the public score only."
                )
            if is_private_ref(cmd):
                deny(
                    "this command references a held-out private/ split. "
                    "Inner agents may only touch task.md, score.py and public/."
                )
            if RSI_GLOB.search(cmd) and "priv" not in cmd:
                # Wildcards under an RSI task tree could expand to private/.
                deny(
                    "wildcards under an RSI task tree are blocked (they could "
                    "expand to the private/ split). Name paths explicitly."
                )
        # Immutable harness: no shell writes into a run's task battery,
        # outer-marked or not (the outer loop never edits the battery either).
        if re.search(
            r"(>>?|\b(cp|mv|rm|tee|sed\s+-i|ln|chmod|truncate)\b)[^|;&]*rsi-runs/[^\s'\"]*/(tasks|holdout-tasks)/",
            cmd,
        ):
            deny("the task battery under rsi-runs/ is immutable once initialized.")
        sys.exit(0)

    if tool in READ_TOOLS or tool in WRITE_TOOLS:
        for s in strings_of(tool_input):
            if is_private_ref(s):
                deny(
                    f"{tool} may not touch a held-out private/ split. "
                    "Only the outer harness scores private data."
                )
            if tool in WRITE_TOOLS and (
                IMMUTABLE_RUN_PATH.search(s) or SCORER_PATH.search(s)
            ):
                deny(
                    f"{tool} may not modify the immutable harness "
                    "(task battery / scorers). Generations may only write "
                    "inside their own generation directory and work area."
                )
    sys.exit(0)


if __name__ == "__main__":
    main()
