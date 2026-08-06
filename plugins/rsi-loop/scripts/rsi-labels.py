#!/usr/bin/env python3
"""rsi-labels.py — §13.2 Track 2: free labels, and the §13.3 hard line.

Part of the immutable rsi-loop harness (outer loop only). A generation may feed
this script, never edit it.

Some supervision is already ground truth and costs nothing to collect: user
corrections, human review findings, CI failures, revert events (§13.2 Track 2).
Those four signals license exactly one kind of online write — an ADDITIVE one,
recording a *fact* ("this repo runs tests via `make test-skills`", "the v1
pagination API is deprecated"). That is memory, not optimization: it is strictly
new information, so it cannot regress anything and needs no counterfactual and
no statistics.

What it does NOT license is a policy/strategy edit — a prompt rewrite, hook
logic, a review procedure, a behavioral rule in CLAUDE.md. §13.1 measures why:
with σ_d ≈ 0.05, MDE(1) = 0.124, while real harness gains are 0.02–0.05. One
task cannot separate a genuine improvement from run-to-run luck, so accepting a
policy edit on single-task evidence is hill-climbing on noise. Those go through
Track 3's paired counterfactual (both harnesses, same real task, K ≥ 10–25) and
then the §3 gates.

`gate` enforces that line by PATH, not by intent: the classification looks at
where the edit lands, so a policy change cannot be relabelled as a fact by
describing it differently. `fact --scope` routes through the same classifier, so
"just recording a fact about the reviewer prompt" is refused too.

Both logs are append-only (rail §13.5.3): every write opens in "a" mode and adds
one line. Nothing here rewrites, reorders, or compacts what is already on disk.

Usage:
    rsi-labels.py fact    --store DIR --signal SIG --text TXT [--scope PATH] [--source S]
    rsi-labels.py failure --store DIR --signal SIG --summary TXT [--repro CMD]
    rsi-labels.py gate    --store DIR --path PATH [--path PATH ...]

Exit codes: 0 accepted · 2 usage/validation error · 3 REFUSED (§13.3 hard line).
"""

import argparse
import json
import os
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

DESCRIPTION = "§13.2 Track 2: free labels, and the §13.3 hard line."

# §13.2's four free-label sources. Anything else (a benchmark score, a hunch) is
# not ground truth and must not be recordable as one.
SIGNALS = ("user-correction", "review-finding", "ci-failure", "revert")

MDE_CITE = (
    "single-task evidence never licenses a policy change: MDE(1) = 0.124 (§13.1) "
    "dwarfs the 0.02-0.05 real harness gains, so one task cannot tell an "
    "improvement from noise. Use Track 3's paired counterfactual (both harnesses "
    "on the same task, K >= 10-25) plus the §3 gates."
)

# Policy classification, keyed on normalized path components — one source of
# truth for `gate` and `fact --scope`. All keys are casefolded: see normalize().
POLICY_DIRS = {  # any component with this name, at any depth
    "prompts": "lives under a prompts/ directory (prompt text is policy)",
    "hooks": "lives under a hooks/ directory (hook logic is policy)",
}
POLICY_NAMES = {  # exact file name, at any depth
    "policy.json": "is the policy file",
    "claude.md": "is a CLAUDE.md behavioral-rule file",
    "skill.md": "is a skill definition",
    "search-engine.mjs": "is the search engine",
}
POLICY_MD_DIRS = {  # markdown under a directory with this name
    "agents": "is an agent definition",
    "skills": "is skill documentation",
    "commands": "is a command definition (behavioral instructions)",
}


def normalize(path: str) -> tuple[str, ...]:
    """Casefolded path components, with every cheap spelling dodge collapsed.

    A gate that classifies raw strings is a gate with a bypass per spelling, so
    normalize once here and let both callers inherit it:

    * NFKC — fullwidth lookalikes (`ｐrompts`, `／`) fold to ASCII.
    * `\\` is a separator too; on Windows `prompts\\x.md` is that policy file.
    * Windows drops trailing dots and spaces from a name, so `CLAUDE.md.` and
      `CLAUDE.md ` open `CLAUDE.md`. Strip both, and leading space with them.
    * `.`/`..`/duplicate separators resolve away: `a/../prompts/x.md` is policy.
    * Casefolded, because on a case-insensitive filesystem (APFS, NTFS)
      `claude.md` and `PROMPTS/` ARE `CLAUDE.md` and `prompts/` — the same bytes
      on disk. A case-sensitive classifier hands out a real bypass.

    ponytail: no confusable-script mapping — Cyrillic `рrompts/` is a genuinely
    different directory, and a homoglyph table would refuse innocent paths.
    """
    text = unicodedata.normalize("NFKC", path).replace("\\", "/")
    out: list[str] = []
    for raw in PurePosixPath(text).parts:
        if raw in ("", "."):
            continue
        if raw == "..":
            out.append(raw)
            continue
        # Trailing dots/spaces are not part of the name a filesystem opens.
        part = raw.strip().rstrip(". ").strip() or raw
        out.append(part.casefold())
    return tuple(out)


def policy_reason(path: str) -> str | None:
    """Why `path` is a policy/strategy edit, or None if it is additive-safe.

    Classifies the spelling given AND the symlink-resolved target: a link named
    `docs/notes.md` that points into `prompts/` still edits the prompt, and an
    innocent name is not a defence.
    """
    # realpath() also anchors a relative path to the cwd, which is correct: run
    # from inside prompts/, `x.md` IS prompts/x.md. Deliberately fail-safe.
    for parts in (normalize(path), normalize(os.path.realpath(path))):
        if why := classify(parts):
            return why
    return None


def classify(parts: tuple[str, ...]) -> str | None:
    """Policy reason for already-normalized components, or None."""
    name = parts[-1] if parts else ""
    for d, why in POLICY_DIRS.items():
        if d in parts:  # includes the directory itself, not just its contents
            return why
    if name in POLICY_NAMES:
        return POLICY_NAMES[name]
    if name.endswith(".workflow.mjs"):
        return "is an agent workflow"
    if name.endswith(".md"):
        for d, why in POLICY_MD_DIRS.items():
            if d in parts[:-1]:
                return why
    return None


def blank(value: str, flag: str) -> bool:
    """True (and complains) if a path argument carries no path at all."""
    if value.strip():
        return False
    print(f"rsi-labels: {flag} must not be empty", file=sys.stderr)
    return True


def refuse(offenders: list[tuple[str, str]]) -> int:
    """Print an actionable §13.3 refusal naming only the policy paths."""
    print("rsi-labels: REFUSED — §13.3 hard line.", file=sys.stderr)
    for path, why in offenders:
        print(f"  policy path: {path} — {why}", file=sys.stderr)
    print(f"  {MDE_CITE}", file=sys.stderr)
    return 3


def append(store: str, log: str, record: dict) -> None:
    """Append one compact JSON line. Append-only: mode 'a', never a rewrite.

    Raises OSError on an unusable --store; cmd_* turns that into exit 2, because
    an uncaught traceback exits 1 and 1 is not one of this tool's verdicts.
    """
    d = Path(store)
    d.mkdir(parents=True, exist_ok=True)
    with open(d / log, "a") as fh:
        fh.write(json.dumps(record, separators=(",", ":")) + "\n")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmd_fact(args: argparse.Namespace) -> int:
    text = args.text.strip()
    if not text:
        print("rsi-labels: --text must not be empty", file=sys.stderr)
        return 2
    # Classify BEFORE any write: a refused call leaves the store byte-identical.
    if args.scope is not None:
        if blank(args.scope, "--scope"):
            return 2
        if why := policy_reason(args.scope):
            return refuse([(args.scope, why)])
    record = {"ts": now(), "signal": args.signal, "text": text}
    if args.scope:
        record["scope"] = args.scope
    if args.source:
        record["source"] = args.source
    return write(args.store, "facts.jsonl", record, f"recorded fact ({args.signal})")


def cmd_failure(args: argparse.Namespace) -> int:
    summary = args.summary.strip()
    if not summary:
        print("rsi-labels: --summary must not be empty", file=sys.stderr)
        return 2
    record = {"ts": now(), "signal": args.signal, "summary": summary}
    if args.repro:
        record["repro"] = args.repro
    return write(args.store, "failures.jsonl", record, f"logged failure ({args.signal})")


def write(store: str, log: str, record: dict, said: str) -> int:
    """append() plus the confirmation line, with --store errors as exit 2."""
    try:
        append(store, log, record)
    except OSError as exc:
        print(f"rsi-labels: cannot write --store {store}: {exc}", file=sys.stderr)
        return 2
    print(f"rsi-labels: {said}")
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    if any(blank(p, "--path") for p in args.path):
        return 2
    offenders = [(p, why) for p in args.path if (why := policy_reason(p))]
    if offenders:
        return refuse(offenders)
    print(f"rsi-labels: additive-safe — {len(args.path)} path(s) cleared")
    return 0


def main() -> int:
    # Literal, not __doc__: python3 -OO strips docstrings, and reading one at
    # startup dies with an AttributeError — exit 1, a code that is not a verdict.
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def with_common(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
        p.add_argument("--store", required=True, help="label store directory")
        return p

    f = with_common(sub.add_parser("fact", help="record an additive fact (Track 2)"))
    f.add_argument("--signal", required=True, choices=SIGNALS)
    f.add_argument("--text", required=True)
    f.add_argument("--scope", help="path the fact is about (gated like an edit)")
    f.add_argument("--source", help="provenance, e.g. 'MR !412'")
    f.set_defaults(fn=cmd_fact)

    x = with_common(sub.add_parser("failure", help="log a real failure (Track 1 feed)"))
    x.add_argument("--signal", required=True, choices=SIGNALS)
    x.add_argument("--summary", required=True)
    x.add_argument("--repro", help="command that reproduces it")
    x.set_defaults(fn=cmd_failure)

    g = with_common(sub.add_parser("gate", help="classify proposed edit paths (§13.3)"))
    g.add_argument("--path", action="append", required=True, help="repeatable")
    g.set_defaults(fn=cmd_gate)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
