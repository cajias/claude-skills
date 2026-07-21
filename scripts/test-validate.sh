#!/usr/bin/env bash
# Regression tests for scripts/validate.sh's extract_frontmatter() helper.
#
# Guards the fix that replaced the old `sed -n '/^---$/,/^---$/p' | sed '1d;$d'`
# frontmatter extraction. That pipeline had two defects this suite pins down:
#   (a) OVER-CAPTURE — a SKILL.md / agent .md that uses `---` as a body section
#       separator (e.g. skills/hld-phase-executor/SKILL.md) made the second sed
#       range re-open, swallowing the whole document instead of just the header.
#   (b) FLAKY SIGPIPE — under `set -o pipefail`, `echo "$fm" | grep -q` lost a
#       SIGPIPE race (~6% of runs) and reported bogus "missing name/description"
#       warnings. The shipped code now uses an awk helper (stops at the 2nd ---)
#       plus here-string greps, which are deterministic.
#
# NOT `set -e`: assertions must keep running after one fails so we see them all.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VALIDATE="$SCRIPT_DIR/validate.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PASS=0
FAIL=0

check() { # $1 label, $2 expected, $3 actual
  if [[ "$2" == "$3" ]]; then
    PASS=$((PASS + 1)); printf '  ok   %s\n' "$1"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL %s (want %s, got %s)\n' "$1" "$2" "$3"
  fi
}

# grep-as-value: emit yes/no instead of leaking grep's exit status.
has() { grep -q "$1" <<< "$2" && echo yes || echo no; }

echo "[test-validate]"

# ─── Load the REAL shipped extract_frontmatter() into this shell ─────
# Pull only the function definition out of validate.sh so the test exercises
# the exact code that ships, without running the whole repo-wide validator.
[[ -f "$VALIDATE" ]] || { echo "  cannot find $VALIDATE"; exit 1; }
eval "$(sed -n '/^extract_frontmatter()/,/^}/p' "$VALIDATE")"
check "extract_frontmatter is loaded as a function" function "$(type -t extract_frontmatter || true)"

# ─── Fixtures ────────────────────────────────────────────────────────
NORMAL="$WORK/normal.md"
cat > "$NORMAL" <<'EOF'
---
name: normal-skill
description: a plain skill with a simple header
---

# Body

Ordinary body content, no separators.
EOF

# Mirrors the shape of skills/hld-phase-executor/SKILL.md: valid header, then a
# body peppered with `---` horizontal rules that the old sed range re-opened.
BODYSEP="$WORK/body-separator.md"
cat > "$BODYSEP" <<'EOF'
---
name: body-sep-skill
description: header followed by body horizontal rules
---

# Phase 1

Intro text.

---

## Phase 2

More text.

---

## Phase 3

name: not-a-field
description: this line lives in the body and must be ignored

---

Done.
EOF

NOFM="$WORK/no-frontmatter.md"
cat > "$NOFM" <<'EOF'
# Just a title

This document has no YAML frontmatter at all.
name: should-not-be-seen
description: should-not-be-seen
EOF

# ─── 1. Normal frontmatter: header fields are found ──────────────────
fm="$(extract_frontmatter "$NORMAL")"
check "normal: extracts name"        yes "$(has '^name:' "$fm")"
check "normal: extracts description" yes "$(has '^description:' "$fm")"

# ─── 2. Body-separator file: NOT over-captured ───────────────────────
# The header ends at the first closing `---`; the body's `---` rules and its
# stray `name:`/`description:` lines must never leak into the frontmatter.
fm="$(extract_frontmatter "$BODYSEP")"
check "body-sep: zero '---' lines captured" 0   "$(grep -c '^---$' <<< "$fm")"
check "body-sep: still finds header name"    yes "$(has '^name: body-sep-skill' "$fm")"
check "body-sep: still finds header desc"    yes "$(has '^description: header' "$fm")"
check "body-sep: body 'name:' NOT captured"  no  "$(has '^name: not-a-field' "$fm")"

# ─── 3. No frontmatter: empty output ─────────────────────────────────
fm="$(extract_frontmatter "$NOFM")"
check "no-frontmatter: emits empty string" empty "$([[ -z "$fm" ]] && echo empty || echo nonempty)"

# ─── 4. Flakiness regression (deterministic, 200 iterations) ─────────
# Under the OLD `echo "$fm" | grep -q` pipeline this flaked ~6% of the time,
# yielding false "missing name" warnings. The here-string form must be 100%
# stable: assert ZERO missing-name detections across 200 runs.
flaky_fail=0
for _ in $(seq 1 200); do
  fm="$(extract_frontmatter "$BODYSEP")"
  grep -q '^name:' <<< "$fm" || flaky_fail=$((flaky_fail + 1))
done
check "flakiness: 0 missing-name over 200 iterations" 0 "$flaky_fail"

# ─── Summary ─────────────────────────────────────────────────────────
echo
echo "test-validate: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
