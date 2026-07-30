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
  2  usage error, or a bank that cannot be read (bad id, malformed case)
  3  REFUSED — that id is already banked (rail 3, append-only)
  4  TAMPERED — the bank does not match its ledger

Exit 1 is reserved: it means a real regression and nothing else. A crash would
also exit 1, so a malformed bank would be indistinguishable from the ratchet
biting to any caller gating on the code — which is the entire signal. Every way
a case can fail to be read is therefore caught and reported as 2, and main()
backstops the rest so no internal error can impersonate a regression.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

SOURCES = ("review-finding", "ci-break", "revert", "escaped-bug")
# A wedged repro must not be able to hold CI hostage; a timeout is a regression.
REPRO_TIMEOUT_S = 120
DEFAULT_BANK = Path(__file__).resolve().parent.parent / "ratchet"
# An id becomes a file name, so it is a path component and nothing else.
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class BadId(Exception):
    """An id that cannot safely become a file name."""


class Malformed(Exception):
    """A banked case that cannot be read as a case."""


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case_path(bank, case_id):
    """The single point where an id becomes a path — so the single guard.

    Unvalidated, an id is an arbitrary-file-write primitive in the one tool whose
    whole job is integrity: '../../x' escapes the bank, and an absolute id
    discards it outright because Path('bank') / '/tmp/x' == Path('/tmp/x'). The
    regex is the guard; the resolved-parent check is defence in depth against
    whatever the regex fails to anticipate.
    """
    if not ID_RE.match(case_id):
        raise BadId(case_id)
    cases = bank / "cases"
    path = cases / f"{case_id}.json"
    if path.resolve().parent != cases.resolve():
        raise BadId(case_id)
    return path


def unfailable(repro):
    """A repro that cannot express failure witnesses nothing.

    An empty or whitespace-only shell command exits 0 forever, so such a case
    inflates the count of banked cases while never being able to bite.
    """
    return not isinstance(repro, str) or not repro.strip()


def load_case(path):
    """Parse a banked case, or say why it is not one.

    Every read of a case file goes through here, so no unreadable case can reach
    subprocess.run and turn into an exit 1 that reads as a regression.
    """
    try:
        case = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise Malformed(str(exc)) from exc
    if not isinstance(case, dict):
        raise Malformed("not a JSON object")
    if "repro" not in case:
        raise Malformed("no 'repro' command")
    if unfailable(case["repro"]):
        raise Malformed("repro is empty; it could never fail")
    return case


def report_malformed(bad):
    print("rsi-ratchet: MALFORMED — banked case(s) cannot be read:")
    for line in bad:
        print(f"  {line}")
    return 2


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
    path = case_path(bank, args.id)

    if unfailable(args.repro):
        print(
            "rsi-ratchet: --repro is empty; a repro that cannot fail can never bite",
            file=sys.stderr,
        )
        return 2

    # Rail 3: refuse before touching anything, so a refused duplicate leaves the
    # banked bytes byte-identical. The ledger is consulted too — re-adding an id
    # whose file was deleted behind the tool's back would overwrite the evidence.
    if path.exists() or args.id in witnessed(bank):
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
    path.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys makes the serialization deterministic, which is what makes the
    # witnessed sha reproducible by anyone holding the same case.
    path.write_text(json.dumps(case, indent=2, sort_keys=True) + "\n")

    # Hash what landed on disk, not what we meant to write: the ledger witnesses
    # bytes, so `check` (and a plain sha256sum) compare the same thing.
    with (bank / "ledger.jsonl").open("a") as fh:
        entry = {"event": "add", "id": args.id, "case_sha256": sha256_file(path)}
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
        # The id comes from the ledger, so it is untrusted here too: an appended
        # line naming '../../x' would otherwise walk `check` out of the bank. An
        # id `add` could never have written is itself evidence of tampering.
        try:
            path = case_path(bank, case_id)
        except BadId:
            tampered.append(f"{case_id}: illegal id — no `add` could have written it")
            continue
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

    # Load every case before running any repro. A case that cannot be read is a
    # data error (2), and it must be settled here: once a repro has run, a later
    # crash would surface as exit 1 and read as the ratchet biting.
    loaded = []
    bad = []
    for path in cases:
        try:
            loaded.append((path, load_case(path)))
        except Malformed as exc:
            bad.append(f"{path.stem}: malformed — {exc}")
    if bad:
        return report_malformed(bad)

    # Report only failures: a passing case in the output would let an empty run
    # look like a clean one, and buries the regression an operator must act on.
    failed = []
    for path, case in loaded:
        try:
            proc = subprocess.run(
                case["repro"],
                shell=True,
                capture_output=True,
                timeout=REPRO_TIMEOUT_S,
                check=False,  # we read returncode; a raise would crash, not report
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
    # Same load path as `check`, for the same reason: a bad case file is a data
    # error with a name attached, never a traceback.
    lines = []
    bad = []
    for path in banked_cases(Path(args.bank)):
        try:
            case = load_case(path)
        except Malformed as exc:
            bad.append(f"{path.stem}: malformed — {exc}")
            continue
        # Collapse whitespace so the invariant holds: exactly one line per case.
        summary = " ".join(str(case.get("summary", "")).split())
        lines.append(
            f"{case.get('id', path.stem)}\t{case.get('source', '?')}\t{summary}"
        )
    if bad:
        return report_malformed(bad)
    for line in lines:
        print(line)
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
    try:
        return {"add": cmd_add, "check": cmd_check, "list": cmd_list}[args.cmd](args)
    except BadId as exc:
        print(
            f"rsi-ratchet: invalid --id '{exc}': an id is a bare file name — "
            "letters, digits, '.', '_', '-', starting alphanumeric",
            file=sys.stderr,
        )
        return 2
    except Exception:  # noqa: BLE001 — blind is the point; see below
        # Exit 1 is reserved for a real regression, so an internal error must not
        # be able to claim it. Print the trace to stderr for the operator and
        # report a data error; a bare traceback would exit 1 and read as the
        # ratchet biting. Narrowing this catch would reopen exactly that hole for
        # whichever exception type the narrowing failed to anticipate.
        traceback.print_exc(file=sys.stderr)
        print("rsi-ratchet: internal error — not a regression verdict", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
