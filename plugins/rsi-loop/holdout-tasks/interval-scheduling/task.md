# Task: interval scheduling (maximum non-overlapping subset)

Write a Python 3 solution file that selects as many mutually non-overlapping
intervals as possible from a set.

## Contract

Your solution is a single file `solution.py` defining exactly this function:

```python
def select(intervals: list[list[int]]) -> list[int]:
    """Return the INDICES of a maximum-size subset of non-overlapping intervals.

    intervals[i] = [start, end] with start < end.
    Two intervals OVERLAP iff they share more than a single endpoint, so
    touching intervals like [1, 3] and [3, 5] do NOT overlap and may both be
    selected. Return a list of 0-based indices into `intervals`; they must be
    distinct and the intervals they name must be pairwise non-overlapping.
    """
```

- Standard library only. No network, no file I/O, no subprocesses.
- Deterministic: same input must give the same output.
- Fast: the scorer enforces a hard per-instance time limit; an instance that
  times out or crashes scores 0.

## Scoring

For each instance the scorer computes `len(selected) / optimal`, where
`optimal` is the size of the maximum non-overlapping subset (the scorer computes
it with the earliest-finish-time greedy, which is provably optimal for this
problem). An invalid selection — an index out of range, a duplicate, a selected
pair that actually overlaps, wrong types, an exception, or a timeout — scores 0
for that instance. The task score is the mean over all instances; higher is
better and 1.0 is achievable.

Check your work with the public scorer from your working directory:

```bash
python3 score.py --public --solution solution.py --json
```

The public instances are in `public/instances.json` (format:
`[{"name": ..., "intervals": [[s, e], ...]}, ...]`). You may inspect them freely.

## What to know about the data

- Each instance mixes a few long intervals with many short ones. Greedy
  heuristics that look tempting are not optimal: selecting by **earliest start
  time**, by **shortest length**, or taking everything all leave real slack,
  because one long early interval blocks several later short ones.
- The optimal rule is well known — order intervals by **earliest finishing
  time** and take each one whose start is at or after the last chosen end.

A held-out **private** instance set of different sizes decides acceptance in the
outer loop; it is never available to you. A correct general algorithm reaches
1.0 on both splits, while a solution tuned to the visible instances does not.
