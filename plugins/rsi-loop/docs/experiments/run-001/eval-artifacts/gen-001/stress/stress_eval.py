#!/usr/bin/env python3
"""
Stress evaluator for bin-packing solutions.
Uses the same validation and scoring logic as score.py on synthetic stress instances.
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile

PER_INSTANCE_TIMEOUT_S = 10

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


def run_instance(inst, solution_path, runner_path):
    payload = json.dumps(
        {
            "items": inst["items"],
            "capacity": inst["capacity"],
            "solution_path": os.path.abspath(solution_path),
        }
    )
    with tempfile.TemporaryDirectory() as neutral_cwd:
        try:
            proc = subprocess.run(
                [sys.executable, runner_path],
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
    if "error" in out:
        return 0.0, None, out["error"][:300]
    reason = validate(out["bins"], inst["items"], inst["capacity"])
    if reason is not None:
        return 0.0, None, reason
    lb = max(math.ceil(sum(inst["items"]) / inst["capacity"]), 1)
    return lb / len(out["bins"]), len(out["bins"]), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solution", required=True)
    ap.add_argument("--json", action="store_true", help="output JSON")
    args = ap.parse_args()

    if not os.path.exists(args.solution):
        print(f"solution file not found: {args.solution}", file=sys.stderr)
        sys.exit(2)

    # Load stress instances
    stress_dir = os.path.dirname(os.path.abspath(__file__))
    instances_path = os.path.join(stress_dir, "instances", "instances.json")
    if not os.path.exists(instances_path):
        print(f"stress instances not found at {instances_path}", file=sys.stderr)
        sys.exit(4)

    with open(instances_path) as f:
        instances = json.load(f)

    with tempfile.NamedTemporaryFile("w", suffix="_runner.py", delete=False) as rf:
        rf.write(RUNNER_SRC)
        runner_path = rf.name
    try:
        scores = []
        errors = []
        for inst in instances:
            score, bins_used, error = run_instance(inst, args.solution, runner_path)
            if error:
                errors.append({"name": inst["name"], "error": error})
            scores.append(score)
    finally:
        os.unlink(runner_path)

    stress_score = sum(scores) / len(scores) if scores else 0.0
    report = {
        "stress_score": round(stress_score, 6),
        "n_instances": len(instances),
        "errors": errors,
    }
    print(json.dumps(report))


if __name__ == "__main__":
    main()
