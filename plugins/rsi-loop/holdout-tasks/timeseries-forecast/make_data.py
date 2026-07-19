#!/usr/bin/env python3
"""Deterministic generator for the timeseries-forecast holdout task data.

Run:  python3 make_data.py   (rewrites public/instances.json, private/instances.json)

Pure standard library, fully seeded (a Numerical-Recipes LCG, no `random`, no
clock) — reproducible byte-for-byte. This is a FAR-OOD SECOND-ORDER-
GENERALIZATION holdout (a WeatherBench-2 analog): the rsi-loop outer loop never
trains on it, and it is a different domain (numeric time-series forecasting)
from the training battery. The best inner agent is later run here to measure
whether its research policy transfers.

Each series is  value(t) = level + slope*t + amp*sin(2*pi*t/period + phase)
                            + small noise.
The scorer splits it into `history` (the first ~30-40 points) and `future`
(the next ~6-8 points), and grades a forecast by a smooth skill ratio against
the naive persistence ("repeat the last value") baseline:

    score = MAE_persistence / (MAE_persistence + MAE_solution)

Persistence scores ~0.5 by construction. A flat mean forecast scores around or
below 0.5 (it ignores both trend and seasonality). A forecaster that models the
trend and the seasonal cycle scores well above 0.5. The instances are seeded so
that gap is wide and stable across the public and private splits.
"""
import json
import math
import os


def lcg(seed):
    """Numerical-Recipes LCG as an endless stream of floats in [0, 1)."""
    s = seed & 0x7FFFFFFF
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


def frange(rng, lo, hi):
    return lo + (hi - lo) * next(rng)


def gen_series(rng, name, hist_len, horizon):
    level = frange(rng, 5.0, 20.0)
    slope = frange(rng, 0.15, 0.6) * (1 if next(rng) < 0.7 else -1)
    amp = frange(rng, 3.0, 8.0)
    period = float(4 + int(next(rng) * 6))     # integer period in 4..9
    phase = frange(rng, 0.0, 2 * math.pi)
    noise_scale = frange(rng, 0.3, 0.9)

    total = hist_len + horizon
    series = []
    for t in range(total):
        noise = (next(rng) * 2 - 1) * noise_scale
        v = level + slope * t + amp * math.sin(2 * math.pi * t / period + phase) + noise
        series.append(round(v, 4))
    return {"name": name, "history": series[:hist_len], "future": series[hist_len:]}


def main():
    here = os.path.dirname(os.path.abspath(__file__))

    pub_rng = lcg(70012345)
    pub_specs = [(30, 6), (34, 7), (38, 8), (32, 6), (36, 7), (40, 8), (33, 6), (37, 8)]
    public = [gen_series(pub_rng, f"pub-{i}", h, hz) for i, (h, hz) in enumerate(pub_specs)]

    prv_rng = lcg(80054321)
    prv_specs = [(31, 6), (35, 7), (39, 8), (32, 7), (36, 6), (40, 8), (34, 7), (38, 8)]
    private = [gen_series(prv_rng, f"prv-{i}", h, hz) for i, (h, hz) in enumerate(prv_specs)]

    os.makedirs(os.path.join(here, "public"), exist_ok=True)
    os.makedirs(os.path.join(here, "private"), exist_ok=True)
    with open(os.path.join(here, "public", "instances.json"), "w") as f:
        json.dump(public, f, indent=1)
    with open(os.path.join(here, "private", "instances.json"), "w") as f:
        json.dump(private, f, indent=1)

    def mae(pred, fut):
        return sum(abs(p - y) for p, y in zip(pred, fut)) / len(fut)

    # Persistence and mean baselines, reported so a reviewer sees the headroom.
    for tag, data in (("public", public), ("private", private)):
        persist_scores, mean_scores = [], []
        for d in data:
            hz = len(d["future"])
            persist = [d["history"][-1]] * hz
            meanf = [sum(d["history"]) / len(d["history"])] * hz
            mp = mae(persist, d["future"])
            mm = mae(meanf, d["future"])
            persist_scores.append(mp / (mp + mp) if mp else 1.0)  # always 0.5
            mean_scores.append(mp / (mp + mm) if (mp + mm) else 1.0)
        print(f"{tag}: n={len(data)} persistence-self={sum(persist_scores)/len(persist_scores):.3f} "
              f"mean-forecast={sum(mean_scores)/len(mean_scores):.3f}")


if __name__ == "__main__":
    main()
