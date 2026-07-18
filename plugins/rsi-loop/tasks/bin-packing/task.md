# Task: 1-D bin packing

Write a Python 3 solution file that packs items into as few bins as possible.

## Contract

Your solution is a single file `solution.py` defining exactly this function:

```python
def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.
    """
```

- Standard library only. No network, no file I/O, no subprocesses.
- Deterministic: same input must give the same output.
- Fast: the scorer enforces a hard time limit across all instances; an
  instance that times out or crashes scores 0.

## Scoring

For each instance the scorer computes `LB / bins_used`, where
`LB = max(ceil(sum(sizes) / capacity), 1)` is the classical lower bound.
An invalid packing (missing/duplicated indices, overfull bin, wrong types,
exception, timeout) scores 0 for that instance. The task score is the mean
over all instances — higher is better, 1.0 is a (usually unreachable)
upper bound.

Check your work with the public scorer from your working directory:

```bash
python3 score.py --public --solution solution.py --json
```

The public instances are in `public/instances.json` (format:
`[{"name": ..., "capacity": C, "items": [s1, s2, ...]}, ...]`). You may
inspect them freely. A held-out private instance set of different sizes
exists but is not available to you; do not try to access it. Solutions
that generalize (good packing heuristics) beat solutions tuned to the
public instances.
