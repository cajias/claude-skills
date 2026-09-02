#!/usr/bin/env bash
set -euo pipefail

# Claude Code Skills Repository Validator
# Checks structural correctness of plugins, agents, skills, and marketplace sync.
# Run: npm run validate

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ERRORS=0
WARNINGS=0

red()    { printf "\033[31m%s\033[0m\n" "$1"; }
yellow() { printf "\033[33m%s\033[0m\n" "$1"; }
green()  { printf "\033[32m%s\033[0m\n" "$1"; }
dim()    { printf "\033[2m%s\033[0m\n" "$1"; }

error()   { red "  ERROR: $1"; ERRORS=$((ERRORS + 1)); }
warn()    { yellow "  WARN:  $1"; WARNINGS=$((WARNINGS + 1)); }
pass()    { dim "  OK:    $1"; }

section() { printf "\n\033[1m[%s]\033[0m\n" "$1"; }

# Print the YAML frontmatter (between the first '---' on line 1 and the next '---').
# Emits nothing if the file does not start with '---'.
extract_frontmatter() {
  awk 'NR==1 && $0!="---"{exit} NR==1{next} $0=="---"{exit} {print}' "$1"
}

# Length of the `description:` value in a frontmatter block read on stdin,
# with continuation lines joined and whitespace collapsed. Prints 0 when there
# is no description.
# The stop pattern must accept a BARE key (`metadata:`, nothing after the
# colon) as well as `key: value` — requiring a space after the colon let the
# nested lines of a `metadata:` block be swallowed into the description, the
# same over-capture class this file's extraction fix already addressed.
description_length() {
  awk '
    /^description:/ { sub(/^description:[[:space:]]*/, ""); d = $0; ind = 1; next }
    ind && /^[a-zA-Z0-9_-]+:([[:space:]]|$)/ { ind = 0 }
    ind { d = d " " $0 }
    END { gsub(/[[:space:]]+/, " ", d); gsub(/^ | $/, "", d); print length(d) }
  '
}

# ─── 1. Plugin Structure ───────────────────────────────────────────

section "Plugin Structure"

for dir in "$REPO_ROOT"/plugins/*/; do
  name="$(basename "$dir")"
  manifest="$dir.claude-plugin/plugin.json"

  if [[ ! -f "$manifest" ]]; then
    error "plugins/$name — missing .claude-plugin/plugin.json"
  elif ! jq empty "$manifest" 2>/dev/null; then
    error "plugins/$name — plugin.json is invalid JSON"
  else
    # Check required fields
    for field in name description version; do
      val=$(jq -r ".$field // empty" "$manifest")
      if [[ -z "$val" ]]; then
        error "plugins/$name — plugin.json missing required field: $field"
      fi
    done
    pass "plugins/$name"
  fi
done

# ─── 2. Marketplace Sync ──────────────────────────────────────────

section "Marketplace Sync"

MARKETPLACE="$REPO_ROOT/.claude-plugin/marketplace.json"

if [[ ! -f "$MARKETPLACE" ]]; then
  error "Missing .claude-plugin/marketplace.json"
else
  # Get plugin names listed in marketplace
  marketplace_names=$(jq -r '.plugins[].name' "$MARKETPLACE" | sort)

  # Get actual plugin directories
  actual_names=""
  for dir in "$REPO_ROOT"/plugins/*/; do
    name="$(basename "$dir")"
    actual_names="$actual_names$name"$'\n'
  done
  actual_names=$(echo "$actual_names" | sort | sed '/^$/d')

  # Plugins on disk that are NOT in marketplace.json are intentional
  # (hidden / WIP / private). The marketplace publishes a curated
  # subset of plugins/ — marketplace.json is the source of truth for published plugins.
  hidden_count=$(comm -23 <(echo "$actual_names") <(echo "$marketplace_names") | grep -c . || true)

  # Find plugins in marketplace but not on disk
  orphaned_in_marketplace=$(comm -13 <(echo "$actual_names") <(echo "$marketplace_names"))
  if [[ -n "$orphaned_in_marketplace" ]]; then
    while IFS= read -r name; do
      error "$name — listed in marketplace.json but no plugins/$name/ directory"
    done <<< "$orphaned_in_marketplace"
  fi

  if [[ -z "$orphaned_in_marketplace" ]]; then
    actual_count=$(echo "$actual_names" | wc -l | tr -d ' ')
    published_count=$(echo "$marketplace_names" | wc -l | tr -d ' ')
    pass "marketplace.json: $published_count published, $hidden_count hidden, $actual_count total on disk"
  fi

  # Version in marketplace.json must match each plugin's plugin.json (source of truth)
  while IFS=$'\t' read -r mp_name mp_version; do
    manifest="$REPO_ROOT/plugins/$mp_name/.claude-plugin/plugin.json"
    [[ -f "$manifest" ]] || continue
    pl_version=$(jq -r '.version // empty' "$manifest")
    if [[ "$mp_version" != "$pl_version" ]]; then
      error "$mp_name — marketplace.json version ($mp_version) != plugin.json version ($pl_version)"
    fi
  done < <(jq -r '.plugins[] | "\(.name)\t\(.version)"' "$MARKETPLACE")
fi

# ─── 3. Hooks Schema ──────────────────────────────────────────────

section "Hook Definitions"

while IFS= read -r -d '' hooks_file; do
  rel="${hooks_file#"$REPO_ROOT"/}"

  if ! jq empty "$hooks_file" 2>/dev/null; then
    error "$rel — invalid JSON"
    continue
  fi

  # Check for correct nested schema: should have "hooks" top-level key
  # with event names (PreToolUse, PostToolUse, etc.) as children
  has_hooks_key=$(jq 'has("hooks")' "$hooks_file")
  if [[ "$has_hooks_key" != "true" ]]; then
    error "$rel — missing top-level 'hooks' key (expected nested schema)"
  else
    pass "$rel"
  fi
done < <(find "$REPO_ROOT/plugins" -name "hooks.json" -not -path "*/node_modules/*" -print0)

# Also check for hooks defined inline in plugin.json
while IFS= read -r -d '' manifest; do
  rel="${manifest#"$REPO_ROOT"/}"
  has_hooks=$(jq 'has("hooks")' "$manifest" 2>/dev/null)
  if [[ "$has_hooks" == "true" ]]; then
    hook_count=$(jq '.hooks | length' "$manifest")
    pass "$rel — $hook_count hook event(s)"
  fi
done < <(find "$REPO_ROOT/plugins" -path "*/.claude-plugin/plugin.json" -print0)

# ─── 4. Agent Frontmatter ─────────────────────────────────────────

section "Agent Definitions"

REQUIRED_AGENT_FIELDS=(name description model)

for agent_file in "$REPO_ROOT"/agents/*.md; do
  [[ -f "$agent_file" ]] || continue
  name="$(basename "$agent_file")"

  # Extract YAML frontmatter (between first two --- lines)
  frontmatter=$(extract_frontmatter "$agent_file")

  if [[ -z "$frontmatter" ]]; then
    error "agents/$name — no YAML frontmatter found"
    continue
  fi

  has_error=false
  for field in "${REQUIRED_AGENT_FIELDS[@]}"; do
    if ! grep -q "^${field}:" <<< "$frontmatter"; then
      error "agents/$name — missing required frontmatter field: $field"
      has_error=true
    fi
  done

  if [[ "$has_error" == false ]]; then
    # Validate model value
    model_val=$(grep "^model:" <<< "$frontmatter" | sed 's/^model:[[:space:]]*//')
    case "$model_val" in
      sonnet|haiku|opus) pass "agents/$name (model: $model_val)" ;;
      *) warn "agents/$name — non-standard model value: '$model_val' (expected: sonnet, haiku, or opus)" ;;
    esac
  fi
done

# ─── 5. Skill Completeness ────────────────────────────────────────

section "Skill Completeness"

total_skills=0
valid_skills=0
empty_dirs=0
missing_frontmatter=0

for dir in "$REPO_ROOT"/skills/*/; do
  [[ -d "$dir" ]] || continue
  total_skills=$((total_skills + 1))
  name="$(basename "$dir")"
  skill_file="$dir/SKILL.md"

  if [[ ! -f "$skill_file" ]]; then
    error "skills/$name — directory exists but no SKILL.md file"
    empty_dirs=$((empty_dirs + 1))
    continue
  fi

  # Check for README.md (required by CI)
  if [[ ! -f "$dir/README.md" ]]; then
    error "skills/$name — missing README.md (required by CI)"
  fi

  # Check file is not empty
  if [[ ! -s "$skill_file" ]]; then
    error "skills/$name — SKILL.md is empty"
    continue
  fi

  # Check for YAML frontmatter
  first_line=$(head -1 "$skill_file")
  if [[ "$first_line" != "---" ]]; then
    warn "skills/$name — no YAML frontmatter (starts with: ${first_line:0:40})"
    missing_frontmatter=$((missing_frontmatter + 1))
    valid_skills=$((valid_skills + 1))
    continue
  fi

  # Check required frontmatter fields
  fm=$(extract_frontmatter "$skill_file")
  if ! grep -q "^name:" <<< "$fm"; then
    warn "skills/$name — frontmatter missing 'name' field"
  fi
  if ! grep -q "^description:" <<< "$fm"; then
    warn "skills/$name — frontmatter missing 'description' field"
  fi

  valid_skills=$((valid_skills + 1))
done

pass "$valid_skills/$total_skills skills have SKILL.md"
[[ $empty_dirs -gt 0 ]] && error "$empty_dirs empty skill directories"
[[ $missing_frontmatter -gt 0 ]] && warn "$missing_frontmatter skills without YAML frontmatter"

# ─── Skill Description Length ─────────────────────────────────────
# Claude Code truncates each description in the skill listing at
# skillListingMaxDescChars (default 1536). Past that, the trigger phrases the
# tail carries stop reaching the model, so the skill silently stops firing.
# Covers plugins/*/skills/ too — the section above only walks skills/.
# (1024 is the stricter Agent Skills spec limit, relevant only if these are
# ever consumed outside Claude Code; not enforced here.)

section "Skill Description Length"

DESC_CAP=1536
over_cap=0
worst_len=0
worst_file=""

while IFS= read -r skill_file; do
  len=$(extract_frontmatter "$skill_file" | description_length)
  [[ -z "$len" || "$len" -eq 0 ]] && continue
  if [[ "$len" -gt "$DESC_CAP" ]]; then
    over_cap=$((over_cap + 1))
    if [[ "$len" -gt "$worst_len" ]]; then
      worst_len="$len"
      worst_file="${skill_file#"$REPO_ROOT"/}"
    fi
  fi
done < <(find "$REPO_ROOT/plugins" "$REPO_ROOT/skills" -name SKILL.md \
  -not -path '*/node_modules/*' -not -path '*/.venv/*' 2>/dev/null)

if [[ $over_cap -gt 0 ]]; then
  warn "$over_cap skill description(s) over the $DESC_CAP-char listing cap — worst: $worst_file ($worst_len). Their trigger phrases are truncated away."
else
  pass "all skill descriptions within the $DESC_CAP-char listing cap"
fi

# ─── Test Suite CI Coverage ───────────────────────────────────────
# A node --test suite runs in CI only if some job pins its directory as a
# working-directory. Suites outside those directories run in no automation at
# all, so they can rot — or be deleted — without anything going red.

section "Test Suite CI Coverage"

CI_FILE="$REPO_ROOT/.github/workflows/ci.yml"
uncovered=0

if [[ ! -f "$CI_FILE" ]]; then
  warn "no .github/workflows/ci.yml — cannot check test suite coverage"
else
  while IFS= read -r suite_dir; do
    rel="${suite_dir#"$REPO_ROOT"/}"
    if ! grep -q "working-directory: $rel\$" "$CI_FILE"; then
      warn "$rel/tests runs in NO ci.yml job — add one or it is unguarded"
      uncovered=$((uncovered + 1))
    fi
  done < <(find "$REPO_ROOT/plugins" -path '*/tests/*.test.mjs' \
    -not -path '*/node_modules/*' -printf '%h\n' 2>/dev/null |
    sed 's|/tests$||' | sort -u)

  [[ $uncovered -eq 0 ]] && pass "every plugin .test.mjs suite has a ci.yml job"
fi

# ─── Summary ──────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $ERRORS -gt 0 ]]; then
  red "  FAILED: $ERRORS error(s), $WARNINGS warning(s)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 1
elif [[ $WARNINGS -gt 0 ]]; then
  yellow "  PASSED with $WARNINGS warning(s)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 0
else
  green "  ALL CHECKS PASSED"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 0
fi
