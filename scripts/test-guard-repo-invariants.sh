#!/usr/bin/env bash
# Behavioral tests for scripts/guard-repo-invariants.sh: feed it the exact JSON
# Claude Code sends on PreToolUse and assert block (exit 2) vs allow (exit 0).
#
# The allow cases matter as much as the block cases — a guard that blocks the
# normal rebase workflow or an ordinary commit gets disabled within a day.
set -uo pipefail

GUARD="$(cd "$(dirname "$0")" && pwd)/guard-repo-invariants.sh"
PASS=0
FAIL=0

check() { # $1 = block|allow, $2 = label, $3 = payload JSON
  local rc=0
  printf '%s' "$3" | bash "$GUARD" >/dev/null 2>&1 || rc=$?
  local got="allow"
  [ "$rc" -eq 2 ] && got="block"
  if [ "$got" = "$1" ]; then
    PASS=$((PASS + 1))
    printf '  ok   %-5s %s\n' "$1" "$2"
  else
    FAIL=$((FAIL + 1))
    printf '  FAIL want=%s got=%s (exit %d)  %s\n' "$1" "$got" "$rc" "$2"
  fi
}

edit() { printf '{"tool_name":"Edit","tool_input":{"file_path":"%s"}}' "$1"; }
sh_() { # jq -n keeps quoting/escaping correct for arbitrary shell text
  jq -nc --arg c "$1" '{tool_name:"Bash",tool_input:{command:$c}}'
}

echo "[1] frozen run evidence"
check block "edit inside experiments/" \
  "$(edit /repo/plugins/rsi-loop/docs/experiments/run-001/notes.md)"
check allow "edit elsewhere in rsi-loop" \
  "$(edit /repo/plugins/rsi-loop/docs/PLAN.md)"
check allow "path merely containing 'experiments'" \
  "$(edit /repo/plugins/other/experiments-guide.md)"

echo "[2] commit gate bypass"
check block "git commit --no-verify" "$(sh_ 'git commit --no-verify -m "x"')"
check block "git commit -n" "$(sh_ 'git commit -n -m "x"')"
check allow "ordinary commit" "$(sh_ 'git commit -m "feat: x"')"
check allow "commit with body via -F" "$(sh_ 'git commit -F -')"

# Regression: the guard blocked its OWN commit because the message body
# discussed the flag. Heredoc bodies are prose, not invocations.
echo "[2b] heredoc bodies are text, not commands"
check allow "commit whose message mentions the bypass flag" \
  "$(sh_ "$(printf 'git commit -F - <<EOF\nchore: explain why --no-verify is blocked\nEOF')")"
check allow "commit message mentioning pip install" \
  "$(sh_ "$(printf "git commit -F - <<'EOF'\ndocs: say pip install is banned here\nEOF")")"
check block "real bypass alongside a heredoc" \
  "$(sh_ "$(printf 'git commit --no-verify -F - <<EOF\nchore: sneaky\nEOF')")"
check block "banned command on a later line of a script" \
  "$(sh_ "$(printf 'set -e\ncd plugins/semantic-search\npip install pytest')")"

# Regression: `grep -n` in one command plus `git commit` in another combined
# into a phantom bypass. Rules must apply per invocation, not to the whole blob.
echo "[2c] rules apply per invocation, not across a chain"
check allow "grep -n on one line, git commit on another" \
  "$(sh_ "$(printf 'grep -n "cases" CLAUDE.md\ngit add -A\ngit commit -F -')")"
check allow "chained with && across separate commands" \
  "$(sh_ 'grep -n x file && git commit -m "ok"')"
check block "bypass in a chained command is still caught" \
  "$(sh_ 'make validate && git commit --no-verify -m "x"')"

echo "[3] uv/ruff only"
check block "pip install" "$(sh_ 'pip install pytest')"
check block "pip3 install" "$(sh_ 'pip3 install -r reqs.txt')"
check block "black" "$(sh_ 'black plugins/semantic-search')"
check allow "uv add" "$(sh_ 'uv add --dev pytest')"
check allow "ruff format" "$(sh_ 'uv run ruff format .')"
check allow "word containing black" "$(sh_ 'grep blacklist src/')"

echo "[4] force-push to main"
check block "explicit main" "$(sh_ 'git push --force origin main')"
check block "explicit master" "$(sh_ 'git push -f origin master')"
check block "force-with-lease to main" \
  "$(sh_ 'git push --force-with-lease origin main')"
check block "refspec HEAD:main" "$(sh_ 'git push --force origin HEAD:main')"
# The normal rebase workflow — must never be blocked.
check allow "force-push a feature branch" \
  "$(sh_ 'git push --force-with-lease origin feat/my-thing')"
check allow "force-push branch whose name contains main" \
  "$(sh_ 'git push --force origin feat/maintain-docs')"
check allow "plain push to main (not forced)" "$(sh_ 'git push origin main')"

# With no refspec, git pushes the current branch, so the verdict depends on
# HEAD rather than on the command text. Run the guard inside throwaway repos
# to cover both branches — otherwise the riskiest rule is untested.
echo "[4b] force-push with no refspec (depends on HEAD)"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
for branch in main feat/x; do
  repo="$tmp/${branch//\//-}"
  git init --quiet -b "$branch" "$repo" 2>/dev/null
  want=$([ "$branch" = "main" ] && echo block || echo allow)
  rc=0
  (cd "$repo" && printf '%s' "$(sh_ 'git push --force')" |
    bash "$GUARD" >/dev/null 2>&1) || rc=$?
  got="allow"
  [ "$rc" -eq 2 ] && got="block"
  if [ "$got" = "$want" ]; then
    PASS=$((PASS + 1))
    printf '  ok   %-5s bare --force while on %s\n' "$want" "$branch"
  else
    FAIL=$((FAIL + 1))
    printf '  FAIL want=%s got=%s  bare --force while on %s\n' "$want" "$got" "$branch"
  fi
done

echo "[5] payload robustness"
check allow "unknown tool" '{"tool_name":"Read","tool_input":{"file_path":"/x"}}'
check allow "empty object" '{}'
check allow "no file_path" '{"tool_name":"Edit","tool_input":{}}'
check allow "malformed json" 'not json at all'

printf '\n  %d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
