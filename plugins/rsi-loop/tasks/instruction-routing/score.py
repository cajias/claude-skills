#!/usr/bin/env python3
"""Immutable scorer for the instruction-routing task. Part of the rsi-loop
harness: generations may read this file but must never modify it.

Usage:
    python3 score.py --public  --solution solution.py [--json]
    python3 score.py --private --solution solution.py [--json]   # outer loop only

Prints a JSON report to stdout and exits 0 (a low score is a report, not an
error). Exit codes: 2 = usage error, 3 = private split refused, 4 = missing
case data.

Solution contract (see task.md):

    def solve(instruction: str) -> str

    instruction : one natural-language instruction (e.g. "add 3 and 5")
    return      : the exact answer as a string (e.g. "8")

Each case is scored 1 if str(solve(instruction)).strip() equals the expected
answer, else 0. The task score is the fraction of cases correct. The private
split uses the same operations with unseen phrasings and edge-case arguments,
and its cases never appear in an inner-agent sandbox — hard-coding the public
answers cannot help there.

Validation happens here, outside the solution subprocess: the scorer holds the
expected answers and the solution only returns strings.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

BATCH_TIMEOUT_S = 20

# The child imports the solution and calls solve() on each instruction, isolating
# a per-case crash so one bad case does not zero the whole battery. It reads
# {"instructions", "solution_path"} on stdin and writes {"answers": [...]} where
# each answer is {"ok": true, "value": "..."} or {"ok": false, "error": "..."}.
RUNNER_SRC = r"""
import json, sys, importlib.util
spec_in = json.load(sys.stdin)
answers = []
try:
    spec = importlib.util.spec_from_file_location("solution", spec_in["solution_path"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    solve = mod.solve
except Exception as e:
    print(json.dumps({"load_error": f"{type(e).__name__}: {e}"}))
    sys.exit(0)
for instr in spec_in["instructions"]:
    try:
        answers.append({"ok": True, "value": str(solve(instr))})
    except Exception as e:
        answers.append({"ok": False, "error": f"{type(e).__name__}: {e}"})
print(json.dumps({"answers": answers}))
"""


def load_cases(task_dir, split_name):
    path = os.path.join(task_dir, split_name, "instances.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        blob = json.load(f)
    if not isinstance(blob, dict) or "cases" not in blob or not blob["cases"]:
        return None
    return blob["cases"]


def run_batch(instructions, solution_path, neutral_cwd):
    """Return (answers, fatal_error). answers is a list aligned to instructions."""
    payload = json.dumps({"instructions": instructions, "solution_path": os.path.abspath(solution_path)})
    try:
        proc = subprocess.run(
            [sys.executable, "-c", RUNNER_SRC],
            input=payload,
            capture_output=True,
            text=True,
            timeout=BATCH_TIMEOUT_S,
            cwd=neutral_cwd,
        )
    except subprocess.TimeoutExpired:
        return None, f"timeout after {BATCH_TIMEOUT_S}s"
    try:
        out = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None, f"unparseable solution output: {proc.stderr.strip()[:200]}"
    if isinstance(out, dict) and "load_error" in out:
        return None, out["load_error"][:300]
    if not isinstance(out, dict) or "answers" not in out or not isinstance(out["answers"], list):
        return None, "solution produced no 'answers' output"
    return out["answers"], None


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
    if not os.path.exists(args.solution):
        print(f"solution file not found: {args.solution}", file=sys.stderr)
        sys.exit(2)
    cases = load_cases(task_dir, split_name)
    if cases is None:
        print(f"no usable {split_name} cases for instruction-routing", file=sys.stderr)
        sys.exit(4)

    instructions = [c["instruction"] for c in cases]
    with tempfile.TemporaryDirectory() as neutral_cwd:
        answers, fatal = run_batch(instructions, args.solution, neutral_cwd)

    per_instance = []
    if fatal is not None:
        # Whole-solution failure (import error, timeout): every case scores 0.
        for c in cases:
            per_instance.append({"name": c["name"], "score": 0.0, "error": fatal})
    else:
        for c, a in zip(cases, answers):
            if not isinstance(a, dict) or not a.get("ok"):
                err = a.get("error") if isinstance(a, dict) else "no answer"
                per_instance.append({"name": c["name"], "score": 0.0, "error": err})
                continue
            got = a["value"].strip()
            ok = got == str(c["expected"]).strip()
            per_instance.append({
                "name": c["name"],
                "score": 1.0 if ok else 0.0,
                "error": None if ok else f"expected {c['expected']!r}, got {got!r}",
            })

    report = {
        "task": "instruction-routing",
        "split": split_name,
        "n_instances": len(per_instance),
        "score": round(sum(p["score"] for p in per_instance) / len(per_instance), 6),
        "per_instance": per_instance,
    }
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
