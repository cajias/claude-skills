#!/usr/bin/env python3
"""PreToolUse deny hook: the rsi-loop private-split firewall.

Blocks tool calls that would let an inner agent (or anything else running in
the session) touch held-out evaluation data or tamper with the immutable
harness:

1. Reads/greps/globs of any `private/` split, or of a task-root directory
   that would recurse into one, under an RSI task tree
   (`tasks/`, `holdout-tasks/`, `rsi-runs/`).
2. Bash commands that reference those paths or invoke a scorer with
   `--private`.
3. Writes/edits to the immutable harness — any task/holdout `score.py`,
   `task.md`, or `instances.json`, and the `score.py`/`task.md` copies inside
   an inner-agent sandbox — the harness/agent boundary from the AIDE² paper.

The protected task-tree roots are defined ONCE in `TREE_ROOTS`; every rule
composes that constant so a new root (or the M3 battery layout) is added in a
single place.

Outer-harness escape hatch: a Bash command may access the private split only
when it starts with the exact prefix `RSI_OUTER_LOOP=1 `. That prefix appears
only in the outer-loop command docs and scripts; `tests/test-deny-hook.sh`
asserts it never appears in a generation directory or inner-agent prompt.

Humans: to disarm the hook entirely (e.g. while developing the plugin
itself), launch the session with RSI_HOOK_DISARM=1 in the environment.
Agents cannot set this — hook processes inherit the session environment,
not the environment of any Bash tool call.

Threat model (mirrors PLAN.md): this blocks accidental leakage and naive
attempts by sandboxed inner agents. It is NOT a security boundary against an
adversary with full session permissions. Two residual gaps are covered
structurally elsewhere, not here: (a) a Bash `cd` into a task dir followed by
a tree-relative `cat private/...` cannot be seen in a single command string —
the primary wall is that inner-agent sandboxes are built (by rsi-sandbox.sh)
with the private/ split absent entirely; (b) exotic writers (`python -c`,
process substitution) can still reach a scorer copy — the verifier stage
re-scores accepted winners against the pristine task dir, so a tampered
sandbox scorer cannot carry a generation to acceptance.
"""
import json
import os
import re
import sys

OUTER_PREFIX = "RSI_OUTER_LOOP=1 "

# Single source of truth for the protected task-tree roots.
TREE_ROOTS = r"(?:rsi-runs|holdout-tasks|tasks)"
_BOUND = r"(?:^|[/\s'\"=])"

# A path segment named exactly `private`, e.g. tasks/foo/private/instances.json
PRIVATE_SEGMENT = re.compile(r"(?:^|[/\s'\"=])private(?:/|$|[\s'\"])")
# ... but only inside an RSI task tree; plain projects with a private/ dir are
# none of our business.
RSI_CONTEXT = re.compile(_BOUND + TREE_ROOTS + r"/")
# The held-out data file is ours by name — deny it even without tree context,
# which also closes the `cd <taskdir>; cat private/instances.json` case.
PRIVATE_INSTANCES = re.compile(r"private/instances\.json")

PRIVATE_FLAG = re.compile(r"(?:^|\s)--private\b")

# Bash wildcard under a task tree could expand to private/.
RSI_GLOB = re.compile(_BOUND + TREE_ROOTS + r"/[^\s'\"]*[*?\[]")

# A Grep/Glob whose path is a task-root (or its parent) directory recurses into
# the sibling private/ split. Matches `tasks`, `tasks/`, `tasks/<name>`,
# `tasks/<name>/`, and `tasks/<name>/<wildcard>` — but NOT `tasks/<name>/public`
# or a single file like `tasks/<name>/task.md` (those don't recurse into private).
TREE_DIR_RECURSE = re.compile(
    _BOUND + r"(?:tasks|holdout-tasks)(?:/[^/\s'\"]+)?/?(?:$|[\s'\"*?\[])"
)

# Immutable harness files: scorers, task specs, and instance data anywhere under
# a task tree, plus the score.py/task.md copies inside an inner-agent sandbox.
IMMUTABLE_FILE = re.compile(
    r"(?:tasks|holdout-tasks)/[^\s'\"]*(?:score\.py|task\.md|instances\.json)"
    r"|/sandbox/(?:score\.py|task\.md)"
    r"|/sandbox/nodes/[^\s'\"]*score\.py"
)

# Bash writers targeting an immutable harness file. Verb list covers the naive
# writers; exotic writers are out of scope per the threat model above.
BASH_WRITE = re.compile(
    r"(?:>>?|\b(?:cp|mv|rm|tee|ln|chmod|truncate|dd|install)\b|sed\s+-i)"
    r"[^|;&]*(?:(?:tasks|holdout-tasks)/[^\s'\"]*(?:score\.py|task\.md|instances\.json)"
    r"|/sandbox/(?:score\.py|task\.md))"
)

RECURSIVE_READ_TOOLS = {"Glob", "Grep"}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


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
    if PRIVATE_INSTANCES.search(s):
        return True
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
        if not cmd.startswith(OUTER_PREFIX):
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
            if RSI_GLOB.search(cmd):
                deny(
                    "wildcards under an RSI task tree are blocked (they could "
                    "expand to the private/ split). Name paths explicitly."
                )
        # Immutable harness: no shell writes to a scorer / task spec / instance
        # data, outer-marked or not (the outer loop never edits the battery).
        if BASH_WRITE.search(cmd):
            deny("the task battery (scorers, task specs, instance data) is immutable.")
        sys.exit(0)

    # Every non-Bash tool (built-in or MCP): a held-out reference is always denied.
    for s in strings_of(tool_input):
        if is_private_ref(s):
            deny(
                f"{tool} may not touch a held-out private/ split. "
                "Only the outer harness scores private data."
            )
        if tool in RECURSIVE_READ_TOOLS and TREE_DIR_RECURSE.search(s):
            deny(
                f"{tool} on a task-root directory would recurse into the "
                "private/ split. Target the public/ subdirectory or a named file."
            )
        if tool in WRITE_TOOLS and IMMUTABLE_FILE.search(s):
            deny(
                f"{tool} may not modify the immutable harness "
                "(scorers, task specs, instance data, or sandbox copies). "
                "Generations may only write inside their own generation dir and work area."
            )
    sys.exit(0)


if __name__ == "__main__":
    main()
