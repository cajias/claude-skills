#!/usr/bin/env python3
"""Deterministic generator for the tabular-ring holdout task data.

Run:  python3 make_data.py   (rewrites public/instances.json, private/instances.json)

Pure standard library, fully seeded — the output is reproducible byte-for-byte.
This is a SECOND-ORDER-GENERALIZATION holdout: the rsi-loop outer loop never
trains on it. The best inner agent is later run here to measure whether a
research policy that helped on the training battery also transfers to a new
decision boundary.

The label rule is a RING (annulus) boundary on two of the six features:

    label = 1  iff  0.3 < (x0*x0 + x1*x1) < 0.85    else 0

with the other four features (x2..x5) pure noise in [-1, 1] and ~4% label noise.
A ring is not linearly separable and not axis-aligned, so a single linear
threshold or a shallow axis-split scores near the majority baseline; a distance-
based model (k-NN) or one that engineers the radius feature does much better,
but only if it is not dragged down by the four irrelevant dimensions. That
naive-to-strong gap is the headroom the outer loop's inner-agent research must
exploit — the same shape of headroom as the XOR training task, but a different
boundary the loop has never optimized against.
"""
import json
import os


def lcg(seed):
    """Numerical-Recipes LCG as an endless stream of floats in [0, 1)."""
    s = seed & 0x7FFFFFFF
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


def gen(n, rng):
    rows = []
    for _ in range(n):
        x0 = round(next(rng) * 2 - 1, 4)  # [-1, 1] signal
        x1 = round(next(rng) * 2 - 1, 4)  # [-1, 1] signal
        x2 = round(next(rng) * 2 - 1, 4)  # [-1, 1] noise
        x3 = round(next(rng) * 2 - 1, 4)  # [-1, 1] noise
        x4 = round(next(rng) * 2 - 1, 4)  # [-1, 1] noise
        x5 = round(next(rng) * 2 - 1, 4)  # [-1, 1] noise
        r2 = x0 * x0 + x1 * x1
        label = 1 if (0.3 < r2 < 0.85) else 0    # ring / annulus boundary
        if next(rng) < 0.04:                     # ~4% label noise (irreducible)
            label ^= 1
        rows.append([x0, x1, x2, x3, x4, x5, label])
    return rows


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    rng = lcg(20260719)
    train = gen(200, rng)   # public training rows (features + labels visible)
    test = gen(80, rng)     # private held-out test rows (labels never leave scorer)

    feats = ["x0", "x1", "x2", "x3", "x4", "x5"]
    os.makedirs(os.path.join(here, "public"), exist_ok=True)
    os.makedirs(os.path.join(here, "private"), exist_ok=True)
    with open(os.path.join(here, "public", "instances.json"), "w") as f:
        json.dump({"features": feats, "rows": train}, f, indent=1)
    with open(os.path.join(here, "private", "instances.json"), "w") as f:
        json.dump({"features": feats, "rows": test}, f, indent=1)

    def majority(rows):
        ones = sum(r[-1] for r in rows)
        return max(ones, len(rows) - ones) / len(rows)

    print(f"train n={len(train)} majority-baseline={majority(train):.4f} "
          f"positives={sum(r[-1] for r in train)}")
    print(f"test  n={len(test)} majority-baseline={majority(test):.4f} "
          f"positives={sum(r[-1] for r in test)}")


if __name__ == "__main__":
    main()
