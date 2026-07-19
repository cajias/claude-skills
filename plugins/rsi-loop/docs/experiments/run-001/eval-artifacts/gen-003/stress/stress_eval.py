#!/usr/bin/env python3
"""Evaluator for the bin-packing stress suite.

Computes a stress_score by running a solution on synthetic instances
and applying the same scoring formula as score.py.

Usage:
    python3 nodes/stress/stress_eval.py --solution <path> --json
"""

import argparse
import importlib.util
import json
import math
import os
import sys


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


def run_instance(inst, solution_module):
    """Run a single instance and return (score, bins_used, error)."""
    try:
        bins = solution_module.pack(inst["items"], inst["capacity"])
    except Exception as e:
        return 0.0, None, f"{type(e).__name__}: {str(e)[:100]}"

    reason = validate(bins, inst["items"], inst["capacity"])
    if reason is not None:
        return 0.0, None, reason

    lb = max(math.ceil(sum(inst["items"]) / inst["capacity"]), 1)
    return lb / len(bins), len(bins), None


def main():
    ap = argparse.ArgumentParser(
        description="Evaluate a bin-packing solution on the stress suite."
    )
    ap.add_argument("--solution", required=True, help="Path to solution.py")
    ap.add_argument(
        "--json", action="store_true", help="Output JSON (default behavior)"
    )
    args = ap.parse_args()

    if not os.path.exists(args.solution):
        print(f"solution file not found: {args.solution}", file=sys.stderr)
        sys.exit(2)

    # Load the solution module
    spec = importlib.util.spec_from_file_location("solution", args.solution)
    solution_module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(solution_module)
    except Exception as e:
        print(f"failed to load solution: {e}", file=sys.stderr)
        sys.exit(2)

    # Load stress instances
    stress_dir = os.path.dirname(__file__)
    instances_path = os.path.join(stress_dir, "instances", "instances.json")
    if not os.path.exists(instances_path):
        print(f"stress instances not found at {instances_path}", file=sys.stderr)
        sys.exit(4)

    with open(instances_path) as f:
        instances = json.load(f)

    # Evaluate on each instance
    per_instance = []
    errors = []
    for inst in instances:
        score, bins_used, error = run_instance(inst, solution_module)
        per_instance.append(
            {
                "name": inst["name"],
                "score": round(score, 6),
                "bins_used": bins_used,
                "error": error,
            }
        )
        if error is not None:
            errors.append(
                {"name": inst["name"], "error": error, "n_items": len(inst["items"])}
            )

    # Compute aggregate stress score
    stress_score = (
        sum(p["score"] for p in per_instance) / len(per_instance)
        if per_instance
        else 0.0
    )
    stress_score = round(stress_score, 6)

    # Output JSON report
    report = {
        "stress_score": stress_score,
        "n_instances": len(instances),
        "errors": errors,
    }
    print(json.dumps(report))


if __name__ == "__main__":
    main()
