#!/usr/bin/env python3
"""Deterministic generator for the interval-scheduling holdout data.

Run:  python3 make_data.py   (rewrites public/instances.json, private/instances.json)

Pure standard library, fully seeded (a Numerical-Recipes LCG, no `random`, no
clock) — reproducible byte-for-byte. This is a SECOND-ORDER-GENERALIZATION
holdout: the rsi-loop outer loop never trains on it; the best inner agent is
later run here to measure whether its research policy transfers.

Each instance is a set of intervals [start, end] (start < end). The task is to
select a maximum-size subset of mutually non-overlapping intervals. Two
intervals overlap iff they share more than a single endpoint, so touching
intervals like [1,3] and [3,5] may both be selected.

Headroom: the classical earliest-FINISH-time greedy is provably optimal and
scores 1.0. Naive heuristics leave real slack — selecting by earliest START, or
by shortest length, or taking everything, all score well below 1.0 because they
grab a long early interval that blocks several later short ones. The instances
are seeded to make that gap wide and stable.
"""
import json
import os


def lcg(seed):
    """Numerical-Recipes LCG as an endless stream of ints."""
    s = seed & 0x7FFFFFFF
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s


def rint(rng, lo, hi):
    return lo + (next(rng) % (hi - lo + 1))


def gen_instance(rng, name, n, span):
    """Generate n intervals over [0, span). Mixes long 'blocker' intervals with
    clusters of short intervals so that greedy-by-start is clearly suboptimal."""
    intervals = []
    # A few long intervals that a start-time-greedy will grab early and regret.
    n_long = max(2, n // 5)
    for _ in range(n_long):
        s = rint(rng, 0, span - 1)
        length = rint(rng, span // 3, max(span // 3 + 1, span // 2))
        e = min(s + length, span)
        if e <= s:
            e = s + 1
        intervals.append([s, e])
    # Many short intervals.
    while len(intervals) < n:
        s = rint(rng, 0, span - 2)
        length = rint(rng, 1, max(2, span // 12))
        e = min(s + length, span)
        if e <= s:
            e = s + 1
        intervals.append([s, e])
    # Shuffle deterministically (Fisher-Yates with the LCG) so index order does
    # not encode the answer.
    for i in range(len(intervals) - 1, 0, -1):
        j = next(rng) % (i + 1)
        intervals[i], intervals[j] = intervals[j], intervals[i]
    return {"name": name, "intervals": intervals}


def main():
    here = os.path.dirname(os.path.abspath(__file__))

    pub_rng = lcg(31337001)
    pub_specs = [(10, 30), (14, 40), (18, 50), (12, 35), (20, 60),
                 (16, 45), (22, 70), (15, 40), (24, 80)]
    public = [gen_instance(pub_rng, f"pub-{i}", n, span)
              for i, (n, span) in enumerate(pub_specs)]

    prv_rng = lcg(90210777)
    prv_specs = [(11, 33), (17, 48), (21, 65), (13, 38), (19, 55),
                 (23, 75), (25, 90), (14, 42), (26, 95)]
    private = [gen_instance(prv_rng, f"prv-{i}", n, span)
               for i, (n, span) in enumerate(prv_specs)]

    os.makedirs(os.path.join(here, "public"), exist_ok=True)
    os.makedirs(os.path.join(here, "private"), exist_ok=True)
    with open(os.path.join(here, "public", "instances.json"), "w") as f:
        json.dump(public, f, indent=1)
    with open(os.path.join(here, "private", "instances.json"), "w") as f:
        json.dump(private, f, indent=1)

    # Report the optimal (earliest-finish greedy) vs a naive earliest-start size
    # so a reviewer can see the headroom without running score.py.
    def opt_size(intervals):
        order = sorted(intervals, key=lambda iv: (iv[1], iv[0]))
        c, last = 0, None
        for s, e in order:
            if last is None or s >= last:
                c += 1
                last = e
        return c

    def start_size(intervals):
        order = sorted(intervals, key=lambda iv: (iv[0], iv[1]))
        c, last = 0, None
        for s, e in order:
            if last is None or s >= last:
                c += 1
                last = e
        return c

    for tag, data in (("public", public), ("private", private)):
        ratios = [start_size(d["intervals"]) / opt_size(d["intervals"]) for d in data]
        print(f"{tag}: n={len(data)} earliest-start/optimal mean ratio={sum(ratios)/len(ratios):.4f}")


if __name__ == "__main__":
    main()
