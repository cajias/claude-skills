# Task: instruction ops (a tiny agent scaffold)

Write a Python 3 solution file that reads a short natural-language instruction,
works out which operation it asks for, performs it, and returns the exact
answer. Your solution *is* a miniature agent scaffold: an intent parser plus an
operation dispatcher. Making it better is harness engineering.

## Contract

Your solution is a single file `solution.py` defining exactly this function:

```python
def solve(instruction: str) -> str:
    """Return the exact answer to one instruction, as a string."""
```

- Standard library only. No network, no file I/O, no subprocesses.
- Deterministic: same instruction must give the same answer.
- Fast: the scorer enforces a hard time limit over the whole case batch.

## The operations

Every instruction is one of these four operations. The phrasings below are
examples, not an exhaustive grammar — the held-out cases paraphrase them:

| Operation     | Example instruction                    | Answer      |
| ------------- | -------------------------------------- | ----------- |
| count words   | `count the words in the quick cat`     | `3`         |
| concatenate   | `concatenate cat and banana`           | `catbanana` |
| smallest num  | `the smallest number in [3, 9, 2]`     | `2`         |
| greater than  | `is 7 greater than 4`                   | `yes`       |

Details:

- **count words**: the number of whitespace-separated words in the sentence.
- **concatenate**: join the two words directly, with **no separator** (`cat` +
  `banana` = `catbanana`).
- **smallest number**: the minimum value in the bracketed list; numbers may be
  negative and the list may hold a single element.
- **greater than**: answer the lowercase string `yes` if the first number is
  strictly greater than the second, otherwise `no` (equal values answer `no`).

The answer must match exactly as a string (e.g. `3`, not `3.0`; `yes`, not
`Yes`). Numbers may be negative.

## Scoring

Each case scores 1 if `str(solve(instruction)).strip()` equals the expected
answer, else 0. The task score is the fraction correct.

Check your work with the public scorer from your working directory:

```bash
python3 score.py --public --solution solution.py --json
```

The public cases are in `public/instances.json` (format:
`{"cases": [{"name": ..., "instruction": ..., "expected": ...}, ...]}`). You may
inspect them freely.

## What decides acceptance

A held-out **private** case set scores the *same four operations* with different
phrasings and edge-case arguments (negatives, ties, single-word sentences,
single-item lists). It is never available to you. A scaffold that only matches
the exact public phrasings — or hard-codes the public answers — scores poorly on
private; a scaffold that genuinely parses intent generalises. Build the general
parser, not a lookup table.
