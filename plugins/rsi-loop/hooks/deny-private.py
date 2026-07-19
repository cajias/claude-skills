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

Threat model (mirrors PLAN.md): this hook blocks accidental leakage and naive
attempts by sandboxed inner agents. It is the FAST-FEEDBACK layer, not the only
wall — agents run as the same uid as the harness (often root), so no in-process
check and no OS permission bit can truly PREVENT a determined write. The
defenses are layered:

- Private-split READS: the primary wall is that inner-agent sandboxes are built
  (by rsi-sandbox.sh) with the private/ split absent entirely. This hook adds
  outer-session coverage: direct refs, the held-out filename, wildcard/recursive
  reads, and `cd` into a `private` dir (closing the multi-step cwd escape). A
  residual remains — arbitrary stateful shell maneuvers cannot be caught by a
  stateless per-command check — but there is no private data in the one place
  inner agents actually run.
- Harness WRITES: not prevented but DETECTED. rsi-check-integrity.sh anchors the
  scorer/task/instance data to git HEAD (or a checksum manifest), and the outer
  private-scoring path (rsi-score.sh --private) plus the verifier refuse to trust
  a score from a tampered harness. So any writer — naive `>>`/`tee` or exotic
  `python -c` / `dd` — fails the step rather than carrying a hacked generation to
  acceptance. This hook's write rules are the fast, legible first line.
"""
import json
import os
import re
import sys

OUTER_PREFIX = "RSI_OUTER_LOOP=1 "

# Single source of truth for the protected task-tree roots.
TREE_ROOTS = r"(?:rsi-runs|holdout-tasks|tasks)"
# The immutable-harness subset: task/holdout trees. `rsi-runs` is excluded
# because a run's battery lives at `rsi-runs/<run>/tasks/...`, already covered
# by the `tasks` alternative.
HARNESS_ROOTS = r"(?:tasks|holdout-tasks)"
# The immutable harness files a scorer/task tree exposes.
HARNESS_FILE = HARNESS_ROOTS + r"/[^\s'\"]*(?:score\.py|task\.md|instances\.json)"
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

# `cd` into a directory named `private`. This closes the multi-step cwd escape
# (`cd tasks/bp` then `cd private` then `cat instances.json`): the first two
# steps are individually innocuous to a stateless string check, but a `cd` whose
# target's final segment is `private` has no legitimate purpose in an RSI session.
CD_INTO_PRIVATE = re.compile(
    r"\bcd\s+[\"']?(?:[^\s;&|\"']*/)?private/?[\"']?(?:$|[\s;&|])"
)

# Bash wildcard under a task tree could expand to private/.
RSI_GLOB = re.compile(_BOUND + TREE_ROOTS + r"/[^\s'\"]*[*?\[]")

# A Grep/Glob whose path is a task-root (or its parent) directory recurses into
# the sibling private/ split. Matches `tasks`, `tasks/`, `tasks/<name>`,
# `tasks/<name>/`, and `tasks/<name>/<wildcard>` — but NOT `tasks/<name>/public`
# or a single file like `tasks/<name>/task.md` (those don't recurse into private).
TREE_DIR_RECURSE = re.compile(
    _BOUND + HARNESS_ROOTS + r"(?:/[^/\s'\"]+)?/?(?:$|[\s'\"*?\[])"
)

# A recursive content read rooted at an ANCESTOR of a protected tree recurses
# INTO the private/ splits below it and returns held-out answers as match lines,
# even though the command/path names no `private`. Two ancestor shapes: the
# plugin's own tree (any path containing an `rsi-loop` segment) and a bare
# filesystem/session root (`.`, `..`, `/`, `~`). Either is denied for a
# recursive read UNLESS it is narrowed to a `public/` subtree or a single file.
# Backstop only (the primary wall is that inner-agent sandboxes contain no
# private/); a residual remains for a recursive read rooted at some arbitrary
# absolute repo path this stateless check cannot resolve.
_ANCESTOR_ROOT = re.compile(
    r"(?:(?:^|[/\s'\"=])(?:\.\.?|~|/)|rsi-loop)(?:/|$|[\s'\"])"
)
_NARROWED_PUBLIC = re.compile(r"/public(?:/|$|[\s'\"])")
_SPECIFIC_FILE = re.compile(r"\.(?:py|md|json|txt|csv|mjs|sh|toml|ya?ml)(?:$|[\s'\"])")


def recursive_read_reaches_private(path):
    """True if a recursive read at `path` would descend into a protected private/
    split: `path` is an RSI task tree, a task-root, or a broad ancestor of one,
    and is not narrowed to public/ or a single file."""
    if not path:
        return True  # empty path == cwd == recurse from here
    if _NARROWED_PUBLIC.search(path) or _SPECIFIC_FILE.search(path):
        return False
    if TREE_DIR_RECURSE.search(path):
        return True
    return bool(_ANCESTOR_ROOT.search(path))


# Recursive-read Bash invocations (grep with an -r/-R in any flag cluster, e.g.
# -rn/-nR/-rIl; ripgrep; silver searcher) whose target could be a broad ancestor
# of a protected tree. The r/R may sit anywhere in a dash-flag cluster and be
# followed by more flags, and the flag need not immediately follow `grep`.
BASH_RECURSIVE_READ = re.compile(r"\bgrep\b[^|;&\n]*?-[A-Za-z]*[rR]|\b(?:rg|ag)\b")

# Immutable harness files: scorers, task specs, and instance data anywhere under
# a task tree, plus the score.py/task.md copies inside an inner-agent sandbox.
IMMUTABLE_FILE = re.compile(
    HARNESS_FILE + r"|/sandbox/(?:score\.py|task\.md)|/sandbox/nodes/[^\s'\"]*score\.py"
)

# Bash writers targeting an immutable harness file. Verb list covers the naive
# writers; exotic writers are out of scope per the threat model above.
BASH_WRITE = re.compile(
    r"(?:>>?|\b(?:cp|mv|rm|tee|ln|chmod|truncate|dd|install)\b|sed\s+-i)"
    r"[^|;&]*(?:" + HARNESS_FILE + r"|/sandbox/(?:score\.py|task\.md))"
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
            if CD_INTO_PRIVATE.search(cmd):
                deny(
                    "changing directory into a `private` directory is blocked "
                    "(it would let a later tree-relative read reach the held-out split)."
                )
            if RSI_GLOB.search(cmd):
                deny(
                    "wildcards under an RSI task tree are blocked (they could "
                    "expand to the private/ split). Name paths explicitly."
                )
            if (
                BASH_RECURSIVE_READ.search(cmd)
                and _ANCESTOR_ROOT.search(cmd)
                and not _NARROWED_PUBLIC.search(cmd)
            ):
                deny(
                    "a recursive read (grep -r / rg) rooted at a broad ancestor "
                    "directory would descend into a private/ split. Narrow it to "
                    "a public/ subtree or a named file."
                )
        # Immutable harness: no shell writes to a scorer / task spec / instance
        # data, outer-marked or not (the outer loop never edits the battery).
        if BASH_WRITE.search(cmd):
            deny("the task battery (scorers, task specs, instance data) is immutable.")
        sys.exit(0)

    # Recursive-read tools (Grep/Glob): deny a search whose base path — or, for
    # Glob, its pattern — is a task tree or a broad ancestor of one. Checked on
    # the path/pattern fields specifically (not the Grep regex, which would
    # false-positive on a pattern that merely looks path-like).
    if tool in RECURSIVE_READ_TOOLS:
        candidates = [tool_input.get("path", "")]
        if tool == "Glob":
            candidates.append(tool_input.get("pattern", ""))
        for c in candidates:
            if isinstance(c, str) and recursive_read_reaches_private(c):
                deny(
                    f"{tool} on a task-root or broad ancestor directory would "
                    "recurse into the private/ split. Target the public/ "
                    "subdirectory or a named file."
                )

    # Every non-Bash tool (built-in or MCP): a held-out reference is always denied,
    # and no write may touch the immutable harness.
    for s in strings_of(tool_input):
        if is_private_ref(s):
            deny(
                f"{tool} may not touch a held-out private/ split. "
                "Only the outer harness scores private data."
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
