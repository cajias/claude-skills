#!/usr/bin/env python3
"""Deterministic generator for the instruction-routing task data.

Run:  python3 make_data.py   (rewrites public/instances.json, private/instances.json)

Pure standard library, fully seeded — reproducible byte-for-byte. The generated
instances.json files are the IMMUTABLE task data (anchored to git HEAD by
rsi-check-integrity.sh). This generator documents how the data was produced; it
is not part of the scored contract (score.py + task.md + public/ + private/ are).

Each case is a small natural-language instruction plus its exact expected answer.
This is a miniature *harness-engineering* task: the solution is a tiny agent
scaffold (an intent parser + operation dispatcher). The eight operations are the
same across the public and private splits, but the PRIVATE split uses alternate
phrasings and edge-case arguments (negatives, ties, single-item lists, larger
indices). A scaffold that merely pattern-matches the public phrasings — or, worse,
hard-codes the public answers — scores poorly on private; a scaffold that truly
parses intent generalises. That gap is the headroom the outer loop competes to
close by proposing better inner-agent research policies.
"""
import json
import os

WORDS = ["cat", "banana", "quick", "harness", "signal", "orange", "delta", "python", "ledger", "kernel"]
LISTWORDS = ["apple", "mango", "kiwi", "pear", "plum", "fig", "lime", "date"]


def lcg(seed):
    s = seed & 0x7FFFFFFF
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s


def pick(rng, seq):
    return seq[next(rng) % len(seq)]


def rint(rng, lo, hi):
    return lo + (next(rng) % (hi - lo + 1))


def fmt_list(items):
    return "[" + ", ".join(str(x) for x in items) + "]"


# Each operation: canonical phrasing (public), alternate phrasings (private),
# a seeded argument generator, and the exact answer. `edge` widens the argument
# space for the private split (negatives, ties, single-item lists, big indices).
def gen_split(rng, phrasing_key, n_each, edge):
    cases = []

    def add(op, instruction, expected):
        cases.append({"name": f"{op}-{len(cases)}", "instruction": instruction, "expected": str(expected)})

    for _ in range(n_each):
        # 1. add
        a = rint(rng, -9, 20) if edge else rint(rng, 1, 20)
        b = rint(rng, -9, 20) if edge else rint(rng, 1, 20)
        instr = {"canon": f"add {a} and {b}", "alt": pick(rng, [f"what is {a} plus {b}", f"sum of {a} and {b}", f"{a} + {b}"])}[phrasing_key]
        add("add", instr, a + b)

        # 2. subtract  ("subtract A from B" = B - A)
        a = rint(rng, -9, 20) if edge else rint(rng, 1, 20)
        b = rint(rng, -9, 30) if edge else rint(rng, 1, 30)
        instr = {"canon": f"subtract {a} from {b}", "alt": pick(rng, [f"what is {b} minus {a}", f"{b} - {a}"])}[phrasing_key]
        add("subtract", instr, b - a)

        # 3. multiply
        a = rint(rng, -6, 9) if edge else rint(rng, 2, 9)
        b = rint(rng, -6, 9) if edge else rint(rng, 2, 9)
        instr = {"canon": f"multiply {a} by {b}", "alt": pick(rng, [f"what is {a} times {b}", f"product of {a} and {b}"])}[phrasing_key]
        add("multiply", instr, a * b)

        # 4. reverse a word
        w = pick(rng, WORDS)
        instr = {"canon": f"reverse the word {w}", "alt": pick(rng, [f"spell {w} backwards", f"what is {w} reversed"])}[phrasing_key]
        add("reverse", instr, w[::-1])

        # 5. uppercase a word
        w = pick(rng, WORDS)
        instr = {"canon": f"uppercase the word {w}", "alt": pick(rng, [f"convert {w} to uppercase", f"shout the word {w}"])}[phrasing_key]
        add("uppercase", instr, w.upper())

        # 6. count letters in a word
        w = pick(rng, WORDS)
        instr = {"canon": f"how many letters in {w}", "alt": pick(rng, [f"length of the word {w}", f"count the letters in {w}"])}[phrasing_key]
        add("letters", instr, len(w))

        # 7. nth item in a list (1-based)
        k = rint(rng, 3, 5)
        items = [pick(rng, LISTWORDS) for _ in range(1 if edge and next(rng) % 3 == 0 else k)]
        n = rint(rng, 1, len(items))
        ordinal = {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")
        instr = {"canon": f"the {ordinal} item in {fmt_list(items)}", "alt": pick(rng, [f"item number {n} of {fmt_list(items)}", f"what is element {n} in {fmt_list(items)}"])}[phrasing_key]
        add("nth", instr, items[n - 1])

        # 8. largest number in a list
        m = rint(rng, 3, 5)
        nums = [rint(rng, -5, 40) if edge else rint(rng, 1, 40) for _ in range(m)]
        instr = {"canon": f"the largest number in {fmt_list(nums)}", "alt": pick(rng, [f"the maximum of {fmt_list(nums)}", f"biggest number in {fmt_list(nums)}"])}[phrasing_key]
        add("max", instr, max(nums))

    return cases


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    pub = gen_split(lcg(700701), "canon", n_each=4, edge=False)   # 8 ops x 4 = 32 canonical cases
    prv = gen_split(lcg(909109), "alt", n_each=4, edge=True)      # 8 ops x 4 = 32 harder cases
    os.makedirs(os.path.join(here, "public"), exist_ok=True)
    os.makedirs(os.path.join(here, "private"), exist_ok=True)
    with open(os.path.join(here, "public", "instances.json"), "w") as f:
        json.dump({"cases": pub}, f, indent=1)
    with open(os.path.join(here, "private", "instances.json"), "w") as f:
        json.dump({"cases": prv}, f, indent=1)
    print(f"public cases={len(pub)} private cases={len(prv)}")
    print("sample public:", pub[0]["instruction"], "->", pub[0]["expected"])
    print("sample private:", prv[0]["instruction"], "->", prv[0]["expected"])


if __name__ == "__main__":
    main()
