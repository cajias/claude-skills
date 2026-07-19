# Task: time-series forecasting

Write a Python 3 solution file that predicts the next few values of a numeric
series from its observed history.

This holdout lives in a **different domain** from the rest of the battery
(numeric time-series forecasting rather than packing, classification, or
instruction parsing). It is a small WeatherBench-2-style analog: forecast the
future and beat the naive baseline.

## Contract

Your solution is a single file `solution.py` defining exactly this function:

```python
def forecast(history: list[float], horizon: int) -> list[float]:
    """Predict the next `horizon` values of the series.

    history : the observed series so far, oldest value first.
    horizon : how many future steps to predict.
    return  : a list of exactly `horizon` predicted numbers, in order.
    """
```

- Standard library only. No network, no file I/O, no subprocesses. (No numpy or
  pandas are available — implement any model yourself; `math` is enough.)
- Deterministic: same input must give the same output.
- Fast: the scorer enforces a hard per-instance time limit; an instance that
  times out or crashes scores 0.

## Scoring

For each instance the scorer compares your forecast to the true future values
with a **smooth skill ratio** against the naive persistence baseline (predicting
the last observed value for every step):

```text
score = MAE_persistence / (MAE_persistence + MAE_solution)
```

where `MAE` is mean absolute error over the horizon. This equals **0.5** when
you tie persistence, approaches **1.0** as your forecast becomes perfect, and
approaches **0.0** when it is much worse than persistence. A forecast that is
not a list of exactly `horizon` finite numbers (wrong length, NaN/inf,
non-number, exception, timeout) scores 0 for that instance. The task score is
the mean over all instances; higher is better.

Check your work with the public scorer from your working directory:

```bash
python3 score.py --public --solution solution.py --json
```

The public instances are in `public/instances.json` (format:
`[{"name": ..., "history": [...], "future": [...]}, ...]`). The `future` field
is shown to you on the public split so you can measure yourself; the private
split's futures are held out by the scorer. You may inspect the public data
freely.

## What to know about the data

- Each series is a **linear trend plus a sine seasonal cycle plus small noise**.
- Persistence (repeat the last value) scores ~0.5 by construction, so beating
  0.5 means genuinely modelling the series.
- A flat **mean** forecast scores around or below 0.5 — it captures neither the
  trend nor the season. To score well above 0.5 you must estimate the **trend**
  (the drift per step) and the **seasonal component** (the repeating cycle) and
  extrapolate both.

A held-out **private** series set decides acceptance in the outer loop; it is
never available to you. A forecaster that models trend and seasonality
generalises; one tuned to the visible series does not.
