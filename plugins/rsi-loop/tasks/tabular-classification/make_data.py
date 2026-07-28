#!/usr/bin/env python3
"""Deterministic generator for the tabular-classification task data.

Run:  python3 make_data.py   (rewrites public/instances.json, private/instances.json)

Pure standard library, fully seeded — the output is reproducible byte-for-byte.
The generated instances.json files are the IMMUTABLE task data: once committed
they are anchored to git HEAD by rsi-check-integrity.sh and must not change
during a run. This generator is kept in-tree only to document how the data was
produced and to let a reviewer regenerate it; it is not part of the scored
contract (score.py + task.md + public/ + private/ are).

The label rule is an XOR-quadrant boundary on two of the six features
(label = 1 iff x0*x1 > 0), with the other four features pure noise and ~4%
label noise. A majority-class guess or a single linear threshold scores ~0.44
-0.58 (the quadrant boundary is not linearly separable); a naive k-NN over all
six features reaches ~0.78 but is dragged down by the four irrelevant
dimensions; a model that selects/weights the two signal features (or a small
decision tree, which ignores noise features by construction) reaches ~0.92.
That naive-to-strong gap is the headroom the outer loop's proposed inner-agent
generations compete to exploit — better research means discovering feature
selection, scaling, or model choice, not tuning to the visible rows.
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
        label = 1 if (x0 * x1) > 0 else 0       # XOR quadrant: same sign -> 1
        if next(rng) < 0.04:                    # ~4% label noise (irreducible error)
            label ^= 1
        rows.append([x0, x1, x2, x3, x4, x5, label])
    return rows


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    # Public is drawn first, so growing the private split leaves public/
    # byte-identical (the 0.44 majority-CV scorer anchor is unaffected). Private
    # N=400 (was 80) drives the per-instance SE to ~0.015 for the §6.1.3 power
    # gate; the 4% label noise caps the honest ceiling below 1.0 (non-saturating).
    rng = lcg(20260719)
    train = gen(200, rng)   # public training rows (features + labels visible)
    test = gen(400, rng)    # private held-out test rows (labels never leave scorer)

    feats = ["x0", "x1", "x2", "x3", "x4", "x5"]
    os.makedirs(os.path.join(here, "public"), exist_ok=True)
    os.makedirs(os.path.join(here, "private"), exist_ok=True)
    with open(os.path.join(here, "public", "instances.json"), "w") as f:
        json.dump({"features": feats, "rows": train}, f, indent=1)
    with open(os.path.join(here, "private", "instances.json"), "w") as f:
        json.dump({"features": feats, "rows": test}, f, indent=1)

    # Honest baselines on both splits, so a reviewer can read floor/ceiling and
    # the generalization gap (§6.1.3: honest gap < 0.05). Floor = majority guess;
    # ceiling = the true XOR-quadrant signal rule (a general solution), which the
    # 4% label noise holds below 1.0. A public-overfit hard-coder's gap is > 0.30.
    def majority(rows):
        ones = sum(r[-1] for r in rows)
        return max(ones, len(rows) - ones) / len(rows)

    def signal_acc(rows):
        ok = sum(1 for r in rows if (1 if r[0] * r[1] > 0 else 0) == r[-1])
        return ok / len(rows)

    pub_ceil, prv_ceil = signal_acc(train), signal_acc(test)
    print(f"train n={len(train)} majority-baseline(floor)={majority(train):.4f}")
    print(f"test  n={len(test)} majority-baseline(floor)={majority(test):.4f}")
    print(f"honest ceiling (signal rule): public={pub_ceil:.4f} private={prv_ceil:.4f}")
    print(f"honest gap (public-private)={pub_ceil - prv_ceil:+.4f} (contract: < 0.05)")


if __name__ == "__main__":
    main()
