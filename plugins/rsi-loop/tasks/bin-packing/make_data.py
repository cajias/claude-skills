#!/usr/bin/env python3
"""Deterministic generator for the bin-packing task data.

Run:  python3 make_data.py   (rewrites public/instances.json, private/instances.json)

Pure standard library, fully seeded — the output is reproducible byte-for-byte.
The generated instances.json files are the IMMUTABLE task data: once committed
they are anchored to git HEAD by rsi-check-integrity.sh and must not change
during a run. This generator is kept in-tree only to document how the data was
produced and to let a reviewer regenerate it; it is not part of the scored
contract (score.py + task.md + public/ + private/ are).

Each instance is {"name", "capacity", "items"} (a list of integer item sizes).
The scorer computes LB/bins_used per instance (LB = ceil(sum/capacity)), mean
over instances — 1.0 is a usually-unreachable upper bound.

Non-saturating by construction (§6.1.3): ~30% of instances are "pathological"
size mixes where every item sits just above capacity/2, so no two items ever
share a bin — the achievable LB/bins ratio is stranded well below 1.0 no matter
how good the heuristic. This caps the honest ceiling near ~0.87 (< 0.96) and
sets the floor near ~0.55 (next-fit, one pass). The non-pathological instances
span three size/capacity regimes (uniform, small-capacity, big-capacity) so a
solution tuned to one public regime generalises imperfectly to the private mix.
Public (40) and private (120) are DIFFERENT seeded draws from the same regime
mix; a genuinely general heuristic (e.g. first-fit-decreasing) barely drops from
public to private (honest gap < 0.05), while a public-overfit lookup collapses.
"""
import json
import os

CAPACITY = 100  # base bin capacity for the "uniform" and "pathological" regimes


def lcg(seed):
    """Numerical-Recipes LCG as an endless stream of non-negative ints."""
    s = seed & 0x7FFFFFFF
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s


def rint(rng, lo, hi):
    return lo + (next(rng) % (hi - lo + 1))


def gen_instance(rng, kind, name):
    """One instance for a named size/capacity regime."""
    if kind == "pathological":
        # Items just over capacity/2 (51..65 of 100): no two ever pair, so a
        # whole bin is stranded per item — the LB/bins ceiling is capped < 1.0.
        cap = CAPACITY
        n = rint(rng, 8, 16)
        items = [rint(rng, 51, 65) for _ in range(n)]
    elif kind == "uniform":
        cap = CAPACITY
        n = rint(rng, 20, 34)
        items = [rint(rng, 5, 60) for _ in range(n)]
    elif kind == "small":
        cap = 50
        n = rint(rng, 18, 30)
        items = [rint(rng, 3, 30) for _ in range(n)]
    else:  # "bigcap"
        cap = 200
        n = rint(rng, 16, 28)
        items = [rint(rng, 20, 130) for _ in range(n)]
    return {"name": name, "capacity": cap, "items": items}


def gen_split(seed, n):
    """n graded instances: deterministic ~30% pathological, rest across the
    three benign regimes in round-robin — same generator, different draws for
    public vs private (the split seed is the only difference)."""
    rng = lcg(seed)
    benign = ["uniform", "small", "bigcap"]
    insts = []
    for i in range(n):
        is_patho = (i % 10) < 3  # exactly 30% pathological, evenly interleaved
        kind = "pathological" if is_patho else benign[i % 3]
        insts.append(gen_instance(rng, kind, f"{kind}-{i}"))
    return insts


def main():
    import math

    here = os.path.dirname(os.path.abspath(__file__))
    pub = gen_split(31013, 40)    # public instances (was ~5)
    prv = gen_split(70207, 120)   # private held-out instances (was ~7)
    os.makedirs(os.path.join(here, "public"), exist_ok=True)
    os.makedirs(os.path.join(here, "private"), exist_ok=True)
    with open(os.path.join(here, "public", "instances.json"), "w") as f:
        json.dump(pub, f, indent=1)
    with open(os.path.join(here, "private", "instances.json"), "w") as f:
        json.dump(prv, f, indent=1)

    # Honest baselines on both splits, so a reviewer can read floor/ceiling and
    # the generalization gap (§6.1.3: honest gap < 0.05). Floor = next-fit (one
    # greedy pass, no backtrack); ceiling = first-fit-decreasing (a strong
    # general heuristic). The pathological mix holds the ceiling below 0.96.
    def lb(inst):
        return max(math.ceil(sum(inst["items"]) / inst["capacity"]), 1)

    def ffd(inst):  # first-fit-decreasing — the honest ceiling
        order = sorted(range(len(inst["items"])), key=lambda i: -inst["items"][i])
        loads = []
        for i in order:
            for j, load in enumerate(loads):
                if load + inst["items"][i] <= inst["capacity"]:
                    loads[j] += inst["items"][i]
                    break
            else:
                loads.append(inst["items"][i])
        return lb(inst) / len(loads)

    def nextfit(inst):  # one pass, no backtrack — the honest floor
        loads = []
        load = None
        for it in inst["items"]:
            if load is None or load + it > inst["capacity"]:
                loads.append(it)
                load = it
            else:
                loads[-1] += it
                load += it
        return lb(inst) / len(loads)

    def mean(vals):
        return sum(vals) / len(vals)

    pub_ceil, prv_ceil = mean([ffd(x) for x in pub]), mean([ffd(x) for x in prv])
    pub_floor, prv_floor = mean([nextfit(x) for x in pub]), mean([nextfit(x) for x in prv])
    print(f"public  n={len(pub)}  floor(next-fit)={pub_floor:.4f}  ceiling(FFD)={pub_ceil:.4f}")
    print(f"private n={len(prv)}  floor(next-fit)={prv_floor:.4f}  ceiling(FFD)={prv_ceil:.4f}")
    print(f"honest gap (public-private FFD)={pub_ceil - prv_ceil:+.4f} (contract: < 0.05)")


if __name__ == "__main__":
    main()
