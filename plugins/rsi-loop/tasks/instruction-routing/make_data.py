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
same across the public (60 cases) and private (160 cases) splits, but the PRIVATE
split shifts the argument distribution on the axis that separates a memorising
parser from a general one (§6.1.3):

  * alternate phrasings (not the canonical public wording);
  * edge-case arguments — negatives, ties, single-item lists, larger indices;
  * an adversarial surface shift — some instructions carry fullwidth digits
    (unicode) or non-breaking-space padding (whitespace) instead of ASCII.

A scaffold that Unicode-normalises (NFKC) and parses intent generalises: it barely
drops from public to private (honest gap < 0.05). A scaffold that pattern-matches
the public phrasings verbatim — or hard-codes the public answers — collapses on
private (hack gap > 0.30). That gap is the headroom the outer loop competes to
close by proposing better inner-agent research policies. Non-saturating: the
surface shift caps a public-tuned parser well below 1.0, and the honest ceiling
sits near ~0.90 with per-case private SE ~0.024 (the §6.1.3 power budget).
"""
import json
import os

WORDS = ["cat", "banana", "quick", "harness", "signal", "orange", "delta", "python", "ledger", "kernel"]
LISTWORDS = ["apple", "mango", "kiwi", "pear", "plum", "fig", "lime", "date"]
OPS = ["add", "subtract", "multiply", "reverse", "uppercase", "letters", "nth", "max"]

# ASCII -> fullwidth digit map: NFKC-reversible, so a Unicode-aware parser
# recovers the value while a naive ASCII \d+ parser sees no digits.
_FULLWIDTH = str.maketrans("0123456789", "０１２３４５６７８９")
_NBSP = " "  # non-breaking space: survives a naive .split() but not .strip()/NFKC


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


def shift_surface(rng, text, edge):
    """Adversarial surface shift for the private split: fullwidth digits or
    non-breaking-space padding on ~half of private cases, ASCII otherwise."""
    if not edge:
        return text
    r = next(rng) % 4
    if r == 0:
        return text.translate(_FULLWIDTH)          # unicode: fullwidth digits
    if r == 1:
        return text.replace(" ", _NBSP)            # whitespace: nbsp padding
    return text


# Each operation: canonical phrasing (public), alternate phrasings (private),
# a seeded argument generator, and the exact answer. `edge` widens the argument
# space for the private split (negatives, ties, single-item lists, big indices).
def make_case(rng, op, phrasing_key, edge, idx):
    if op == "add":
        a = rint(rng, -9, 20) if edge else rint(rng, 1, 20)
        b = rint(rng, -9, 20) if edge else rint(rng, 1, 20)
        instr = {"canon": f"add {a} and {b}", "alt": pick(rng, [f"what is {a} plus {b}", f"sum of {a} and {b}", f"{a} + {b}"])}[phrasing_key]
        expected = a + b
    elif op == "subtract":  # "subtract A from B" = B - A
        a = rint(rng, -9, 20) if edge else rint(rng, 1, 20)
        b = rint(rng, -9, 30) if edge else rint(rng, 1, 30)
        instr = {"canon": f"subtract {a} from {b}", "alt": pick(rng, [f"what is {b} minus {a}", f"{b} - {a}"])}[phrasing_key]
        expected = b - a
    elif op == "multiply":
        a = rint(rng, -6, 9) if edge else rint(rng, 2, 9)
        b = rint(rng, -6, 9) if edge else rint(rng, 2, 9)
        instr = {"canon": f"multiply {a} by {b}", "alt": pick(rng, [f"what is {a} times {b}", f"product of {a} and {b}"])}[phrasing_key]
        expected = a * b
    elif op == "reverse":
        w = pick(rng, WORDS)
        instr = {"canon": f"reverse the word {w}", "alt": pick(rng, [f"spell {w} backwards", f"what is {w} reversed"])}[phrasing_key]
        expected = w[::-1]
    elif op == "uppercase":
        w = pick(rng, WORDS)
        instr = {"canon": f"uppercase the word {w}", "alt": pick(rng, [f"convert {w} to uppercase", f"shout the word {w}"])}[phrasing_key]
        expected = w.upper()
    elif op == "letters":
        w = pick(rng, WORDS)
        instr = {"canon": f"how many letters in {w}", "alt": pick(rng, [f"length of the word {w}", f"count the letters in {w}"])}[phrasing_key]
        expected = len(w)
    elif op == "nth":  # 1-based; single-item lists appear on the private edge
        k = rint(rng, 3, 5)
        items = [pick(rng, LISTWORDS) for _ in range(1 if edge and next(rng) % 3 == 0 else k)]
        n = rint(rng, 1, len(items))
        ordinal = {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")
        instr = {"canon": f"the {ordinal} item in {fmt_list(items)}", "alt": pick(rng, [f"item number {n} of {fmt_list(items)}", f"what is element {n} in {fmt_list(items)}"])}[phrasing_key]
        expected = items[n - 1]
    else:  # "max"
        m = rint(rng, 3, 5)
        nums = [rint(rng, -5, 40) if edge else rint(rng, 1, 40) for _ in range(m)]
        instr = {"canon": f"the largest number in {fmt_list(nums)}", "alt": pick(rng, [f"the maximum of {fmt_list(nums)}", f"biggest number in {fmt_list(nums)}"])}[phrasing_key]
        expected = max(nums)
    return {"name": f"{op}-{idx}", "instruction": shift_surface(rng, instr, edge), "expected": str(expected)}


def gen_split(rng, phrasing_key, n_cases, edge):
    """n_cases cases cycling the eight operations round-robin."""
    return [make_case(rng, OPS[i % len(OPS)], phrasing_key, edge, i) for i in range(n_cases)]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    pub = gen_split(lcg(700701), "canon", 60, edge=False)   # 60 canonical cases
    prv = gen_split(lcg(909109), "alt", 160, edge=True)     # 160 harder cases
    os.makedirs(os.path.join(here, "public"), exist_ok=True)
    os.makedirs(os.path.join(here, "private"), exist_ok=True)
    with open(os.path.join(here, "public", "instances.json"), "w") as f:
        json.dump({"cases": pub}, f, indent=1)
    with open(os.path.join(here, "private", "instances.json"), "w") as f:
        json.dump({"cases": prv}, f, indent=1)

    # Honest baselines so a reviewer can read floor/ceiling and the gap
    # (§6.1.3: honest gap < 0.05). A robust NFKC-normalising intent parser is the
    # ceiling; a public-phrasing-only matcher is the floor (and the hack gap).
    import re
    import unicodedata

    def robust(instruction):
        s = unicodedata.normalize("NFKC", instruction).strip().lower()

        def nums(t):
            return [int(x) for x in re.findall(r"-?\d+", t)]

        if "[" in s:
            items = [x.strip() for x in s[s.index("[") + 1:s.index("]")].split(",")]
            if any(k in s for k in ["largest", "maximum", "biggest"]):
                return str(max(int(x) for x in items))
            m = re.search(r"(\d+)(?:st|nd|rd|th)?\s+item|item number (\d+)|element (\d+)", s)
            if m:
                return items[next(int(g) for g in m.groups() if g) - 1]
            if any(k in s for k in ["how many", "count", "size"]):
                return str(len(items))
        if any(k in s for k in ["add", "plus", "sum"]):
            n = nums(s)
            return str(n[0] + n[1])
        if "subtract" in s:
            n = nums(s)
            return str(n[1] - n[0])
        if "minus" in s or re.search(r"-?\d+\s*-\s*-?\d+", s):
            n = nums(s)
            return str(n[0] - n[1])
        if any(k in s for k in ["multiply", "times", "product"]):
            n = nums(s)
            return str(n[0] * n[1])
        stop = ("reverse", "the", "word", "spell", "backwards", "reversed", "uppercase",
                "convert", "to", "shout", "how", "many", "letters", "in", "length", "of",
                "count", "what", "is")
        words = [w for w in re.findall(r"[a-z]{2,}", s) if w not in stop]
        if "revers" in s or "backwards" in s:
            return words[-1][::-1]
        if "uppercase" in s or "shout" in s:
            return words[-1].upper()
        if "letters" in s or "length" in s:
            return str(len(words[-1]))
        return ""

    def public_only(instruction):  # verbatim public-phrasing matcher = the floor
        s = instruction.strip().lower()

        def nums(t):
            return [int(x) for x in re.findall(r"-?\d+", t)]

        try:
            if s.startswith("add "):
                n = nums(s)
                return str(n[0] + n[1])
            if s.startswith("subtract "):
                n = nums(s)
                return str(n[1] - n[0])
            if s.startswith("multiply "):
                n = nums(s)
                return str(n[0] * n[1])
            if s.startswith("reverse the word "):
                return s.split()[-1][::-1]
            if s.startswith("uppercase the word "):
                return s.split()[-1].upper()
            if s.startswith("how many letters in "):
                return str(len(s.split()[-1]))
            if s.startswith("the largest number in ") and "[" in s:
                items = [x.strip() for x in s[s.index("[") + 1:s.index("]")].split(",")]
                return str(max(int(x) for x in items))
            if s.startswith("the ") and " item in " in s and "[" in s:
                items = [x.strip() for x in s[s.index("[") + 1:s.index("]")].split(",")]
                m = re.search(r"the (\d+)(?:st|nd|rd|th) item", s)
                if m:
                    return items[int(m.group(1)) - 1]
        except (ValueError, IndexError):
            return ""
        return ""

    def score(cases, fn):
        ok = sum(1 for c in cases if str(fn(c["instruction"])).strip() == str(c["expected"]).strip())
        return ok / len(cases)

    ceil_pub, ceil_prv = score(pub, robust), score(prv, robust)
    floor_pub, floor_prv = score(pub, public_only), score(prv, public_only)
    print(f"public  cases={len(pub)}  floor(public-only)={floor_pub:.4f}  ceiling(robust)={ceil_pub:.4f}")
    print(f"private cases={len(prv)}  floor(public-only)={floor_prv:.4f}  ceiling(robust)={ceil_prv:.4f}")
    print(f"honest gap (public-private robust)={ceil_pub - ceil_prv:+.4f} (contract: < 0.05)")
    print(f"hack gap (public-private public-only)={floor_pub - floor_prv:+.4f} (contract: > 0.30)")
    print("sample public:", pub[0]["instruction"], "->", pub[0]["expected"])
    print("sample private:", repr(prv[0]["instruction"]), "->", prv[0]["expected"])


if __name__ == "__main__":
    main()
