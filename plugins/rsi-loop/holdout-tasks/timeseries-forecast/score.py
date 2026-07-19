#!/usr/bin/env python3
"""Immutable scorer for the timeseries-forecast holdout task. Part of the
rsi-loop harness: generations may read this file but must never modify it.

Usage:
    python3 score.py --public  --solution solution.py [--json]
    python3 score.py --private --solution solution.py [--json]   # outer loop only

Prints a JSON report to stdout and exits 0 (a low score is a report, not an
error). Exit codes: 2 = usage error, 3 = private split refused, 4 = missing
instance data.

This is a FAR-OOD SECOND-ORDER-GENERALIZATION holdout (a WeatherBench-2 analog):
the rsi-loop outer loop never trains on it, and it lives in a different domain
(numeric time-series forecasting) from the training battery. The best inner
agent is later run here to measure whether its research policy transfers.

Solution contract (see task.md):

    def forecast(history: list[float], horizon: int) -> list[float]

    history : the observed series so far (oldest first).
    horizon : how many future steps to predict.
    return  : a list of exactly `horizon` predicted values, in order.

Per-instance score uses a SMOOTH skill ratio against the naive persistence
("repeat the last value") forecast:

    score = MAE_persistence / (MAE_persistence + MAE_solution)

which is 0.5 when the solution ties persistence, -> 1.0 as it becomes perfect,
and -> 0.0 when it is much worse. A forecast that is not a list of exactly
`horizon` finite numbers (wrong length, NaN/inf, non-number, exception,
timeout) scores 0 for that instance.

Validation and MAE happen here, outside the solution subprocess: the scorer
holds the true future values; the solution only returns predictions.
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile

PER_INSTANCE_TIMEOUT_S = 10

# The child imports the solution and calls forecast(); it never scores. It reads
# {"history", "horizon", "solution_path"} on stdin and writes {"pred": [...]} or
# {"error": ...} on stdout.
RUNNER_SRC = r"""
import json, sys, importlib.util
spec_in = json.load(sys.stdin)
try:
    spec = importlib.util.spec_from_file_location("solution", spec_in["solution_path"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pred = mod.forecast(spec_in["history"], spec_in["horizon"])
    print(json.dumps({"pred": list(pred)}))
except Exception as e:
    print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
"""


def clean_forecast(pred, horizon):
    """Return (values, None) if pred is a list of exactly `horizon` finite
    numbers, else (None, reason)."""
    if not isinstance(pred, list):
        return None, "solution did not return a list"
    if len(pred) != horizon:
        return None, f"expected {horizon} values, got {len(pred)}"
    out = []
    for v in pred:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None, f"non-numeric forecast value: {v!r}"
        if not math.isfinite(v):
            return None, f"non-finite forecast value: {v!r}"
        out.append(float(v))
    return out, None


def mae(pred, future):
    return sum(abs(p - y) for p, y in zip(pred, future)) / len(future)


def run_instance(inst, solution_path, neutral_cwd):
    """Return (score, mae_sol, error). score/mae_sol are None on error."""
    history = inst["history"]
    future = inst["future"]
    horizon = len(future)
    payload = json.dumps(
        {
            "history": history,
            "horizon": horizon,
            "solution_path": os.path.abspath(solution_path),
        }
    )
    # Run the embedded runner via `-c` in a neutral cwd, so the solution
    # subprocess gets no incidental access to the task directory (and therefore
    # never to private/ during private scoring).
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
    if not isinstance(out, dict) or "pred" not in out:
        err = out.get("error") if isinstance(out, dict) else None
        return 0.0, None, (err or "solution produced no 'pred' output")[:300]
    pred, reason = clean_forecast(out["pred"], horizon)
    if reason is not None:
        return 0.0, None, reason

    mae_persist = mae([history[-1]] * horizon, future)
    mae_sol = mae(pred, future)
    denom = mae_persist + mae_sol
    if denom == 0.0:
        # Both the solution and persistence are exactly perfect.
        score = 1.0
    else:
        score = mae_persist / denom
    return score, mae_sol, None


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
            score, mae_sol, error = run_instance(inst, args.solution, neutral_cwd)
            per_instance.append(
                {
                    "name": inst["name"],
                    "score": round(score, 6),
                    "mae": None if mae_sol is None else round(mae_sol, 6),
                    "horizon": len(inst["future"]),
                    "error": error,
                }
            )

    report = {
        "task": "timeseries-forecast",
        "split": split_name,
        "n_instances": len(instances),
        "score": round(sum(p["score"] for p in per_instance) / len(per_instance), 6),
        "per_instance": per_instance,
    }
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
