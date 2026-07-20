#!/usr/bin/env python3
"""Deterministic generator for the instruction-ops holdout task data.

Run:  python3 make_data.py   (rewrites public/instances.json, private/instances.json)

Pure standard library, fully seeded — reproducible byte-for-byte. This is a
SECOND-ORDER-GENERALIZATION holdout: the rsi-loop outer loop never trains on it.
The best inner agent is later run here to measure whether an agent-scaffold
research policy that helped on the training instruction task also generalises to
FOUR OPERATIONS IT HAS NEVER SEEN.

The four operations here are deliberately disjoint from the training task's
eight (add/subtract/multiply/reverse/uppercase/count-letters/nth-item/largest):

    (a) count words   "count the words in <sentence>"      -> number of words
    (b) concatenate   "concatenate <A> and <B>"            -> A + B  (no space)
    (c) smallest num  "the smallest number in [..]"        -> min of the list
    (d) greater than  "is <X> greater than <Y>"            -> "yes" / "no"

The PUBLIC split uses the canonical phrasings above. The PRIVATE split uses
alternate phrasings and edge-case arguments (negatives, ties, single-item
lists). A scaffold that only pattern-matches the canonical public phrasings
scores well on public but poorly on private; a scaffold that genuinely parses
intent generalises. That gap is the headroom.
"""
import json
import os

WORDS = ["cat", "banana", "quick", "harness", "signal", "orange", "delta", "python", "ledger", "kernel"]


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


def sentence(rng, k):
    return " ".join(pick(rng, WORDS) for _ in range(k))


# Each operation: canonical phrasing (public) vs alternate phrasings (private),
# a seeded argument generator, and the exact answer. `edge` widens the argument
# space for the private split (negatives, ties, single-word/single-item cases).
def gen_split(rng, phrasing_key, n_each, edge):
    cases = []

    def add(op, instruction, expected):
        cases.append({"name": f"{op}-{len(cases)}", "instruction": instruction, "expected": str(expected)})

    for _ in range(n_each):
        # (a) count the words in a sentence
        k = rint(rng, 1, 2) if (edge and next(rng) % 3 == 0) else rint(rng, 3, 7)
        sent = sentence(rng, k)
        instr = {
            "canon": f"count the words in {sent}",
            "alt": pick(rng, [f"how many words are in {sent}", f"word count of {sent}", f"number of words in {sent}"]),
        }[phrasing_key]
        add("words", instr, k)

        # (b) concatenate A and B  ->  A + B  (direct join, no separator)
        a = pick(rng, WORDS)
        b = pick(rng, WORDS)
        instr = {
            "canon": f"concatenate {a} and {b}",
            "alt": pick(rng, [f"join {a} and {b}", f"combine {a} with {b}", f"stick {a} and {b} together"]),
        }[phrasing_key]
        add("concat", instr, a + b)

        # (c) the smallest number in a list
        m = rint(rng, 1, 2) if (edge and next(rng) % 3 == 0) else rint(rng, 3, 6)
        nums = [rint(rng, -20, 40) if edge else rint(rng, 1, 40) for _ in range(m)]
        instr = {
            "canon": f"the smallest number in {fmt_list(nums)}",
            "alt": pick(rng, [f"the minimum of {fmt_list(nums)}", f"smallest value in {fmt_list(nums)}", f"the min of {fmt_list(nums)}"]),
        }[phrasing_key]
        add("smallest", instr, min(nums))

        # (d) is X greater than Y  ->  yes/no  (ties -> no)
        if edge and next(rng) % 4 == 0:
            x = rint(rng, -10, 20)
            y = x  # tie: not greater -> "no"
        else:
            x = rint(rng, -10, 40) if edge else rint(rng, 1, 40)
            y = rint(rng, -10, 40) if edge else rint(rng, 1, 40)
        instr = {
            "canon": f"is {x} greater than {y}",
            "alt": pick(rng, [f"is {x} bigger than {y}", f"is {x} larger than {y}", f"is {x} more than {y}"]),
        }[phrasing_key]
        add("greater", instr, "yes" if x > y else "no")

    return cases


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    pub = gen_split(lcg(440401), "canon", n_each=5, edge=False)   # 4 ops x 5 = 20 canonical
    prv = gen_split(lcg(551509), "alt", n_each=5, edge=True)      # 4 ops x 5 = 20 harder
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
