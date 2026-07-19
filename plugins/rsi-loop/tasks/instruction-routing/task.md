# Task: instruction routing (a tiny agent scaffold)

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

Every instruction is one of these eight operations. The phrasings below are
examples, not an exhaustive grammar — the held-out cases paraphrase them:

| Operation      | Example instruction                 | Answer |
| -------------- | ----------------------------------- | ------ |
| add            | `add 3 and 5`                       | `8`    |
| subtract       | `subtract 4 from 10`                | `6`    |
| multiply       | `multiply 6 by 7`                   | `42`   |
| reverse word   | `reverse the word cat`              | `tac`  |
| uppercase word | `uppercase the word cat`            | `CAT`  |
| count letters  | `how many letters in banana`        | `6`    |
| nth list item  | `the 2nd item in [a, b, c]`         | `b`    |
| largest number | `the largest number in [3, 9, 2]`   | `9`    |

The answer must match exactly as a string (e.g. `8`, not `8.0`; `tac`, not
`"tac"`). Numbers may be negative.

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

A held-out **private** case set scores the *same eight operations* with
different phrasings and edge-case arguments (negatives, ties, single-item lists,
larger indices). It is never available to you. A scaffold that only matches the
exact public phrasings — or hard-codes the public answers — scores poorly on
private; a scaffold that genuinely parses intent generalises. Build the general
parser, not a lookup table.
