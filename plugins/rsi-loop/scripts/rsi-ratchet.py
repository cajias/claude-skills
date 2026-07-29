#!/usr/bin/env python3
"""rsi-ratchet.py — the online ratchet (§13.2 Track 1).
Part of the immutable rsi-loop harness (outer loop only).

WHY this exists: §13.1 proves a single real task cannot license a harness edit
(MDE at K=1 is 0.124, real gains are 0.02-0.05), so online *optimization* is
off the table. What IS available online is *hardening*, which needs no
counterfactual and no statistics because it is monotone: every real failure — a
review finding, a CI break, a revert, an escaped bug — becomes a permanent
regression case with the fix as its golden ref, and no future harness may
regress it. That is a ratchet, not a search, so it cannot hill-climb on noise.

Two subcommands do the whole job. `add` banks a failure; `check` asserts the
bank still holds. There is deliberately no retire/delete/remove: rail 3 of
§13.5 makes the bank append-only, and retiring a saturated case is a human act
appended to the ledger, never something the loop can call. Asking for one gets
argparse's own "invalid choice" — a usage error.

Append-only is enforced the way the harness-integrity guard enforces its own
rails: by DETECTION, with the ledger as the witness. Nothing here chmods
anything. Inner agents share this uid, so a read-only bit is theatre — it
buys false assurance while a determined write still lands. Instead every `add`
records the case file's sha256 in an append-only ledger, and `check` reconciles
bank against ledger in BOTH directions: a witnessed case that vanished or
changed is a tamper, and so is a case file the ledger never vouched for. That
second direction is what stops a wiped ledger from laundering a deletion into a
pass — with only one direction, `: > ledger.jsonl` would erase the evidence
along with the obligation.

Integrity is checked before any repro runs, and outranks it: a bank that does
not match its witness makes every repro verdict meaningless.

Exit codes (a shell caller can gate on these):
  0  success / the ratchet holds
  1  THE RATCHET BIT — a banked case's repro failed (regression)
  2  usage error
  3  REFUSED — that id is already banked (rail 3, append-only)
  4  TAMPERED — the bank does not match its ledger
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SOURCES = ("review-finding", "ci-break", "revert", "escaped-bug")
# A wedged repro must not be able to hold CI hostage; a timeout is a regression.
REPRO_TIMEOUT_S = 120
DEFAULT_BANK = Path(__file__).resolve().parent.parent / "ratchet"


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def witnessed(bank):
    """id -> case_sha256 for every `add` the ledger vouches for.

    A malformed line is skipped rather than fatal, and that still fails closed:
    losing a witness turns its case file into an unwitnessed file on disk, which
    `check` already reports as tampering.
    """
    out = {}
    path = bank / "ledger.jsonl"
    if not path.is_file():
        return out
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get("event") == "add" and "id" in entry:
            out[entry["id"]] = entry.get("case_sha256")
    return out


def banked_cases(bank):
    cases_dir = bank / "cases"
    return sorted(cases_dir.glob("*.json")) if cases_dir.is_dir() else []


def cmd_add(args):
    bank = Path(args.bank)
    case_path = bank / "cases" / f"{args.id}.json"

    # Rail 3: refuse before touching anything, so a refused duplicate leaves the
    # banked bytes byte-identical. The ledger is consulted too — re-adding an id
    # whose file was deleted behind the tool's back would overwrite the evidence.
    if case_path.exists() or args.id in witnessed(bank):
        print(
            f"rsi-ratchet: REFUSED: '{args.id}' is already banked; the ratchet is append-only",
            file=sys.stderr,
        )
        return 3

    if args.golden is not None:
        golden_file = Path(args.golden)
        if not golden_file.is_file():
            print(
                f"rsi-ratchet: --golden file not found: {golden_file}", file=sys.stderr
            )
            return 2
        golden = {"path": str(golden_file), "sha256": sha256_file(golden_file)}
    else:
        golden = {"text": args.golden_text}

    case = {
        "id": args.id,
        "source": args.source,
        "summary": args.summary,
        "repro": args.repro,
        "golden": golden,
        "banked_at": datetime.now(timezone.utc).isoformat(),
    }
    case_path.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys makes the serialization deterministic, which is what makes the
    # witnessed sha reproducible by anyone holding the same case.
    case_path.write_text(json.dumps(case, indent=2, sort_keys=True) + "\n")

    # Hash what landed on disk, not what we meant to write: the ledger witnesses
    # bytes, so `check` (and a plain sha256sum) compare the same thing.
    with (bank / "ledger.jsonl").open("a") as fh:
        entry = {"event": "add", "id": args.id, "case_sha256": sha256_file(case_path)}
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
        fh.flush()

    print(f"banked {args.id} ({args.source})")
    return 0


def cmd_check(args):
    bank = Path(args.bank)
    ledger = witnessed(bank)
    cases = banked_cases(bank)

    tampered = []
    for case_id, want_sha in sorted(ledger.items()):
        path = bank / "cases" / f"{case_id}.json"
        if not path.is_file():
            tampered.append(f"{case_id}: missing — the ledger witnessed it")
        elif sha256_file(path) != want_sha:
            tampered.append(f"{case_id}: modified — sha256 differs from the ledger")
    for path in cases:
        if path.stem not in ledger:
            tampered.append(
                f"{path.stem}: unwitnessed — no ledger entry vouches for it"
            )
    if tampered:
        print("rsi-ratchet: TAMPERED — the bank does not match its ledger:")
        for line in tampered:
            print(f"  {line}")
        return 4

    # Report only failures: a passing case in the output would let an empty run
    # look like a clean one, and buries the regression an operator must act on.
    failed = []
    for path in cases:
        case = json.loads(path.read_text())
        try:
            proc = subprocess.run(
                case["repro"],
                shell=True,
                capture_output=True,
                timeout=REPRO_TIMEOUT_S,
            )
            reason = None if proc.returncode == 0 else f"repro exited {proc.returncode}"
        except subprocess.TimeoutExpired:
            reason = f"repro timed out after {REPRO_TIMEOUT_S}s"
        if reason:
            failed.append((path.stem, reason, case.get("summary", "")))

    if failed:
        print("rsi-ratchet: THE RATCHET BIT — banked case(s) regressed:")
        for case_id, reason, summary in failed:
            print(f"  {case_id}: {reason} — {summary}")
        print(f"rsi-ratchet: {len(failed)} of {len(cases)} banked case(s) regressed")
        return 1

    print(f"rsi-ratchet: ratchet holds — {len(cases)} banked case(s) still fixed")
    return 0


def cmd_list(args):
    for path in banked_cases(Path(args.bank)):
        case = json.loads(path.read_text())
        # Collapse whitespace so the invariant holds: exactly one line per case.
        summary = " ".join(str(case.get("summary", "")).split())
        print(f"{case.get('id', path.stem)}\t{case.get('source', '?')}\t{summary}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="§13.2 Track 1 online ratchet: bank real failures forever"
    )
    # One shared --bank via parents=, not one per subparser: a duplicate on the
    # top-level parser would be silently shadowed by the subparser's default.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--bank", default=str(DEFAULT_BANK), help="ratchet bank directory"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser(
        "add",
        parents=[common],
        help="bank a real failure as a permanent regression case",
    )
    p_add.add_argument(
        "--id", required=True, help="stable case id (also the file name)"
    )
    p_add.add_argument(
        "--source", required=True, choices=SOURCES, help="ground-truth signal"
    )
    p_add.add_argument(
        "--summary", required=True, help="what actually failed, in one line"
    )
    p_add.add_argument(
        "--repro", required=True, help="shell command that must keep passing"
    )
    golden = p_add.add_mutually_exclusive_group(required=True)
    golden.add_argument(
        "--golden", help="path to the fix's golden ref (recorded as path + sha256)"
    )
    golden.add_argument("--golden-text", help="the fix's golden ref inline")

    sub.add_parser(
        "check",
        parents=[common],
        help="verify integrity, then re-run every banked repro",
    )
    sub.add_parser("list", parents=[common], help="one line per banked case")

    args = ap.parse_args()
    return {"add": cmd_add, "check": cmd_check, "list": cmd_list}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
