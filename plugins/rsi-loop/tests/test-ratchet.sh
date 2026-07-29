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

echo
echo "rsi-ratchet: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
