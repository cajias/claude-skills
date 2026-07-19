#!/usr/bin/env python3
"""Immutable scorer for the tabular-classification task. Part of the rsi-loop
harness: generations may read this file but must never modify it.

Usage:
    python3 score.py --public  --solution solution.py [--json]
    python3 score.py --private --solution solution.py [--json]   # outer loop only

Prints a JSON report to stdout and exits 0 (a low score is a report, not an
error). Exit codes: 2 = usage error, 3 = private split refused, 4 = missing
instance data.

Solution contract (see task.md):

    def predict(train, test) -> list[int]

    train : list of rows [x0, x1, x2, x3, x4, x5, label]   (labels visible)
    test  : list of rows [x0, x1, x2, x3, x4, x5]           (features only)
    return: list of predicted 0/1 labels, one per test row, in order.

Public score is a seeded 5-fold cross-validation accuracy over the public
training rows: the solution never sees a held-out fold's labels, so there is no
answer key to memorize — the public signal rewards a model that generalizes.
Private score is accuracy on a genuinely held-out test set (private/), trained
on the full public set. The private labels never enter the solution subprocess
and never appear in an inner-agent sandbox (which contains no private/).

Validation happens here, outside the solution subprocess: a solution cannot fake
accuracy — it returns predictions, the scorer compares them to labels it holds.
"""
import argparse
import json
import os
import subprocess
import sys

PER_CALL_TIMEOUT_S = 15
N_FOLDS = 5

# The child imports the solution and calls predict(); it never scores. It reads
# {"train", "test", "solution_path"} on stdin and writes {"pred": [...]} or
# {"error": ...} on stdout.
RUNNER_SRC = r"""
import json, sys, importlib.util
spec_in = json.load(sys.stdin)
try:
    spec = importlib.util.spec_from_file_location("solution", spec_in["solution_path"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pred = mod.predict(spec_in["train"], spec_in["test"])
    print(json.dumps({"pred": list(pred)}))
except Exception as e:
    print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
"""


def load_rows(path):
    with open(path) as f:
        blob = json.load(f)
    if not isinstance(blob, dict) or "rows" not in blob or not blob["rows"]:
        return None
    return blob["rows"]


def run_predict(train, test, solution_path, neutral_cwd):
    """Return (predictions, error). predictions is None on error."""
    # `test` is already features-only (callers strip labels before scoring).
    payload = json.dumps(
        {
            "train": train,
            "test": test,
            "solution_path": os.path.abspath(solution_path),
        }
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", RUNNER_SRC],
            input=payload,
            capture_output=True,
            text=True,
            timeout=PER_CALL_TIMEOUT_S,
            cwd=neutral_cwd,
        )
    except subprocess.TimeoutExpired:
        return None, f"timeout after {PER_CALL_TIMEOUT_S}s"
    try:
        out = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None, f"unparseable solution output: {proc.stderr.strip()[:200]}"
    if not isinstance(out, dict) or "pred" not in out:
        err = out.get("error") if isinstance(out, dict) else None
        return None, (err or "solution produced no 'pred' output")[:300]
    return out["pred"], None


def accuracy(pred, labels):
    """Fraction correct, or (0.0, reason) if predictions are malformed."""
    if not isinstance(pred, list) or len(pred) != len(labels):
        return 0.0, f"expected {len(labels)} predictions, got {len(pred) if isinstance(pred, list) else type(pred).__name__}"
    correct = 0
    for p, y in zip(pred, labels):
        if isinstance(p, bool):
            p = int(p)
        if not isinstance(p, int):
            try:
                p = int(p)
            except (ValueError, TypeError):
                return 0.0, f"non-integer prediction: {p!r}"
        if p == y:
            correct += 1
    return correct / len(labels), None


def score_public(task_dir, solution_path, neutral_cwd):
    """Seeded 5-fold CV accuracy over public training rows."""
    rows = load_rows(os.path.join(task_dir, "public", "instances.json"))
    if rows is None:
        return None
    per_fold = []
    for f in range(N_FOLDS):
        test_idx = [i for i in range(len(rows)) if i % N_FOLDS == f]
        train_rows = [rows[i] for i in range(len(rows)) if i % N_FOLDS != f]
        test_rows = [rows[i][:-1] for i in test_idx]   # strip labels from test
        test_labels = [rows[i][-1] for i in test_idx]
        pred, err = run_predict(train_rows, test_rows, solution_path, neutral_cwd)
        if err is not None:
            per_fold.append({"name": f"fold-{f}", "score": 0.0, "n": len(test_labels), "error": err})
            continue
        acc, reason = accuracy(pred, test_labels)
        per_fold.append({"name": f"fold-{f}", "score": round(acc, 6), "n": len(test_labels), "error": reason})
    return per_fold


def score_private(task_dir, solution_path, neutral_cwd):
    """Accuracy on the held-out private test set, trained on the full public set."""
    train_rows = load_rows(os.path.join(task_dir, "public", "instances.json"))
    test_all = load_rows(os.path.join(task_dir, "private", "instances.json"))
    if train_rows is None or test_all is None:
        return None
    test_rows = [r[:-1] for r in test_all]
    test_labels = [r[-1] for r in test_all]
    pred, err = run_predict(train_rows, test_rows, solution_path, neutral_cwd)
    if err is not None:
        return [{"name": "private-holdout", "score": 0.0, "n": len(test_labels), "error": err}]
    acc, reason = accuracy(pred, test_labels)
    return [{"name": "private-holdout", "score": round(acc, 6), "n": len(test_labels), "error": reason}]


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
            "harness (RSI_OUTER_LOOP=1). Inner agents optimize the public CV score.",
            file=sys.stderr,
        )
        sys.exit(3)

    task_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(args.solution):
        print(f"solution file not found: {args.solution}", file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(os.path.join(task_dir, split_name, "instances.json")):
        print(f"no {split_name} instances for tabular-classification", file=sys.stderr)
        sys.exit(4)

    import tempfile

    with tempfile.TemporaryDirectory() as neutral_cwd:
        if args.private:
            per_instance = score_private(task_dir, args.solution, neutral_cwd)
        else:
            per_instance = score_public(task_dir, args.solution, neutral_cwd)
    if per_instance is None:
        print(f"no usable {split_name} instances for tabular-classification", file=sys.stderr)
        sys.exit(4)

    report = {
        "task": "tabular-classification",
        "split": split_name,
        "n_instances": len(per_instance),
        "score": round(sum(p["score"] for p in per_instance) / len(per_instance), 6),
        "per_instance": per_instance,
    }
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
