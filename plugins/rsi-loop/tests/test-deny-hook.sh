#!/usr/bin/env bash
# Behavioral tests for hooks/deny-private.py: feed the hook the exact JSON
# Claude Code sends on PreToolUse and assert deny/allow.
set -euo pipefail

HOOK="$(cd "$(dirname "$0")/.." && pwd)/hooks/deny-private.py"
PASS=0
FAIL=0

run_hook() { # $1 = tool_name, $2 = tool_input JSON
  printf '{"hook_event_name":"PreToolUse","tool_name":"%s","tool_input":%s}' "$1" "$2" |
    RSI_HOOK_DISARM='' python3 "$HOOK"
}

expect() { # $1 = deny|allow, $2 = label, $3 = tool, $4 = input JSON
  local out decision="allow"
  out="$(run_hook "$3" "$4")"
  if [[ "$out" == *'"permissionDecision": "deny"'* || "$out" == *'"permissionDecision":"deny"'* ]]; then
    decision="deny"
  fi
  if [[ "$decision" == "$1" ]]; then
    PASS=$((PASS + 1))
    printf '  ok   %-8s %s\n' "$1" "$2"
  else
    FAIL=$((FAIL + 1))
    printf '  FAIL want=%s got=%s  %s\n    hook output: %s\n' "$1" "$decision" "$2" "$out"
  fi
}

echo "[deny-private hook]"

# ── Attacks that must be denied ──────────────────────────────────────
expect deny "Read private instances" Read \
  '{"file_path":"/w/rsi-runs/r1/tasks/bin-packing/private/instances.json"}'
expect deny "Read plugin-source private split" Read \
  '{"file_path":"/repo/plugins/rsi-loop/tasks/bin-packing/private/instances.json"}'
expect deny "Glob into private dir" Glob \
  '{"pattern":"rsi-runs/r1/tasks/*/private/**"}'
expect deny "Grep private path" Grep \
  '{"pattern":"score","path":"/w/rsi-runs/r1/tasks/bp/private"}'
expect deny "Bash cat private file" Bash \
  '{"command":"cat rsi-runs/r1/tasks/bp/private/instances.json"}'
expect deny "Bash score --private without outer mark" Bash \
  '{"command":"python3 score.py --private --solution solution.py"}'
expect deny "Bash wrapper --private without outer mark" Bash \
  '{"command":"bash /p/scripts/rsi-score.sh --private t s.py"}'
expect deny "Bash env-var smuggle without prefix" Bash \
  '{"command":"cd rsi-runs/r1 && RSI_OUTER_LOOP=1 python3 tasks/bp/score.py --private --solution s.py"}'
expect deny "Bash glob evasion p*" Bash \
  '{"command":"cat rsi-runs/r1/tasks/bp/p*/instances.json"}'
expect deny "Bash glob evasion ?rivate" Bash \
  '{"command":"cat rsi-runs/r1/tasks/bp/?rivate/instances.json"}'
expect deny "Bash symlink into private" Bash \
  '{"command":"ln -s rsi-runs/r1/tasks/bp/private peek"}'
expect deny "Bash copy private elsewhere" Bash \
  '{"command":"cp -r holdout-tasks/x/private /tmp/loot"}'
expect deny "Write into run task battery" Write \
  '{"file_path":"/w/rsi-runs/r1/tasks/bp/public/instances.json","content":"[]"}'
expect deny "Edit scorer" Edit \
  '{"file_path":"/w/rsi-runs/r1/tasks/bp/score.py","old_string":"a","new_string":"b"}'
expect deny "Edit plugin-source scorer" Edit \
  '{"file_path":"/repo/plugins/rsi-loop/tasks/bin-packing/score.py","old_string":"a","new_string":"b"}'
expect deny "Bash overwrite battery via tee" Bash \
  '{"command":"echo x | tee rsi-runs/r1/tasks/bp/public/instances.json"}'
expect deny "Bash append to scorer" Bash \
  '{"command":"echo pwned >> rsi-runs/r1/tasks/bp/score.py"}'

# ── Legitimate calls that must be allowed ────────────────────────────
expect allow "Read task.md" Read \
  '{"file_path":"/w/rsi-runs/r1/work/g1-bp/task.md"}'
expect allow "Read public instances" Read \
  '{"file_path":"/w/rsi-runs/r1/tasks/bp/public/instances.json"}'
expect allow "Bash public scoring" Bash \
  '{"command":"python3 score.py --public --solution solution.py --json"}'
expect allow "Bash outer-marked private scoring" Bash \
  '{"command":"RSI_OUTER_LOOP=1 bash /p/scripts/rsi-score.sh --private /w/rsi-runs/r1/tasks/bp nodes/n3/solution.py"}'
expect allow "Write solution in work area" Write \
  '{"file_path":"/w/rsi-runs/r1/work/g1-bp/nodes/n1/solution.py","content":"def pack..."}'
expect allow "Write new generation file" Write \
  '{"file_path":"/w/rsi-runs/r1/generations/gen-003/policy.json","content":"{}"}'
expect allow "Bash unrelated private word" Bash \
  '{"command":"git log --oneline -- src/privatelib.rs"}'
expect allow "Read unrelated project private dir" Read \
  '{"file_path":"/home/u/app/private/config.json"}'
expect allow "Bash ls sandbox public" Bash \
  '{"command":"ls public/"}'
expect allow "Grep task.md in sandbox" Grep \
  '{"pattern":"capacity","path":"/w/rsi-runs/r1/work/g1-bp"}'
expect allow "Edit generation prompt" Edit \
  '{"file_path":"/w/rsi-runs/r1/generations/gen-002/prompts/draft.md","old_string":"a","new_string":"b"}'

# Disarm escape hatch for humans
out="$(printf '{"tool_name":"Read","tool_input":{"file_path":"rsi-runs/r/tasks/t/private/x"}}' | RSI_HOOK_DISARM=1 python3 "$HOOK")"
if [[ -z "$out" ]]; then
  PASS=$((PASS + 1)); echo "  ok   allow    RSI_HOOK_DISARM=1 disarms"
else
  FAIL=$((FAIL + 1)); echo "  FAIL RSI_HOOK_DISARM=1 did not disarm: $out"
fi

echo
echo "deny-private hook: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
