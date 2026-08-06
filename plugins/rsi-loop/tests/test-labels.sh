#!/usr/bin/env bash
# Tests for rsi-labels.py: §13.2 Track 2 (free labels) + the §13.3 hard line.
#
# Track 2 licenses ADDITIVE writes only — recording a *fact* ("this repo runs
# tests via `make test-x`", "that API is deprecated"). That is memory, not
# optimization, and cannot regress anything because it is strictly new
# information. Policy/strategy edits (prompt rewrites, hook logic, review
# procedure, CLAUDE.md behavioral rules) are NEVER accepted on single-task
# evidence: §13.1's MDE(1) = 0.124 dwarfs the 0.02–0.05 real harness gains, so
# one task cannot separate a genuine improvement from run-to-run luck. Those
# need Track 3's paired counterfactual. The `gate` subcommand is where that line
# is enforced, so most of this file is about refusals, not happy paths.
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABELS="$PLUGIN_ROOT/scripts/rsi-labels.py"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PASS=0
FAIL=0

check() { # $1 label, $2 expected, $3 actual
  if [[ "$2" == "$3" ]]; then
    PASS=$((PASS + 1)); printf '  ok   %s\n' "$1"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL %s (want exit %s, got %s)\n' "$1" "$2" "$3"
  fi
}

OUT_FILE="$WORK/.stdout"
ERR_FILE="$WORK/.stderr"
RC=""

# run() sets RC to the script's exit code — or to the non-numeric sentinel
# "no-script" when the implementation is absent. The sentinel matters: python3
# exits 2 on a missing file, which would silently satisfy every "want exit 2"
# assertion below and turn a red suite green for the wrong reason.
run() {
  : > "$OUT_FILE"; : > "$ERR_FILE"
  if [[ ! -f "$LABELS" ]]; then
    RC="no-script"
    printf 'NO-SCRIPT-PRESENT\n' > "$ERR_FILE"
    return 0
  fi
  set +e
  python3 "$LABELS" "$@" > "$OUT_FILE" 2> "$ERR_FILE"
  RC=$?
  set -e
}

out_has() { # $1 extended-regex (case-insensitive) -> yes/no
  if grep -qiE "$1" "$OUT_FILE" "$ERR_FILE" 2>/dev/null; then echo yes; else echo no; fi
}

records_in() { # $1 jsonl file -> non-empty record count, or "no-file"
  python3 - "$1" <<'PY'
import os, sys
p = sys.argv[1]
print(sum(1 for ln in open(p) if ln.strip()) if os.path.isfile(p) else "no-file")
PY
}

jfield() { # $1 jsonl file, $2 1-based index, $3 key
  python3 - "$1" "$2" "$3" <<'PY'
import json, sys
try:
    line = open(sys.argv[1]).read().splitlines()[int(sys.argv[2]) - 1]
    print(json.loads(line).get(sys.argv[3], "no-key"))
except Exception:
    print("no-json")
PY
}

has_utc_ts() { # $1 jsonl file, $2 1-based index -> yes/no
  python3 - "$1" "$2" <<'PY'
import datetime, json, sys
def utc(s):
    try:
        d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return False
    return d.tzinfo is not None and d.utcoffset() == datetime.timedelta(0)
try:
    rec = json.loads(open(sys.argv[1]).read().splitlines()[int(sys.argv[2]) - 1])
    print("yes" if any(isinstance(x, str) and utc(x) for x in rec.values()) else "no")
except Exception:
    print("no-file")
PY
}

# snap() records the current bytes of a log for the later append-only check.
# Tolerant of an absent log so a missing implementation reports as a failed
# assertion instead of killing the suite at the first `cp` under `set -e`.
snap() { # $1 log, $2 snapshot destination
  cp "$1" "$2" 2>/dev/null || : > "$2"
}

is_grown_prefix() { # $1 file, $2 snapshot-of-earlier-state -> yes/no
  python3 - "$1" "$2" <<'PY'
import sys
try:
    big = open(sys.argv[1], "rb").read()
    small = open(sys.argv[2], "rb").read()
    print("yes" if big.startswith(small) and len(big) > len(small) else "no")
except Exception:
    print("no-file")
PY
}

echo "[rsi-labels]"

# ── Subcommand `fact` — the additive path (Track 2, licensed online) ──────
echo "[fact]"

S="$WORK/s-fact"
run fact --store "$S" --signal user-correction --text 'this repo runs tests via make test-skills'
check "fact exits 0" 0 "$RC"
check "fact creates the store and facts.jsonl (1 record)" 1 "$(records_in "$S/facts.jsonl")"
check "record carries the signal" "user-correction" "$(jfield "$S/facts.jsonl" 1 signal)"
check "record carries the text" "this repo runs tests via make test-skills" \
  "$(jfield "$S/facts.jsonl" 1 text)"
check "record carries a UTC timestamp" "yes" "$(has_utc_ts "$S/facts.jsonl" 1)"

# Append-only: rail §13.5.3. A second fact may only extend the file; the bytes
# already on disk must be untouched (no rewrite, no reorder, no compaction).
snap "$S/facts.jsonl" "$WORK/facts.snap1"
run fact --store "$S" --signal review-finding --text 'the v1 pagination API is deprecated'
check "second fact exits 0" 0 "$RC"
check "two adds leave exactly 2 records" 2 "$(records_in "$S/facts.jsonl")"
check "earlier bytes are an untouched prefix" "yes" "$(is_grown_prefix "$S/facts.jsonl" "$WORK/facts.snap1")"
check "first record still byte-identical" "this repo runs tests via make test-skills" \
  "$(jfield "$S/facts.jsonl" 1 text)"
check "second record is the new one" "the v1 pagination API is deprecated" \
  "$(jfield "$S/facts.jsonl" 2 text)"

# Ground-truth signals only — these four are exactly §13.2's free-label sources
# (user corrections, human review findings, CI failures, revert events). Anything
# else is not ground truth and must not be recordable as one.
for sig in user-correction review-finding ci-failure revert; do
  run fact --store "$WORK/s-sig-$sig" --signal "$sig" --text "fact from $sig"
  check "signal '$sig' accepted" 0 "$RC"
done
run fact --store "$WORK/s-badsig" --signal benchmark-score --text 'harness got a better score'
check "unknown --signal exits 2" 2 "$RC"
check "unknown signal wrote nothing" "no-file" "$(records_in "$WORK/s-badsig/facts.jsonl")"

run fact --store "$WORK/s-empty" --signal ci-failure --text ''
check "empty --text exits 2" 2 "$RC"
run fact --store "$WORK/s-ws" --signal ci-failure --text '   '
check "whitespace-only --text exits 2" 2 "$RC"

# Optional metadata is recorded, not dropped.
S2="$WORK/s-meta"
SAFE_SCOPE="$WORK/tree/docs/NOTES.md"
mkdir -p "$(dirname "$SAFE_SCOPE")"; : > "$SAFE_SCOPE"
run fact --store "$S2" --signal revert --text 'the retry wrapper caused duplicate writes' \
  --scope "$SAFE_SCOPE" --source 'MR !412'
check "fact with --scope/--source exits 0" 0 "$RC"
check "--source is recorded" "MR !412" "$(jfield "$S2/facts.jsonl" 1 source)"

# ── Subcommand `failure` — §13.2's "facts + a failure log" ────────────────
echo "[failure]"

F="$WORK/s-fail"
run failure --store "$F" --signal ci-failure --summary 'lint job fails on markdownlint MD013' \
  --repro 'make lint'
check "failure exits 0" 0 "$RC"
check "failures.jsonl has 1 record" 1 "$(records_in "$F/failures.jsonl")"
check "failure record carries the summary" "lint job fails on markdownlint MD013" \
  "$(jfield "$F/failures.jsonl" 1 summary)"
check "failure record carries --repro" "make lint" "$(jfield "$F/failures.jsonl" 1 repro)"
check "failure record carries a UTC timestamp" "yes" "$(has_utc_ts "$F/failures.jsonl" 1)"

snap "$F/failures.jsonl" "$WORK/fail.snap1"
run failure --store "$F" --signal revert --summary 'reverted 3d123a5, symlink escape'
check "second failure exits 0" 0 "$RC"
check "two failures leave exactly 2 records" 2 "$(records_in "$F/failures.jsonl")"
check "failure log earlier bytes untouched" "yes" \
  "$(is_grown_prefix "$F/failures.jsonl" "$WORK/fail.snap1")"

run failure --store "$WORK/s-fbadsig" --signal hunch --summary 'feels slow'
check "failure unknown --signal exits 2" 2 "$RC"
run failure --store "$WORK/s-fempty" --signal ci-failure --summary '  '
check "failure whitespace-only --summary exits 2" 2 "$RC"

# facts and failures are separate logs — a failure must not land in facts.jsonl.
check "failure did not write facts.jsonl" "no-file" "$(records_in "$F/facts.jsonl")"

# ── Subcommand `gate` — THE §13.3 HARD LINE ──────────────────────────────
echo "[gate — §13.3 hard line]"

TREE="$WORK/tree"
POLICY_PATHS=(
  "prompts/system.md"                   # anything under a prompts/ directory
  "plugins/rsi-loop/prompts/inner.txt"  # ...including nested
  "policy.json"
  "hooks/pre-commit.sh"                 # hook logic
  ".claude/hooks/deny-edit.py"
  "CLAUDE.md"                           # behavioral rules
  "plugins/x/CLAUDE.md"                 # ...anywhere in the tree
  "agents/reviewer.md"                  # agent definitions
  "SKILL.md"                            # skill definitions
  "skills/foo/SKILL.md"
  "skills/foo/reference.md"             # skills/**/*.md
  "inner.workflow.mjs"                  # the inner-agent workflow
  "search-engine.mjs"                   # ...and the engine
  "commands/rsi.md"                     # commands are behavioral instructions
)
SAFE_PATHS=(
  "facts.jsonl"
  "failures.jsonl"
  "docs/NOTES.md"                       # prose, not policy
  "docs/HARNESS-RSI-DESIGN.md"
  "README.md"
  "tests/fixtures/x.json"
)
for p in "${POLICY_PATHS[@]}" "${SAFE_PATHS[@]}"; do
  mkdir -p "$TREE/$(dirname "$p")"; : > "$TREE/$p"
done

# Every additive-safe path passes, alone and together.
for p in "${SAFE_PATHS[@]}"; do
  run gate --store "$WORK/s-gate" --path "$TREE/$p"
  check "additive-safe: $p" 0 "$RC"
done
SAFE_ARGS=()
for p in "${SAFE_PATHS[@]}"; do SAFE_ARGS+=(--path "$TREE/$p"); done
run gate --store "$WORK/s-gate" "${SAFE_ARGS[@]}"
check "all-safe batch exits 0" 0 "$RC"

# Every policy path is REFUSED with exit 3. Auto-accept is not an option here:
# §13.1 says one task cannot resolve a 0.02–0.05 effect against MDE(1) = 0.124.
for p in "${POLICY_PATHS[@]}"; do
  run gate --store "$WORK/s-gate" --path "$TREE/$p"
  check "POLICY refused (exit 3): $p" 3 "$RC"
done

# The refusal must be legible, not a bare exit code: it explains that
# single-task evidence never licenses a policy change, cites MDE(1) = 0.124,
# and points at Track 3.
run gate --store "$WORK/s-gate" --path "$TREE/prompts/system.md"
check "refusal exits 3" 3 "$RC"
check "refusal cites MDE(1) = 0.124" "yes" "$(out_has '0\.124')"
check "refusal points at Track 3" "yes" "$(out_has 'track[ -]*3')"
check "refusal says single-task evidence is not enough" "yes" "$(out_has 'single[ -]task')"
# ...and it is not vacuous: it names WHICH path was policy.
check "refusal names the offending path" "yes" "$(out_has 'prompts/system\.md')"

# One bad apple refuses the whole batch, and the safe paths are not blamed.
run gate --store "$WORK/s-gate" \
  --path "$TREE/docs/NOTES.md" --path "$TREE/prompts/system.md" --path "$TREE/README.md"
check "policy mixed among safe paths still exits 3" 3 "$RC"
check "mixed refusal names the policy path" "yes" "$(out_has 'prompts/system\.md')"
check "mixed refusal does not blame NOTES.md" "no" "$(out_has 'NOTES\.md')"
check "mixed refusal does not blame README.md" "no" "$(out_has 'README\.md')"

# The gate classifies the path, not the file: it must work on a *proposed* edit
# that does not exist yet, and it must not be dodgeable by relabelling the
# change ("just recording a fact about the prompt").
run gate --store "$WORK/s-gate" --path "$TREE/prompts/does-not-exist-yet.md"
check "policy path refused before the file exists" 3 "$RC"
run gate --store "$WORK/s-gate" --path "$TREE/docs/not-created-yet.md"
check "safe path passes before the file exists" 0 "$RC"

# The gate must not be silently bypassable by calling it with nothing.
run gate --store "$WORK/s-gate"
check "gate with no --path is not a vacuous pass (exit 2)" 2 "$RC"

# ── The real teeth: no smuggling a policy edit in as a "fact about" it ────
echo "[gate teeth — fact --scope cannot smuggle policy]"

for p in "prompts/system.md" "CLAUDE.md" "hooks/pre-commit.sh" "search-engine.mjs" "commands/rsi.md"; do
  SS="$WORK/s-smuggle-$(echo "$p" | tr '/.' '--')"
  run fact --store "$SS" --signal user-correction \
    --text 'user said the reviewer prompt should demand a test plan' --scope "$TREE/$p"
  check "fact --scope on POLICY path refused (exit 3): $p" 3 "$RC"
  check "refused fact wrote nothing: $p" "no-file" "$(records_in "$SS/facts.jsonl")"
done

# ── Bypass resistance: normalize first, then classify ────────────────────
echo "[gate — classifier normalization]"

# Case folding is not a nicety here. On a case-insensitive filesystem (APFS,
# NTFS) `claude.md` IS `CLAUDE.md` and `PROMPTS/` IS `prompts/` — the same
# bytes on disk. A case-sensitive gate therefore hands out a real bypass, so
# the classifier compares casefolded.
CASE_BYPASSES=(
  "PROMPTS/x.md" "Prompts/x.md" "HOOKS/x.sh" "AGENTS/r.md" "agents/r.MD"
  "claude.md" "Claude.md" "CLAUDE.MD" "skill.md" "policy.JSON"
  "inner.WORKFLOW.MJS" "search-engine.MJS"
)
for p in "${CASE_BYPASSES[@]}"; do
  run gate --store "$WORK/s-gate" --path "$TREE/$p"
  check "case variant refused (exit 3): $p" 3 "$RC"
done

# Separator and filename-shape spellings of the same policy file. Backslash is
# a separator on Windows; Windows also strips trailing dots and spaces from a
# name, so `CLAUDE.md.` resolves to `CLAUDE.md` there.
SHAPE_BYPASSES=(
  'prompts\x.md' 'plugins\x\CLAUDE.md'
  "CLAUDE.md." "CLAUDE.md " " CLAUDE.md"
  "prompts" "prompts/" "x/prompts"       # the policy directory itself
  "hooks" "plugins/x/hooks/"
)
for p in "${SHAPE_BYPASSES[@]}"; do
  run gate --store "$WORK/s-gate" --path "$TREE/$p"
  check "shape variant refused (exit 3): $p" 3 "$RC"
done

# Unicode lookalikes. NFKC folds fullwidth forms to ASCII, so `ｐｒｏｍｐｔｓ/`
# cannot be a second spelling of the policy directory. (Casefolding alone does
# NOT do this: 'ｐｒｏｍｐｔｓ'.casefold() is still fullwidth.)
for p in 'ｐｒｏｍｐｔｓ/x.md' 'ＣＬＡＵＤＥ.md' 'ｈｏｏｋｓ/x.sh'; do
  run gate --store "$WORK/s-gate" --path "$p"
  check "fullwidth lookalike refused (exit 3): $p" 3 "$RC"
done

# `..` resolves both ways or not at all. It must collapse INTO a policy dir
# (asserted above) and equally collapse back OUT of one: prompts/../docs/x.md
# is docs/x.md, and refusing it would block a licensed additive write.
run gate --store "$WORK/s-gate" --path "$TREE/prompts/../docs/NOTES.md"
check "'..' out of a policy dir resolves to the safe path (exit 0)" 0 "$RC"

# A symlink with an innocent name is still an edit to the policy file it points
# at, so the resolved target is classified too — spelling is not a defence.
ln -s "$TREE/prompts/system.md" "$TREE/docs/looks-safe.md"
run gate --store "$WORK/s-gate" --path "$TREE/docs/looks-safe.md"
check "symlink to a policy file refused (exit 3)" 3 "$RC"
ln -s "$TREE/prompts" "$TREE/safe-dir"
run gate --store "$WORK/s-gate" --path "$TREE/safe-dir/system.md"
check "path through a symlinked policy dir refused (exit 3)" 3 "$RC"
# ...and resolution must not start refusing ordinary files.
ln -s "$TREE/docs/NOTES.md" "$TREE/docs/alias.md"
run gate --store "$WORK/s-gate" --path "$TREE/docs/alias.md"
check "symlink to a safe file still passes" 0 "$RC"

# An empty path is not a cleared path: "0 real paths, exit 0" is the vacuous
# pass again, one argument lower.
run gate --store "$WORK/s-gate" --path ''
check "empty --path is a usage error (exit 2)" 2 "$RC"
run gate --store "$WORK/s-gate" --path '   '
check "whitespace-only --path is a usage error (exit 2)" 2 "$RC"
run fact --store "$WORK/s-blankscope" --signal ci-failure --text 'x' --scope '  '
check "blank --scope is a usage error (exit 2)" 2 "$RC"

# One classifier, so `fact --scope` inherits every normalization above for free.
# If these pass while the `gate` cases above pass, the check is not duplicated
# at the call site.
i=0
for p in "PROMPTS/x.md" "claude.md" 'prompts\x.md' "x/prompts" "CLAUDE.md."; do
  i=$((i + 1))
  SS="$WORK/s-smug2-$i"
  run fact --store "$SS" --signal user-correction \
    --text 'a fact about the reviewer prompt' --scope "$TREE/$p"
  check "fact --scope normalizes too (exit 3): $p" 3 "$RC"
  check "normalized refusal wrote nothing: $p" "no-file" "$(records_in "$SS/facts.jsonl")"
done

# ── Robustness: no crash may impersonate a verdict ───────────────────────
echo "[robustness]"

# `python3 -OO` strips docstrings, so anything that reads __doc__ at startup
# dies with an AttributeError before argparse runs — exit 1, no verdict.
set +e
python3 -OO "$LABELS" gate --store "$WORK/s-oo" --path "$TREE/README.md" \
  > "$OUT_FILE" 2> "$ERR_FILE"
OO_RC=$?
set -e
check "runs under python3 -OO (docstrings stripped)" 0 "$OO_RC"
check "-OO run prints no traceback" "no" "$(out_has 'Traceback')"

# A hostile --store is an error the tool reports, not one the interpreter does.
: > "$WORK/store-is-a-file"
run fact --store "$WORK/store-is-a-file" --signal ci-failure --text 'x'
check "--store that is a file exits 2" 2 "$RC"
check "hostile --store prints no traceback" "no" "$(out_has 'Traceback')"

# ── Usage ────────────────────────────────────────────────────────────────
echo "[usage]"

run promote --store "$WORK/s-usage" --path "$TREE/prompts/system.md"
check "unknown subcommand exits 2" 2 "$RC"
run
check "no subcommand exits 2" 2 "$RC"

echo
echo "rsi-labels: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
