# STRESS-HARNESS operator method

You are building a measurement instrument, not a solution. Public splits are
small, so distinct working solutions often tie on the public score and the
search goes blind. Your synthetic stress suite gives the search a finer,
generalization-oriented signal to break those ties.

## 1. Learn the exact contract

Read `task.md` and the source of `score.py`. Extract precisely:

- the instance file format and where instances live,
- how a solution is loaded and invoked (function name, signature),
- the validity checks applied to outputs,
- the per-instance scoring formula and how instances are aggregated.

## 2. Write `nodes/stress/make_stress.py`

A generator that writes a synthetic instance suite to
`nodes/stress/instances/` in the SAME format as the public instances.

- Use a single hard-coded integer seed (e.g. `SEED = 1729`) with Python's
  `random.Random(SEED)` so the suite is byte-identical on every run.
- Aim for roughly 20-40 instances spanning DIVERSE parametric families:
  sizes from small up to several times larger than the largest public
  instance, and varied value distributions (uniform, clustered/peaked,
  skewed, mixtures of modes, near-boundary values). Generalization is the
  point — cover input classes the public split under-represents.
- Never copy, perturb, or rename public instances into the suite, and never
  attempt to guess, imitate, or access any private or held-out data. The
  suite is your own independent synthetic creation from the task definition.

## 3. Write `nodes/stress/stress_eval.py`

An evaluator with the interface:

```
python3 nodes/stress/stress_eval.py --solution <path> --json
```

- Load and invoke the solution exactly the way `score.py` does (reuse its
  loading/validation/scoring logic where possible so the two scores are
  comparable in kind).
- Apply the SAME per-instance scoring formula and validity checks, averaged
  over the stress instances.
- Keep the whole run fast (a few seconds): bound instance sizes accordingly
  and treat a per-instance crash or invalid output as that instance scoring
  0, recorded in an `errors` list.
- Print a single JSON object: `{"stress_score": <float>, "n_instances": <int>,
  "errors": [...]}`. Deterministic output, no randomness at eval time.

## 4. Calibrate on the existing nodes

Run the generator once, then run `stress_eval.py` on every node you were
given. Sanity-check the instrument: a working solution should score in a
plausible range (not all 0, not all exactly 1.0 — if every solution saturates
at the top, make the suite harder until it discriminates).

Report `harness_ok: true` only if generation and at least one evaluation
genuinely succeeded. Report the REAL printed stress scores — a fabricated or
estimated score is a protocol violation and will be caught by re-testing.
