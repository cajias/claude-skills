#!/usr/bin/env python3
"""rsi-aggregate.py — robust score aggregation + reward-hack outlier detection.
Part of the immutable rsi-loop harness (outer loop only).

Two jobs, both on the OUTER-loop side of the harness/agent boundary (so a
generation cannot influence them):

1. Robust aggregation across seeds. Tiny private splits are noisy (PLAN.md §7),
   so a single lucky or hacked seed must not drive acceptance. For each task we
   take the MEDIAN private score across seeds; the run-level aggregate is the
   mean of per-task medians. With >=3 seeds we also report a trimmed mean that
   drops the single highest score — the paper's "statistical removal of too-good
   results" (reward-hack defense layer 3), applied to the seed distribution.

2. Too-good outlier flagging for the verifier. Given per-INSTANCE private scores
   for a task, flag any instance whose score sits far above the task's own
   distribution (> median + k*MAD, k configurable). An instance that is suddenly
   perfect while its siblings sit at baseline is the fingerprint of
   instance-specific hard-coding; the verifier treats a flag as refutation
   evidence, not proof. This is DETECTION (the harness cannot prevent a write
   under a shared uid), consistent with the integrity model.

3. Battery-resolution power gate (§6.1.3, the precondition for ANY verdict — the
   exact check M5 skipped). Given per-INSTANCE private scores of a reference
   solution per task, assert (1) each task's bootstrap SE ≤ its se_max ceiling
   and (2) a planted true Δ=0.03 between two synthetic scaffolds is resolvable at
   α=0.05 by a paired bootstrap over the pooled private instances. If either
   fails the verdict is "underpowered — inconclusive" (never "not supported").
   This lives here because it is a property of the private splits the aggregator
   already bootstraps; the ignition-instrument power calc (MDE/K) is separate
   (rsi-ignition.py power, §6.1.6). Bootstraps are seeded → deterministic.

Usage:
    # Robust cross-seed aggregate for selection:
    echo '{"tasks": {"bin-packing": {"seeds": [0.94, 0.95, 0.94]}, ...}}' \
        | rsi-aggregate.py --aggregate

    # Too-good instance outliers for the verifier (one task):
    echo '{"per_instance": [0.5, 0.52, 0.48, 1.0]}' \
        | rsi-aggregate.py --flag-outliers [--k 3.0]

    # Battery power gate (per-task se_max defaults 0.02; pass 0.025 per task):
    echo '{"tasks": {"bin-packing": {"per_instance": [...], "se_max": 0.02}}}' \
        | rsi-aggregate.py --power-check [--planted-delta 0.03] [--alpha 0.05]

Output: JSON on stdout. Exit 0 on success (for --power-check, only when
pass:true), 1 when --power-check reports pass:false, 2 on usage/parse error.
"""
import argparse
import json
import random
import statistics
import sys

DEFAULT_SE_MAX = 0.02   # §6.1.3 selection-family ceiling (instruction-routing passes 0.025)
BOOTSTRAP_B = 2000      # bootstrap resamples (seeded → deterministic)
BOOTSTRAP_SEED = 20260727


def median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def trimmed_mean_drop_top(xs):
    """Mean after removing the single highest value (the 'too good' one).

    Only meaningful with >=3 samples; otherwise returns the plain mean.
    """
    if len(xs) < 3:
        return sum(xs) / len(xs) if xs else 0.0
    s = sorted(xs)[:-1]  # drop the max
    return sum(s) / len(s)


def mad(xs, med):
    """Median absolute deviation — a robust spread estimate."""
    return median([abs(x - med) for x in xs])


def aggregate(payload):
    tasks = payload.get("tasks", {})
    if not tasks:
        raise ValueError("no tasks to aggregate")
    per_task = {}
    for name, rec in tasks.items():
        seeds = rec.get("seeds", [])
        if not seeds:
            raise ValueError(f"task {name} has no seed scores")
        per_task[name] = {
            "median": round(median(seeds), 6),
            "mean": round(sum(seeds) / len(seeds), 6),
            "trimmed_mean_drop_top": round(trimmed_mean_drop_top(seeds), 6),
            "n_seeds": len(seeds),
            "spread": round(max(seeds) - min(seeds), 6),
        }
    medians = [t["median"] for t in per_task.values()]
    return {
        # Selection statistic: mean of per-task medians (robust to a single
        # outlier seed on any one task).
        "private_aggregate": round(sum(medians) / len(medians), 6),
        "per_task": per_task,
        "method": "mean-of-per-task-medians",
        "note": (
            "single-seed run: median==score, no seed-level outlier removal possible"
            if all(t["n_seeds"] < 3 for t in per_task.values())
            else "multi-seed: per-task median used; trimmed_mean_drop_top reported for audit"
        ),
    }


def flag_outliers(payload, k):
    scores = payload.get("per_instance", [])
    if not scores:
        raise ValueError("no per_instance scores to check")
    med = median(scores)
    spread = mad(scores, med)
    # With zero spread (all equal) nothing is an outlier. Guard k*0 == 0 so an
    # all-1.0 or all-baseline vector never trips the flag.
    threshold = med + k * spread if spread > 1e-9 else 1.0 + 1e-9
    outliers = [
        {"index": i, "score": s}
        for i, s in enumerate(scores)
        if s > threshold and s > med
    ]
    return {
        "median": round(med, 6),
        "mad": round(spread, 6),
        "threshold": round(threshold, 6),
        "k": k,
        "too_good_outliers": outliers,
        "flagged": bool(outliers),
        "note": (
            "one or more instances score far above the task's own distribution — "
            "possible instance-specific hard-coding; verify the mechanism"
            if outliers
            else "no too-good instance outliers"
        ),
    }


def _bootstrap_means(vec, b, rng):
    """b bootstrap resamples of the mean of vec, using the given seeded RNG."""
    n = len(vec)
    means = []
    for _ in range(b):
        acc = 0.0
        for _ in range(n):
            acc += vec[rng.randrange(n)]
        means.append(acc / n)
    return means


def power_check(payload, planted_delta, alpha, b=BOOTSTRAP_B, seed=BOOTSTRAP_SEED):
    """Battery-resolution gate (§6.1.3). Two assertions:

    (1) each task's private bootstrap SE (stdev of the bootstrap means) ≤ se_max;
    (2) a planted true Δ is resolvable — pool every task's per_instance scores,
        compare the pool against itself shifted by +planted_delta (clamped to
        [0,1]) via a PAIRED bootstrap of the mean difference, and require the
        one-sided (1−alpha) lower confidence bound to exclude 0. A saturated
        (near-ceiling) battery collapses the paired diff toward 0 and fails this,
        which is exactly the non-saturating precondition being enforced.

    verdict "powered" iff all tasks pass SE AND the planted Δ resolves; otherwise
    "underpowered — inconclusive".
    """
    tasks = payload.get("tasks", {})
    if not tasks:
        raise ValueError("no tasks to power-check")
    per_task = {}
    pooled = []
    all_pass = True
    for name, rec in tasks.items():
        vec = rec.get("per_instance", [])
        if not vec:
            raise ValueError(f"task {name} has no per_instance scores")
        se_max = rec.get("se_max", DEFAULT_SE_MAX)
        se = statistics.pstdev(_bootstrap_means(vec, b, random.Random(seed)))
        passed = se <= se_max
        all_pass = all_pass and passed
        per_task[name] = {"n": len(vec), "se": round(se, 6), "se_max": se_max, "pass": passed}
        pooled.extend(vec)

    diffs = [min(x + planted_delta, 1.0) - x for x in pooled]
    means = sorted(_bootstrap_means(diffs, b, random.Random(seed + 1)))
    ci_lower = means[int(alpha * len(means))]  # one-sided (1−alpha) lower bound
    resolved = ci_lower > 0.0
    all_pass = all_pass and resolved

    return {
        "verdict": "powered" if all_pass else "underpowered — inconclusive",
        "pass": all_pass,
        "per_task": per_task,
        "planted_delta": {
            "delta": planted_delta,
            "alpha": alpha,
            "ci_lower_one_sided": round(ci_lower, 6),
            "resolved": resolved,
            "n_pooled": len(pooled),
        },
        "note": (
            "battery resolves per-task SE within budget and a planted 0.03 effect "
            "at the given alpha — safe to render a verdict"
            if all_pass
            else "battery cannot resolve the planted effect or a task's SE exceeds "
            "budget — any Level-2 verdict would be underpowered, report inconclusive"
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--aggregate", action="store_true", help="robust cross-seed aggregate")
    mode.add_argument("--flag-outliers", action="store_true", help="too-good instance outliers")
    mode.add_argument("--power-check", action="store_true", help="battery-resolution power gate")
    ap.add_argument("--k", type=float, default=3.0, help="MAD multiplier for outlier flag")
    ap.add_argument("--planted-delta", type=float, default=0.03, help="planted effect size for --power-check")
    ap.add_argument("--alpha", type=float, default=0.05, help="significance level for --power-check")
    args = ap.parse_args()

    try:
        payload = json.load(sys.stdin)
    except ValueError as e:
        print(f"rsi-aggregate: bad JSON on stdin: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        if args.aggregate:
            out = aggregate(payload)
        elif args.flag_outliers:
            out = flag_outliers(payload, args.k)
        else:
            out = power_check(payload, args.planted_delta, args.alpha)
    except ValueError as e:
        print(f"rsi-aggregate: {e}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(out, indent=1))
    # --power-check is a gate: non-zero exit lets a shell caller block a verdict.
    if args.power_check and not out["pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
