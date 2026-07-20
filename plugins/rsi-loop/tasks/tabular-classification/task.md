# Task: tabular binary classification

Write a Python 3 solution file that learns a binary classifier from labelled
training rows and predicts labels for unlabelled test rows.

## Contract

Your solution is a single file `solution.py` defining exactly this function:

```python
def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """Train on `train` and return one predicted label (0 or 1) per test row.

    train : rows of [x0, x1, x2, x3, x4, x5, label]  (label is 0 or 1)
    test  : rows of [x0, x1, x2, x3, x4, x5]          (no label)
    return: list of length len(test), each element 0 or 1, in order.
    """
```

- Standard library only. No network, no file I/O, no subprocesses. (No numpy,
  pandas, or scikit-learn are available — implement the model yourself.)
- Deterministic: same input must give the same output.
- Fast: the scorer enforces a hard per-call time limit; a call that times out
  or crashes scores 0 for that fold/instance.

## Scoring

The public score is a **5-fold cross-validation accuracy** over the training
rows: the scorer repeatedly hides one fold, trains your `predict` on the other
four, and measures accuracy on the hidden fold. You never see a hidden fold's
labels, so there is nothing to memorise — the public score rewards a model that
generalises. The task score is the mean fold accuracy (higher is better).

Check your work with the public scorer from your working directory:

```bash
python3 score.py --public --solution solution.py --json
```

The public rows are in `public/instances.json` (format:
`{"features": ["x0"..."x5"], "rows": [[x0,...,x5,label], ...]}`). You may
inspect them freely.

## What to know about the data

- Six features per row. Only some carry signal; others are noise. Part of the
  problem is figuring out which — a model that weights every feature equally is
  dragged down by the irrelevant ones.
- The decision boundary is **not linearly separable**: a single linear
  threshold scores near chance. Nonlinear models (k-NN, a small decision tree,
  or a linear model over engineered/interaction features) do much better.
- There is a few percent of irreducible label noise; do not chase it by
  overfitting.

A held-out **private** test set of unseen rows from the same distribution
decides acceptance in the outer loop; it is never available to you, and
memorising or hard-coding the public rows will not help there. Solutions that
generalise beat solutions tuned to the visible rows.
