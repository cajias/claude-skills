#!/usr/bin/env bash
# Tests for the online ratchet (scripts/rsi-ratchet.py) — §13.2 Track 1: every
# real failure (review finding, CI break, revert, escaped bug) becomes a banked
# regression case with the fix as its golden ref, and no future harness may
# regress it. Append-only is a rail (§13.5 rail 3), enforced the same way the
# harness-integrity guard enforces its own: by DETECTION, with the ledger as the
# witness. Cases are only ever added; a delete/mutate behind the tool's back is
# caught, not prevented.
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RATCHET="$PLUGIN_ROOT/scripts/rsi-ratchet.py"
WORK="$(mktemp -d)"
FIX="$WORK/repo" # the "harness" under ratchet: files whose fixes can regress
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$FIX"
PASS=0
FAIL=0

check() { # $1 label, $2 expected, $3 actual
  if [[ "$2" == "$3" ]]; then
    PASS=$((PASS + 1)); printf '  ok   %s\n' "$1"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL %s (want exit %s, got %s)\n' "$1" "$2" "$3"
  fi
}

run() { # invoke the ratchet; stdout -> $WORK/out, stderr -> $WORK/err; echoes exit code
  # An absent script makes python3 itself exit 2, which would collide with the
  # tool's own usage-error exit 2 and let a missing implementation pass those
  # checks. Report a distinct token so no assertion can be satisfied by absence.
  if [[ ! -f "$RATCHET" ]]; then
    : >"$WORK/out"; : >"$WORK/err"
    echo "no-script"; return
  fi
  set +e
  python3 "$RATCHET" "$@" >"$WORK/out" 2>"$WORK/err"
  local rc=$?
  set -e
  echo "$rc"
}

field() { # $1 json file, $2 python expr over v -> value, or "ERR"
  python3 -c "
import json, sys
try:
    v = json.load(open(sys.argv[1]))
    print($2)
except Exception:
    print('ERR')
" "$1" 2>/dev/null
}

ledger_sha() { # $1 bank, $2 id -> case_sha256 the ledger recorded for the add, or "NONE"
  python3 -c "
import json, sys
out = 'NONE'
try:
    for line in open(sys.argv[1] + '/ledger.jsonl'):
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        if e.get('event') == 'add' and e.get('id') == sys.argv[2]:
            out = e.get('case_sha256', 'NONE')
except Exception:
    pass
print(out)
" "$1" "$2"
}

sha() { # $1 file -> sha256 hex, or MISSING
  if [[ -f "$1" ]]; then sha256sum "$1" | cut -d' ' -f1; else echo MISSING; fi
}

has() { # $1 file, $2 substring -> True/False
  if [[ -f "$1" ]] && grep -qF -- "$2" "$1"; then echo True; else echo False; fi
}

exists() { if [[ -e "$1" ]]; then echo yes; else echo no; fi; }   # $1 path -> yes/no

witness() { # $1 bank, $2 id — append the ledger line vouching for the bytes on disk,
  # so a hand-written case file passes the integrity check and reaches the repro
  # stage. Without this the bank is merely unwitnessed (exit 4) and nothing about
  # reading the case is exercised.
  python3 -c "
import hashlib, json, sys
bank, cid = sys.argv[1], sys.argv[2]
sha = hashlib.sha256(open(f'{bank}/cases/{cid}.json', 'rb').read()).hexdigest()
with open(f'{bank}/ledger.jsonl', 'a') as fh:
    fh.write(json.dumps({'event': 'add', 'id': cid, 'case_sha256': sha}, sort_keys=True) + '\n')
" "$1" "$2"
}

newbank() { mkdir -p "$1/cases"; echo "$1"; }
fixed() { printf 'def f(x):\n    return x  # %s\n' "$2" > "$1"; }   # $1 path, $2 fix token
regress() { printf 'def f(x):\n    return x  # fix reverted\n' > "$1"; }

echo "[rsi-ratchet]"

# ── Scenario 1 ────────────────────────────────────────────────────────
# GIVEN a real failure, WHEN `add` banks it, THEN the case file records the
# repro command AND the fix as a golden reference, and the ledger witnesses it.
B_ADD="$(newbank "$WORK/bank-add")"
fixed "$FIX/parse.py" GUARD_NONE
REPRO_ADD="grep -q GUARD_NONE $FIX/parse.py"
SUMMARY_ADD="reviewer caught parse() crashing on None input"
GOLD_ADD="return x  # GUARD_NONE"
CASE_ADD="$B_ADD/cases/none-guard.json"

check "add banks a review finding (exit 0)" 0 "$(run add --bank "$B_ADD" \
  --id none-guard --source review-finding --summary "$SUMMARY_ADD" \
  --repro "$REPRO_ADD" --golden-text "$GOLD_ADD")"
check "case file written to cases/<id>.json" yes \
  "$([[ -f "$CASE_ADD" ]] && echo yes || echo no)"
check "case records its id" none-guard "$(field "$CASE_ADD" "v['id']")"
check "case records the ground-truth source" review-finding \
  "$(field "$CASE_ADD" "v['source']")"
check "case records the summary" "$SUMMARY_ADD" "$(field "$CASE_ADD" "v['summary']")"
check "case records the repro command verbatim" "$REPRO_ADD" \
  "$(field "$CASE_ADD" "v['repro']")"
check "case records the fix as golden ref" True \
  "$(field "$CASE_ADD" "'$GOLD_ADD' in str(v['golden'])")"
check "case records banked_at" True "$(field "$CASE_ADD" "bool(v.get('banked_at'))")"
check "ledger witnesses the add with the case sha256" "$(sha "$CASE_ADD")" \
  "$(ledger_sha "$B_ADD" none-guard)"

# --golden PATH form: the golden ref is recorded as path + sha256.
GOLDFILE="$WORK/golden-fix.patch"
printf '+    return x  # GUARD_NONE\n' > "$GOLDFILE"
CASE_GP="$B_ADD/cases/path-golden.json"
check "add accepts --golden PATH (exit 0)" 0 "$(run add --bank "$B_ADD" \
  --id path-golden --source ci-break --summary "CI broke on the None path" \
  --repro "$REPRO_ADD" --golden "$GOLDFILE")"
check "path golden records the file's sha256" True \
  "$(field "$CASE_GP" "'$(sha "$GOLDFILE")' in str(v['golden'])")"
check "path golden records the path" True \
  "$(field "$CASE_GP" "'$GOLDFILE' in str(v['golden'])")"

# `list` prints one line per banked case.
check "list exits 0" 0 "$(run list --bank "$B_ADD")"
check "list prints one line per banked case" 2 "$(wc -l < "$WORK/out" | tr -d ' ')"
check "list names both cases with their sources" "True True True" \
  "$(has "$WORK/out" none-guard) $(has "$WORK/out" path-golden) $(has "$WORK/out" review-finding)"

# All four ground-truth sources are accepted; anything else is a usage error.
B_SRC="$(newbank "$WORK/bank-src")"
n=0
for src in review-finding ci-break revert escaped-bug; do
  n=$((n + 1))
  check "source '$src' accepted" 0 "$(run add --bank "$B_SRC" --id "src-$n" \
    --source "$src" --summary "real failure $n" --repro "$REPRO_ADD" \
    --golden-text "$GOLD_ADD")"
done
RC="$(run add --bank "$B_SRC" --id bogus --source made-up-signal \
  --summary "not a ground-truth signal" --repro "$REPRO_ADD" --golden-text x)"
check "bogus --source rejected (exit 2)" 2 "$RC"
check "bogus --source error names the option" True "$(has "$WORK/err" source)"

# ── Scenario 2 ────────────────────────────────────────────────────────
# GIVEN a banked case, WHEN a harness regresses it, THEN `check` exits nonzero.
# The regression is real: the repro greps for the fix, and the fix is reverted.
B_PASS="$(newbank "$WORK/bank-pass")"
fixed "$FIX/router.py" ROUTE_FALLBACK
run add --bank "$B_PASS" --id route-fallback --source revert \
  --summary "router dropped unmatched requests" \
  --repro "grep -q ROUTE_FALLBACK $FIX/router.py" --golden-text "ROUTE_FALLBACK" >/dev/null
check "check passes while the fix is in place (exit 0)" 0 "$(run check --bank "$B_PASS")"

B_REG="$(newbank "$WORK/bank-reg")"
fixed "$FIX/retry.py" RETRY_BACKOFF
run add --bank "$B_REG" --id retry-backoff --source escaped-bug \
  --summary "retry storm escaped to prod" \
  --repro "grep -q RETRY_BACKOFF $FIX/retry.py" --golden-text "RETRY_BACKOFF" >/dev/null
regress "$FIX/retry.py"
check "the ratchet bites on a real regression (exit 1)" 1 "$(run check --bank "$B_REG")"
check "check names the regressed case" True "$(has "$WORK/out" retry-backoff)"

# Mixed bank: one passing, one regressed. Still exit 1, and the passing case is
# not reported as failing (one combined verdict so an empty stdout cannot pass).
B_MIX="$(newbank "$WORK/bank-mix")"
fixed "$FIX/stable.py" STABLE_FIX
fixed "$FIX/broken.py" BROKEN_FIX
run add --bank "$B_MIX" --id stable-case --source ci-break --summary "still fixed" \
  --repro "grep -q STABLE_FIX $FIX/stable.py" --golden-text "STABLE_FIX" >/dev/null
run add --bank "$B_MIX" --id broken-case --source ci-break --summary "regressed" \
  --repro "grep -q BROKEN_FIX $FIX/broken.py" --golden-text "BROKEN_FIX" >/dev/null
regress "$FIX/broken.py"
check "mixed bank still exits 1" 1 "$(run check --bank "$B_MIX")"
check "check reports only the regressed case" "True False" \
  "$(has "$WORK/out" broken-case) $(has "$WORK/out" stable-case)"

# ── Scenario 3 ────────────────────────────────────────────────────────
# GIVEN an attempt to delete or retire a banked case, THEN it is refused.
# There is no retire/delete subcommand: retiring is a human act appended to the
# ledger, never something the loop can call.
for sub in retire delete remove; do
  RC="$(run "$sub" --bank "$B_ADD" --id none-guard)"
  check "no '$sub' subcommand (exit 2)" 2 "$RC"
  check "'$sub' rejection names the subcommand" True "$(has "$WORK/err" "$sub")"
done

# Re-adding a banked id is REFUSED and leaves the case file byte-identical.
BEFORE="$(sha "$CASE_ADD")"
check "duplicate --id refused (exit 3)" 3 "$(run add --bank "$B_ADD" --id none-guard \
  --source ci-break --summary "overwrite attempt" --repro "true" --golden-text "nope")"
AFTER="$(sha "$CASE_ADD")"
if [[ "$BEFORE" == "$AFTER" && "$BEFORE" != MISSING ]]; then V=unchanged; else V="$BEFORE -> $AFTER"; fi
check "refused duplicate left the case bytes unchanged" unchanged "$V"

# Deleting a case behind the tool's back is DETECTED (exit 4), not prevented.
B_MISS="$(newbank "$WORK/bank-missing")"
fixed "$FIX/gone.py" GONE_FIX
run add --bank "$B_MISS" --id gone-case --source review-finding --summary "deleted case" \
  --repro "grep -q GONE_FIX $FIX/gone.py" --golden-text "GONE_FIX" >/dev/null
rm -f "$B_MISS/cases/gone-case.json"
check "deleted banked case detected (exit 4)" 4 "$(run check --bank "$B_MISS")"
check "check says which case is missing" "True True" \
  "$(has "$WORK/out" gone-case) $(has "$WORK/out" missing)"

# Mutating a case's bytes behind the tool's back is DETECTED (exit 4).
B_MUT="$(newbank "$WORK/bank-mutated")"
fixed "$FIX/mut.py" MUT_FIX
run add --bank "$B_MUT" --id mut-case --source revert --summary "mutated case" \
  --repro "grep -q MUT_FIX $FIX/mut.py" --golden-text "MUT_FIX" >/dev/null
printf '\n' >> "$B_MUT/cases/mut-case.json"
check "mutated banked case detected (exit 4)" 4 "$(run check --bank "$B_MUT")"
check "check says which case was modified" "True True" \
  "$(has "$WORK/out" mut-case) $(has "$WORK/out" modified)"

# Truncating the ledger must not launder a tamper into a pass: cases on disk the
# ledger no longer vouches for are a refusal (1 or 4), not a usage error (2).
B_TRUNC="$(newbank "$WORK/bank-truncated")"
fixed "$FIX/trunc.py" TRUNC_FIX
run add --bank "$B_TRUNC" --id trunc-case --source ci-break --summary "ledger wiped" \
  --repro "grep -q TRUNC_FIX $FIX/trunc.py" --golden-text "TRUNC_FIX" >/dev/null
: > "$B_TRUNC/ledger.jsonl"
RC="$(run check --bank "$B_TRUNC")"
case "$RC" in 1 | 4) V=ratchet-refusal ;; *) V="exit $RC" ;; esac
check "wiped ledger cannot launder a tamper into a pass" ratchet-refusal "$V"

# ── Scenario 4 ────────────────────────────────────────────────────────
# GIVEN an --id that is not a bare name, THEN `add` refuses it (exit 2) and
# writes nothing. The id becomes a file name, so an id like '../escaped' or an
# absolute path is an arbitrary-file-write primitive — in the one tool whose job
# is integrity. Every escape target here stays under $WORK: a regression must not
# be able to litter the real filesystem.
B_DEEP="$(newbank "$WORK/deep/bank")"
check "traversal --id refused (exit 2)" 2 "$(run add --bank "$B_DEEP" --id "../escaped" \
  --source revert --summary "escape attempt" --repro "true" --golden-text x)"
# The id is joined onto cases/, so '../x' escapes to the bank root and '../../x'
# escapes the bank entirely. Assert at the level each one actually reaches.
check "traversal --id wrote nothing outside cases/" no "$(exists "$B_DEEP/escaped.json")"
check "traversal rejection names the offending id" True "$(has "$WORK/err" "../escaped")"

check "deep traversal --id refused (exit 2)" 2 "$(run add --bank "$B_DEEP" \
  --id "../../escaped-deep" --source revert --summary "escape attempt" \
  --repro "true" --golden-text x)"
check "deep traversal wrote nothing outside the bank" no "$(exists "$WORK/deep/escaped-deep.json")"

# An absolute id discards the bank prefix entirely (Path('a') / '/tmp/x' == '/tmp/x').
check "absolute --id refused (exit 2)" 2 "$(run add --bank "$B_DEEP" \
  --id "$WORK/abs-escape" --source revert --summary "escape attempt" \
  --repro "true" --golden-text x)"
check "absolute --id wrote nothing at that path" no "$(exists "$WORK/abs-escape.json")"

check "subdirectory --id refused (exit 2)" 2 "$(run add --bank "$B_DEEP" --id "sub/dir" \
  --source revert --summary "escape attempt" --repro "true" --golden-text x)"
check "subdirectory --id created no subdirectory" no "$(exists "$B_DEEP/cases/sub")"

check "dot --id refused (exit 2)" 2 "$(run add --bank "$B_DEEP" --id ".." \
  --source revert --summary "escape attempt" --repro "true" --golden-text x)"
check "no refused id landed in the bank" 0 \
  "$(ls "$B_DEEP/cases" 2>/dev/null | wc -l | tr -d ' ')"

# ── Scenario 5 ────────────────────────────────────────────────────────
# GIVEN a malformed case file the ledger vouches for, THEN `check` reports a data
# error (exit 2), NOT the ratchet (exit 1). A crash would exit 1 too, which makes
# a broken bank indistinguishable from a real regression to any caller gating on
# the exit code — the ratchet's whole signal. A traceback is never an answer.
B_NOREPRO="$(newbank "$WORK/bank-norepro")"
printf '{"id": "no-repro", "source": "revert", "summary": "no repro key"}\n' \
  > "$B_NOREPRO/cases/no-repro.json"
witness "$B_NOREPRO" no-repro
RC="$(run check --bank "$B_NOREPRO")"
check "case missing 'repro' is a data error, not the ratchet (exit 2)" 2 "$RC"
check "malformed case did not traceback" "False False" \
  "$(has "$WORK/out" Traceback) $(has "$WORK/err" Traceback)"
check "malformed case is named in the message" True \
  "$([[ "$(has "$WORK/out" no-repro)$(has "$WORK/err" no-repro)" == *True* ]] && echo True || echo False)"

B_BADJSON="$(newbank "$WORK/bank-badjson")"
printf '{"id": "bad-json", "repro": "true"\n' > "$B_BADJSON/cases/bad-json.json"
witness "$B_BADJSON" bad-json
RC="$(run check --bank "$B_BADJSON")"
check "unparseable case is a data error, not the ratchet (exit 2)" 2 "$RC"
check "unparseable case did not traceback" "False False" \
  "$(has "$WORK/out" Traceback) $(has "$WORK/err" Traceback)"

# `list` reads the same case files and must not traceback on them either.
RC="$(run list --bank "$B_BADJSON")"
check "list did not traceback on an unparseable case" "False False" \
  "$(has "$WORK/out" Traceback) $(has "$WORK/err" Traceback)"
check "list on an unparseable case is a data error (exit 2)" 2 "$RC"

# A forged ledger line is the other direction of the same escape: `check` derives
# a path from the ledger's id, so an appended '../../x' walks it out of the bank.
# Pointed at an existing out-of-bank file with a matching sha, an unguarded check
# satisfies its own integrity test against something that is not a case at all
# and prints "ratchet holds" — a laundered pass, which is the failure mode the
# ledger exists to prevent. An id `add` could never have written is a tamper (4).
B_FORGE="$(newbank "$WORK/deep/bank-forged")"
# cases/../../ is $WORK/deep — one level above the bank, outside it either way.
printf 'not a case at all\n' > "$WORK/deep/outsider.json"
printf '{"case_sha256": "%s", "event": "add", "id": "../../outsider"}\n' \
  "$(sha "$WORK/deep/outsider.json")" > "$B_FORGE/ledger.jsonl"
RC="$(run check --bank "$B_FORGE")"
check "forged ledger id cannot launder a pass (exit 4)" 4 "$RC"
check "forged ledger id did not traceback" "False False" \
  "$(has "$WORK/out" Traceback) $(has "$WORK/err" Traceback)"

# TAMPERED still outranks malformed: an unwitnessed bad case is a tamper (4).
B_UNWIT="$(newbank "$WORK/bank-unwitnessed-bad")"
printf 'not json at all\n' > "$B_UNWIT/cases/unwitnessed-bad.json"
check "tamper still outranks malformed (exit 4)" 4 "$(run check --bank "$B_UNWIT")"

# ── Scenario 6 ────────────────────────────────────────────────────────
# GIVEN a repro that cannot express failure, THEN `add` refuses it (exit 2). An
# empty shell command exits 0 forever, so the case can never bite: it inflates
# the count of banked cases while witnessing nothing.
B_REPRO="$(newbank "$WORK/bank-repro")"
check "empty --repro refused (exit 2)" 2 "$(run add --bank "$B_REPRO" --id empty-repro \
  --source revert --summary "unfailable repro" --repro "" --golden-text x)"
check "whitespace --repro refused (exit 2)" 2 "$(run add --bank "$B_REPRO" \
  --id blank-repro --source revert --summary "unfailable repro" --repro "   " \
  --golden-text x)"
check "no unfailable case landed in the bank" 0 \
  "$(ls "$B_REPRO/cases" 2>/dev/null | wc -l | tr -d ' ')"

# ── Scenario 7 ────────────────────────────────────────────────────────
# GIVEN a symlink planted in the bank's layout, THEN the tool refuses to operate
# (exit 2). This is the --id escape of scenario 4 by a different vector, and the
# guards there cannot see it: resolving a path FOLLOWS the link, so with cases/
# pointed elsewhere the resolved parent still *is* <bank>/cases — it just lives
# outside the bank now. Every write the tool makes is redirected: case files under
# `add`, witness lines appended to the ledger. Nothing in a legitimate bank is
# ever a link, so the rule is the lazy one — cases/ a real directory, the ledger
# and every case a regular file.
B_SYMDIR="$WORK/bank-symdir"
mkdir -p "$B_SYMDIR" "$WORK/sym-target"
ln -s "$WORK/sym-target" "$B_SYMDIR/cases"
check "symlinked cases/ refused by add (exit 2)" 2 "$(run add --bank "$B_SYMDIR" \
  --id sym-escape --source revert --summary "symlink escape" --repro "true" \
  --golden-text x)"
check "symlinked cases/ wrote nothing at the link target" no \
  "$(exists "$WORK/sym-target/sym-escape.json")"
check "symlinked cases/ refused by check (exit 2)" 2 "$(run check --bank "$B_SYMDIR")"
check "symlink rejection names what was rejected" "True True" \
  "$(has "$WORK/err" cases) $(has "$WORK/err" symlink)"
check "symlinked cases/ refused by list (exit 2)" 2 "$(run list --bank "$B_SYMDIR")"

# A case file may not be a link either: moved out and linked back, its sha still
# matches the ledger, so integrity "passes" while the banked bytes now live where
# the append-only regime cannot see them.
B_SYMCASE="$(newbank "$WORK/bank-symcase")"
fixed "$FIX/symcase.py" SYMCASE_FIX
run add --bank "$B_SYMCASE" --id linked-case --source ci-break --summary "case relinked" \
  --repro "grep -q SYMCASE_FIX $FIX/symcase.py" --golden-text "SYMCASE_FIX" >/dev/null
mv "$B_SYMCASE/cases/linked-case.json" "$WORK/outside-case.json"
ln -s "$WORK/outside-case.json" "$B_SYMCASE/cases/linked-case.json"
RC="$(run check --bank "$B_SYMCASE")"
case "$RC" in 2 | 4) V=refused ;; *) V="exit $RC" ;; esac
check "symlinked case file refused, never a pass" refused "$V"
check "symlinked case file did not traceback" "False False" \
  "$(has "$WORK/out" Traceback) $(has "$WORK/err" Traceback)"

# A symlinked ledger redirects the append that IS the witness: the obligation
# lands in a file outside the bank, which a later `check` can simply not find.
B_SYMLED="$(newbank "$WORK/bank-symledger")"
: > "$WORK/outside-ledger.jsonl"
ln -s "$WORK/outside-ledger.jsonl" "$B_SYMLED/ledger.jsonl"
check "symlinked ledger refused by add (exit 2)" 2 "$(run add --bank "$B_SYMLED" \
  --id led-escape --source revert --summary "ledger redirect" --repro "true" \
  --golden-text x)"
check "symlinked ledger received no witness line" 0 \
  "$(wc -l < "$WORK/outside-ledger.jsonl" | tr -d ' ')"
check "symlinked ledger refused by check (exit 2)" 2 "$(run check --bank "$B_SYMLED")"

# ── Scenario 8 ────────────────────────────────────────────────────────
# GIVEN a repro written relative to the repository root — which every real banked
# case is — THEN `check` reaches the same verdict from any cwd. A repro is a shell
# command, so leaving its execution directory undefined makes the ratchet bite on
# a PHANTOM regression whenever the caller's cwd differs: corrosive in an
# integrity tool, because it trains operators to ignore the ratchet and reds CI
# for the wrong reason. The directory is therefore fixed at the repo root.
REPO_ROOT="$(cd "$PLUGIN_ROOT/../.." && pwd)"
B_CWD="$(newbank "$WORK/bank-cwd")"
run add --bank "$B_CWD" --id repo-relative --source review-finding \
  --summary "repro path is relative to the repo root" \
  --repro "grep -q lint-file Makefile" --golden-text "lint-file" >/dev/null
check "repo-relative repro passes from the repo root (exit 0)" 0 \
  "$(cd "$REPO_ROOT" && run check --bank "$B_CWD")"
check "repo-relative repro passes from an unrelated cwd (exit 0)" 0 \
  "$(cd "$WORK" && run check --bank "$B_CWD")"
# The default is a default, not a hardcoding: pointed somewhere the repro cannot
# succeed, --cwd makes the ratchet bite — which proves the flag is load-bearing.
check "--cwd override is honored (exit 1)" 1 \
  "$(run check --bank "$B_CWD" --cwd "$WORK")"

echo
echo "rsi-ratchet: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
