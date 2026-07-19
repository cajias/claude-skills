#!/usr/bin/env python3
"""Immutable scorer for the bin-packing task. Part of the rsi-loop harness:
generations may read this file but must never modify it.

Usage:
    python3 score.py --public  --solution solution.py [--json]
    python3 score.py --private --solution solution.py [--json]   # outer loop only

Prints a JSON report to stdout and exits 0 (score of 0 is a report, not an
error). Exit codes: 2 = usage error, 3 = private split refused, 4 = missing
instance data.

The private split is scored only by the rsi-loop outer harness, never by
inner agents: it requires RSI_OUTER_LOOP=1 in the environment and the
private/instances.json file, which is absent from inner-agent sandboxes.

Validation happens here, outside the solution subprocess, so a solution
cannot fake a packing: it must return real bins that partition the items
without overflowing capacity.
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile

PER_INSTANCE_TIMEOUT_S = 10

# The child process imports the solution and calls pack(); it never validates
# or scores. It reads {"items", "capacity", "solution_path"} on stdin and
# writes {"bins": ...} or {"error": ...} on stdout.
RUNNER_SRC = r"""
import json, sys, importlib.util
spec_in = json.load(sys.stdin)
try:
    spec = importlib.util.spec_from_file_location("solution", spec_in["solution_path"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    bins = mod.pack(spec_in["items"], spec_in["capacity"])
    print(json.dumps({"bins": bins}))
except Exception as e:
    print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
"""


def validate(bins, items, capacity):
    """Return None if bins is a valid packing, else a reason string."""
    if not isinstance(bins, list) or not all(isinstance(b, list) for b in bins):
        return "solution did not return a list of lists"
    seen = []
    for b in bins:
        load = 0
        for idx in b:
            if not isinstance(idx, int) or isinstance(idx, bool):
                return f"non-integer item index: {idx!r}"
            if idx < 0 or idx >= len(items):
                return f"index out of range: {idx}"
            seen.append(idx)
            load += items[idx]
        if load > capacity:
            return f"bin over capacity ({load} > {capacity})"
    if len(seen) != len(items) or len(set(seen)) != len(items):
        return "items not partitioned exactly once"
    if any(len(b) == 0 for b in bins):
        return "empty bin"
    return None


def lower_bound(inst):
    return max(math.ceil(sum(inst["items"]) / inst["capacity"]), 1)


def run_instance(inst, solution_path, neutral_cwd):
    """Return (score, bins_used, error). score/bins_used are None on error."""
    payload = json.dumps(
        {
            "items": inst["items"],
            "capacity": inst["capacity"],
            "solution_path": os.path.abspath(solution_path),
        }
    )
    # Run the embedded runner via `-c` (no temp file to leak on a timeout kill)
    # in a neutral cwd, so the solution subprocess gets no *incidental* (cwd
    # -relative) access to the task directory. This is not a filesystem sandbox:
    # a solution could still read private/ via an absolute path during private
    # scoring — that is a reward hack the verifier detects, not one prevented
    # here (detection, not prevention; see PLAN.md).
    try:
        proc = subprocess.run(
            [sys.executable, "-c", RUNNER_SRC],
            input=payload,
            capture_output=True,
            text=True,
            timeout=PER_INSTANCE_TIMEOUT_S,
            cwd=neutral_cwd,
        )
    except subprocess.TimeoutExpired:
        return 0.0, None, f"timeout after {PER_INSTANCE_TIMEOUT_S}s"
    try:
        out = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return 0.0, None, f"unparseable solution output: {proc.stderr.strip()[:200]}"
    if not isinstance(out, dict) or "bins" not in out:
        # Includes the runner's {"error": ...} path and any stray final line
        # that is valid JSON but not a packing (e.g. a diagnostic print before
        # an early exit) — scored 0, never crashes the battery.
        err = out.get("error") if isinstance(out, dict) else None
        return 0.0, None, (err or "solution produced no 'bins' output")[:300]
    reason = validate(out["bins"], inst["items"], inst["capacity"])
    if reason is not None:
        return 0.0, None, reason
    return lower_bound(inst) / len(out["bins"]), len(out["bins"]), None


def main():
    ap = argparse.ArgumentParser()
    split = ap.add_mutually_exclusive_group(required=True)
    split.add_argument("--public", action="store_true")
    split.add_argument("--private", action="store_true")
    ap.add_argument("--solution", required=True)
    # Output is always JSON; --json is accepted because every documented
    # invocation (rsi-score.sh, the operator prompts) passes it and evolved
    # generations may keep passing it. Accept-and-ignore, never require.
    ap.add_argument("--json", action="store_true", help="accepted no-op; output is always JSON")
    args = ap.parse_args()

    split_name = "private" if args.private else "public"
    if args.private and os.environ.get("RSI_OUTER_LOOP") != "1":
        print(
            "refused: the private split is scored only by the rsi-loop outer "
            "harness (RSI_OUTER_LOOP=1). Inner agents optimize the public score.",
            file=sys.stderr,
        )
        sys.exit(3)

    task_dir = os.path.dirname(os.path.abspath(__file__))
    instances_path = os.path.join(task_dir, split_name, "instances.json")
    if not os.path.exists(instances_path):
        print(f"no {split_name} instances at {instances_path}", file=sys.stderr)
        sys.exit(4)
    if not os.path.exists(args.solution):
        print(f"solution file not found: {args.solution}", file=sys.stderr)
        sys.exit(2)

    with open(instances_path) as f:
        instances = json.load(f)
    if not isinstance(instances, list) or not instances:
        print(f"no usable instances in {instances_path}", file=sys.stderr)
        sys.exit(4)

    per_instance = []
    with tempfile.TemporaryDirectory() as neutral_cwd:
        for inst in instances:
            score, bins_used, error = run_instance(inst, args.solution, neutral_cwd)
            per_instance.append(
                {
                    "name": inst["name"],
                    "score": round(score, 6),
                    "bins_used": bins_used,
                    "lower_bound": lower_bound(inst),
                    "error": error,
                }
            )

    report = {
        "task": "bin-packing",
        "split": split_name,
        "n_instances": len(instances),
        "score": round(sum(p["score"] for p in per_instance) / len(per_instance), 6),
        "per_instance": per_instance,
    }
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
