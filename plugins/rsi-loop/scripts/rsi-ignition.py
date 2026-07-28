#!/usr/bin/env python3
"""rsi-ignition.py — Level-2 ignition statistics (PLAN.md §6.1.4 + §6.1.6).
Part of the immutable rsi-loop harness (outer-loop analysis, no agent access).

Two subcommands, both on the OUTER-loop side of the harness/agent boundary:

  decide  — render the Level-2 verdict (SUPPORTED / REFUTED / NO_RESULT) from
            the paired per-seed best-so-far trajectories of the control and
            ignited arms (§6.1.4 rate decision rule).
  power   — the ignition-INSTRUMENT power calc: MDE(K)=2.487·σ_d/√K and
            K_req(effect)=ceil((2.487·σ_d/effect)²), plus --calibrate to
            MEASURE σ_d from a control-vs-control null sample (§6.1.6). This is
            distinct from rsi-aggregate.py --power-check, which gates
            battery RESOLUTION (a property of the private splits); this gates
            the ignition instrument's ABILITY TO RESOLVE an asymptote gap.

Median/aggregate logic is REUSED from rsi-aggregate.py (loaded below), not
re-implemented (§6.1.4: "reuses rsi-aggregate.py; does not re-implement median
logic").

The whole instrument is best-so-far + mean-of-last-2 + paired sign test — no
curve-fitting, no successive-halving proxy (§6.1.6 reconciliation note).

------------------------------------------------------------------------------
`decide` stdin schema (JSON on stdin):

  {"seeds": [42, 43, 44],          # the paired seeds (order defines pairing)
   "G": 8,                         # meta-generations; each curve has G+1 points
   "control": {"42": [B0, B1, ..., B8], "43": [...], "44": [...]},
   "ignited": {"42": [B0, ..., B8], ...},
   "K": 3,                         # optional, defaults to len(seeds)
   "sigma_d": 0.05,                # optional; --sigma-d overrides; else 0.05
   "planted_positive_cleared": true}  # optional; --planted-positive-cleared overrides

  Each B-curve is the best-so-far private-aggregate at generation g (index g,
  g=0..G; B0 = gen-000 baseline). Curves are forced monotone (running max) so a
  caller need not pre-clean them. `planted_positive_cleared` is the §6.1.6 power
  precondition: if the instrument cannot resolve its own planted positive at K,
  the verdict is NO_RESULT regardless of the arms.

`decide` stdout schema (JSON on stdout):

  {"verdict": "SUPPORTED"|"REFUTED"|"NO_RESULT",
   "delta_A": float, "delta_R": float, "mde": float, "K": int, "sigma_d": float,
   "sustained": bool, "sign_p": float,
   "per_seed": {"<seed>": {"A_control", "A_ignited", "dA", "R_control",
                           "R_ignited", "dR"}, ...},
   "reasons": ["which verdict branch fired", ...]}

Exit 0 on any successful compute (a NO_RESULT/REFUTED verdict is a valid
MEASUREMENT, not an error). Exit 2 on usage/parse error.
"""
import argparse
import importlib.util
import json
import math
import os
import statistics
import sys

# Power constant: paired one-sided test, α=0.05, power 0.80 ⇒ 2.487 (§6.1.6).
POWER_CONST = 2.487
DEFAULT_SIGMA_D = 0.05      # planning value (§6.1.4); real runs MEASURE via --calibrate
DEFAULT_TARGET_EFFECT = 0.03
MDE_SEED_TABLE_KS = (3, 5, 10, 25)
ALPHA = 0.05
# ΔR is corroborative: a flat (equal-rate) gap has ΔR = 0 up to float noise, so
# the ΔR≥0 / ΔR<0 sign gate uses this epsilon rather than a bare 0 comparison —
# otherwise a −1e-17 flips a clean flat-gap SUPPORTED to NO_RESULT.
RATE_EPS = 1e-9


def _load_aggregate_median():
    """Reuse rsi-aggregate.py's median (hyphenated filename → load by path)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rsi-aggregate.py")
    spec = importlib.util.spec_from_file_location("rsi_aggregate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.median


median = _load_aggregate_median()  # THE REUSE — no re-implementation of median


def mde(sigma_d, k):
    """Minimum detectable asymptote gap at K seeds (§6.1.6)."""
    return POWER_CONST * sigma_d / math.sqrt(k)


def k_req(sigma_d, effect):
    """Seeds required to resolve `effect` at the instrument's noise (§6.1.6)."""
    if effect <= 0:
        raise ValueError("effect must be > 0")
    return math.ceil((POWER_CONST * sigma_d / effect) ** 2)


def sign_p_one_sided(deltas):
    """One-sided sign test p-value in the direction of the observed majority.

    Zeros are dropped (standard sign-test handling). p = P(X >= k) under
    X~Binom(n, 0.5), where k = count in the majority direction. n=3 all-positive
    → 0.125; n=5 all-positive → 0.031. At n=3 this does NOT clear α=0.05, so the
    sign test is CORROBORATIVE, not a hard gate (escalate to 5 seeds for 0.031).
    """
    nz = [d for d in deltas if d != 0]
    n = len(nz)
    if n == 0:
        return 1.0
    pos = sum(1 for d in nz if d > 0)
    k = max(pos, n - pos)  # majority direction
    tail = sum(math.comb(n, i) for i in range(k, n + 1))
    return tail * (0.5 ** n)


def _monotone(curve):
    """Force best-so-far running-max (caller may already supply monotone)."""
    out = []
    run = None
    for v in curve:
        run = v if run is None else max(run, v)
        out.append(run)
    return out


def asymptote(curve):
    """A = mean(B(G-1), B(G)) — mean-of-last-2 damps a lucky final accept."""
    return (curve[-2] + curve[-1]) / 2.0


def rate(curve):
    """R = (1/G)·Σ_{g=1..G} (B(g) − B(0)); corroborative only, never alone wins."""
    g = len(curve) - 1
    b0 = curve[0]
    return sum(curve[i] - b0 for i in range(1, g + 1)) / g


def decide(payload, sigma_d_override=None, planted_cleared_override=None):
    seeds = payload.get("seeds")
    if not seeds:
        raise ValueError("no seeds in payload")
    g = payload.get("G")
    control = payload.get("control", {})
    ignited = payload.get("ignited", {})
    k = payload.get("K", len(seeds))
    sigma_d = sigma_d_override if sigma_d_override is not None else payload.get("sigma_d")
    sigma_d_defaulted = sigma_d is None
    if sigma_d_defaulted:
        sigma_d = DEFAULT_SIGMA_D
    planted_cleared = planted_cleared_override
    if planted_cleared is None:
        planted_cleared = payload.get("planted_positive_cleared", True)

    curves_c, curves_i = {}, {}
    per_seed = {}
    dA_list, dR_list = [], []
    for s in seeds:
        key = str(s)
        if key not in control or key not in ignited:
            raise ValueError(f"seed {key} missing from control or ignited")
        cc = _monotone(control[key])
        ci = _monotone(ignited[key])
        if g is None:
            g = len(cc) - 1
        if len(cc) != g + 1 or len(ci) != g + 1:
            raise ValueError(f"seed {key}: curves must have G+1={g + 1} points")
        curves_c[key], curves_i[key] = cc, ci
        aA = asymptote(ci) - asymptote(cc)
        aR = rate(ci) - rate(cc)
        dA_list.append(aA)
        dR_list.append(aR)
        per_seed[key] = {
            "A_control": round(asymptote(cc), 6), "A_ignited": round(asymptote(ci), 6),
            "dA": round(aA, 6),
            "R_control": round(rate(cc), 6), "R_ignited": round(rate(ci), 6),
            "dR": round(aR, 6),
        }

    delta_A = median(dA_list)       # REUSED median from rsi-aggregate.py
    delta_R = median(dR_list)
    m = mde(sigma_d, k)
    sign_p = sign_p_one_sided(dA_list)

    # Sustained: B_ignited(g,s) − B_control(g,s) ≥ MDE for the tail {G-2,G-1,G},
    # for ALL seeds (§6.1.4).
    tail = [gi for gi in (g - 2, g - 1, g) if gi >= 0]
    sustained = all(
        (curves_i[str(s)][gi] - curves_c[str(s)][gi]) >= m
        for s in seeds for gi in tail
    )
    all_positive = all(d > 0 for d in dA_list)

    reasons = []
    # 1. Power precondition (hard gate, the M5 lesson).
    if not planted_cleared:
        verdict = "NO_RESULT"
        reasons.append("power precondition failed: instrument could not resolve its "
                       "planted positive at K — no verdict on the arms")
    # 2. ΔA clears the positive MDE band.
    elif delta_A >= m:
        if all_positive and sustained and delta_R >= -RATE_EPS:
            verdict = "SUPPORTED"
            reasons.append(f"ΔA={delta_A:.4f} ≥ MDE={m:.4f}, all seeds ΔA_s>0, "
                           f"sustained over tail {tail}, ΔR={delta_R:.4f} ≥ 0")
        elif delta_R < -RATE_EPS:
            verdict = "NO_RESULT"
            reasons.append(f"ΔA={delta_A:.4f} ≥ MDE but ΔR={delta_R:.4f} < 0 — higher "
                           "plateau via a late jump while converging slower; inconclusive")
        else:
            verdict = "NO_RESULT"
            reasons.append(f"ΔA={delta_A:.4f} ≥ MDE but sign/sustained gate failed "
                           f"(all_positive={all_positive}, sustained={sustained})")
    # 3. ΔA clears the negative MDE band → measurably worse plateau.
    elif delta_A <= -m:
        verdict = "REFUTED"
        reasons.append(f"ΔA={delta_A:.4f} ≤ −MDE={-m:.4f} — ignited plateau measurably worse")
    # 4. Within the ±MDE band.
    else:
        if delta_R <= -m:
            verdict = "REFUTED"
            reasons.append(f"|ΔA|={abs(delta_A):.4f} < MDE={m:.4f} while ΔR={delta_R:.4f} "
                           "≤ −MDE — faster-losing")
        else:
            verdict = "NO_RESULT"
            reasons.append(f"|ΔA|={abs(delta_A):.4f} < MDE={m:.4f} — within noise "
                           "(paper parity: converged faster, no asymptotic advantage)")

    if sigma_d_defaulted:
        reasons.append(f"WARNING: σ_d not supplied — using planning default "
                       f"{DEFAULT_SIGMA_D}; MEASURE it with `power --calibrate`")
    if k < 5 and sign_p > ALPHA:
        reasons.append(f"sign test p={sign_p:.3f} > α={ALPHA} at K={k} (corroborative "
                       "only); escalate to 5 seeds for 5/5 p=0.031")

    return {
        "verdict": verdict,
        "delta_A": round(delta_A, 6),
        "delta_R": round(delta_R, 6),
        "mde": round(m, 6),
        "K": k,
        "sigma_d": round(sigma_d, 6),
        "sustained": sustained,
        "sign_p": round(sign_p, 6),
        "per_seed": per_seed,
        "reasons": reasons,
    }


def power(sigma_d, k, effect, target_effect, calibrate_sample=None):
    out = {}
    if calibrate_sample is not None:
        if len(calibrate_sample) < 5:
            raise ValueError("--calibrate needs N_null ≥ 5 control-vs-control ΔA samples")
        sigma_d = statistics.stdev(calibrate_sample)
        out["calibrated"] = {
            "n_null": len(calibrate_sample),
            "sigma_d_measured": round(sigma_d, 6),
            "note": "σ_d = SD of the control-vs-control null ΔA sample (§6.1.6)",
        }
    out["sigma_d"] = round(sigma_d, 6)
    out["mde_at_K"] = {"K": k, "mde": round(mde(sigma_d, k), 6)}
    out["mde_seed_table"] = {str(kk): round(mde(sigma_d, kk), 6) for kk in MDE_SEED_TABLE_KS}
    out["k_req"] = {
        "target_effect": target_effect,
        "seeds_required": k_req(sigma_d, target_effect),
    }
    if effect is not None:
        out["k_req_effect"] = {"effect": effect, "seeds_required": k_req(sigma_d, effect)}
    out["note"] = (
        "MDE(K)=2.487·σ_d/√K, K_req=ceil((2.487·σ_d/effect)²); declare the run "
        "INCONCLUSIVE up front if the budget cannot fund K_req seeds (§6.1.6)"
    )
    return out


# --- runnable self-check (§6.1.4): four planted trajectory sets -------------

def _flat_gap(gap, base=0.50, g=8, seeds=(42, 43, 44)):
    """control rises base→base+0.2 linearly; ignited = control + gap at every g."""
    ctrl = {str(s): [round(base + 0.2 * (i / g), 6) for i in range(g + 1)] for s in seeds}
    ign = {str(s): [round(v + gap, 6) for v in ctrl[str(s)]] for s in seeds}
    return {"seeds": list(seeds), "G": g, "control": ctrl, "ignited": ign}


def _faster_same_plateau(g=8, seeds=(42, 43, 44)):
    """Ignited converges faster to the SAME asymptote as control (ΔR>0, |ΔA|<MDE)."""
    ctrl = {str(s): [round(0.50 + 0.30 * (i / g), 6) for i in range(g + 1)] for s in seeds}
    # ignited jumps early then flattens to the same top value 0.80.
    ign = {str(s): [round(min(0.80, 0.50 + 0.30 * math.sqrt(i / g)), 6) for i in range(g + 1)]
           for s in seeds}
    return {"seeds": list(seeds), "G": g, "control": ctrl, "ignited": ign}


def self_check():
    cases = []
    # 1. flat +0.10 gap → SUPPORTED
    cases.append(("flat +0.10 → SUPPORTED", _flat_gap(0.10), {}, "SUPPORTED"))
    # 2. faster-same-plateau → NO_RESULT
    cases.append(("faster-same-plateau → NO_RESULT", _faster_same_plateau(), {}, "NO_RESULT"))
    # 3. −0.10 plateau → REFUTED
    cases.append(("−0.10 plateau → REFUTED", _flat_gap(-0.10), {}, "REFUTED"))
    # 4. σ_d=0.08 with real ΔA=0.10 → MDE(3)≈0.1149 > 0.10 → NO_RESULT (power-fail/noise)
    cases.append(("σ_d=0.08, ΔA=0.10 → NO_RESULT (within-noise)",
                  _flat_gap(0.10), {"sigma_d_override": 0.08}, "NO_RESULT"))

    ok = True
    for label, payload, kwargs, expected in cases:
        res = decide(payload, **kwargs)
        got = res["verdict"]
        passed = got == expected
        ok = ok and passed
        print(f"  {'ok  ' if passed else 'FAIL'} {label} "
              f"(ΔA={res['delta_A']}, MDE={res['mde']}, got {got})")
    print(f"self-check: {'all passed' if ok else 'FAILURES'}")
    return ok


def _read_stdin_json():
    try:
        return json.load(sys.stdin)
    except ValueError as e:
        print(f"rsi-ignition: bad JSON on stdin: {e}", file=sys.stderr)
        sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description="Level-2 ignition statistics")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("decide", help="render the Level-2 verdict from paired trajectories")
    d.add_argument("--self-check", action="store_true", help="run the 4 planted-verdict controls")
    d.add_argument("--sigma-d", type=float, default=None, help="override σ_d (measured via power --calibrate)")
    d.add_argument("--planted-positive-cleared", dest="planted", default=None,
                   choices=["true", "false"], help="power precondition result")

    p = sub.add_parser("power", help="MDE(K) / K_req / --calibrate")
    p.add_argument("--calibrate", action="store_true",
                   help="measure σ_d from a null ΔA sample on stdin {\"null_deltas\":[...]}")
    p.add_argument("--sigma-d", type=float, default=DEFAULT_SIGMA_D)
    p.add_argument("--K", type=int, default=3)
    p.add_argument("--effect", type=float, default=None, help="also report K_req for this effect")
    p.add_argument("--target-effect", type=float, default=DEFAULT_TARGET_EFFECT)

    args = ap.parse_args()

    if args.cmd == "decide":
        if args.self_check:
            sys.exit(0 if self_check() else 1)
        payload = _read_stdin_json()
        planted = None if args.planted is None else (args.planted == "true")
        try:
            out = decide(payload, sigma_d_override=args.sigma_d, planted_cleared_override=planted)
        except ValueError as e:
            print(f"rsi-ignition: {e}", file=sys.stderr)
            sys.exit(2)
        print(json.dumps(out, indent=1))
        sys.exit(0)  # a verdict is data, not an error

    # power
    sample = None
    if args.calibrate:
        payload = _read_stdin_json()
        sample = payload.get("null_deltas")
        if not isinstance(sample, list):
            print("rsi-ignition: --calibrate needs {\"null_deltas\":[...]} on stdin", file=sys.stderr)
            sys.exit(2)
    try:
        out = power(args.sigma_d, args.K, args.effect, args.target_effect, sample)
    except ValueError as e:
        print(f"rsi-ignition: {e}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(out, indent=1))
    sys.exit(0)


if __name__ == "__main__":
    main()
