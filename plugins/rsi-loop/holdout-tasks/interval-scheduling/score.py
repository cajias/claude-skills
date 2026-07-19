#!/usr/bin/env python3
"""Immutable scorer for the interval-scheduling holdout task. Part of the
rsi-loop harness: generations may read this file but must never modify it.

Usage:
    python3 score.py --public  --solution solution.py [--json]
    python3 score.py --private --solution solution.py [--json]   # outer loop only

Prints a JSON report to stdout and exits 0 (a low score is a report, not an
error). Exit codes: 2 = usage error, 3 = private split refused, 4 = missing
instance data.

This is a SECOND-ORDER-GENERALIZATION holdout: the rsi-loop outer loop never
trains on it. The best inner agent is later run here (by /rsi:report) to measure
whether a research policy that helped on the training battery also transfers.

Solution contract (see task.md):

    def select(intervals: list[list[int]]) -> list[int]

    intervals[i] = [start, end] with start < end. Return the INDICES of a
    maximum-size subset of mutually non-overlapping intervals. Two intervals
    overlap iff they share more than a single endpoint (so [1,3] and [3,5] do
    not overlap).

Per-instance score = len(selected) / optimal, where `optimal` is the size of
the earliest-finish-time greedy solution (provably optimal for this problem, so
it is the exact denominator). An invalid selection (out-of-range/duplicate
indices, a pair that actually overlaps, wrong types, exception, timeout) scores
0 for that instance.

Validation happens here, outside the solution subprocess, so a solution cannot
fake a schedule: it must return real, pairwise non-overlapping indices.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

PER_INSTANCE_TIMEOUT_S = 10

# The child process imports the solution and calls select(); it never validates
# or scores. It reads {"intervals", "solution_path"} on stdin and writes
# {"selected": ...} or {"error": ...} on stdout.
RUNNER_SRC = r"""
import json, sys, importlib.util
spec_in = json.load(sys.stdin)
try:
    spec = importlib.util.spec_from_file_location("solution", spec_in["solution_path"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    selected = mod.select(spec_in["intervals"])
    print(json.dumps({"selected": list(selected)}))
except Exception as e:
    print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
"""


def overlap(a, b):
    """True iff intervals a=[s,e], b=[s,e] share more than an endpoint."""
    return a[0] < b[1] and b[0] < a[1]


def validate(selected, intervals):
    """Return None if `selected` is a valid non-overlapping subset, else why."""
    if not isinstance(selected, list):
        return "solution did not return a list"
    seen = set()
    for idx in selected:
        if not isinstance(idx, int) or isinstance(idx, bool):
            return f"non-integer index: {idx!r}"
        if idx < 0 or idx >= len(intervals):
            return f"index out of range: {idx}"
        if idx in seen:
            return f"duplicate index: {idx}"
        seen.add(idx)
    chosen = [intervals[i] for i in selected]
    for i in range(len(chosen)):
        for j in range(i + 1, len(chosen)):
            if overlap(chosen[i], chosen[j]):
                return f"selected intervals overlap: {chosen[i]} and {chosen[j]}"
    return None


def optimal(intervals):
    """Size of the earliest-finish-time greedy schedule (provably optimal)."""
    order = sorted(intervals, key=lambda iv: (iv[1], iv[0]))
    count = 0
    last_end = None
    for s, e in order:
        if last_end is None or s >= last_end:
            count += 1
            last_end = e
    return max(count, 1)


def run_instance(inst, solution_path, neutral_cwd):
    """Return (score, n_selected, error). score/n_selected are None on error."""
    payload = json.dumps(
        {
            "intervals": inst["intervals"],
            "solution_path": os.path.abspath(solution_path),
        }
    )
    # Run the embedded runner via `-c` (no temp file to leak on a timeout kill)
    # in a neutral cwd, so the solution subprocess gets no incidental access to
    # the task directory (and therefore never to private/ during private scoring).
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
    if not isinstance(out, dict) or "selected" not in out:
        err = out.get("error") if isinstance(out, dict) else None
        return 0.0, None, (err or "solution produced no 'selected' output")[:300]
    reason = validate(out["selected"], inst["intervals"])
    if reason is not None:
        return 0.0, None, reason
    opt = optimal(inst["intervals"])
    return len(out["selected"]) / opt, len(out["selected"]), None


def main():
    ap = argparse.ArgumentParser()
    split = ap.add_mutually_exclusive_group(required=True)
    split.add_argument("--public", action="store_true")
    split.add_argument("--private", action="store_true")
    ap.add_argument("--solution", required=True)
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
            score, n_selected, error = run_instance(inst, args.solution, neutral_cwd)
            per_instance.append(
                {
                    "name": inst["name"],
                    "score": round(score, 6),
                    "selected": n_selected,
                    "optimal": optimal(inst["intervals"]),
                    "error": error,
                }
            )

    report = {
        "task": "interval-scheduling",
        "split": split_name,
        "n_instances": len(instances),
        "score": round(sum(p["score"] for p in per_instance) / len(per_instance), 6),
        "per_instance": per_instance,
    }
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
