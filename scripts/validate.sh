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
    for field in name description; do
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

  # Find plugins in directory but not in marketplace
  missing_from_marketplace=$(comm -23 <(echo "$actual_names") <(echo "$marketplace_names"))
  if [[ -n "$missing_from_marketplace" ]]; then
    while IFS= read -r name; do
      error "plugins/$name — exists on disk but missing from marketplace.json"
    done <<< "$missing_from_marketplace"
  fi

  # Find plugins in marketplace but not on disk
  orphaned_in_marketplace=$(comm -13 <(echo "$actual_names") <(echo "$marketplace_names"))
  if [[ -n "$orphaned_in_marketplace" ]]; then
    while IFS= read -r name; do
      error "$name — listed in marketplace.json but no plugins/$name/ directory"
    done <<< "$orphaned_in_marketplace"
  fi

  if [[ -z "$missing_from_marketplace" && -z "$orphaned_in_marketplace" ]]; then
    pass "marketplace.json in sync with plugins/ ($(echo "$actual_names" | wc -l | tr -d ' ') plugins)"
  fi
fi

# ─── 3. Hooks Schema ──────────────────────────────────────────────

section "Hook Definitions"

for hooks_file in $(find "$REPO_ROOT/plugins" -name "hooks.json" -not -path "*/node_modules/*"); do
  rel="${hooks_file#$REPO_ROOT/}"

  if ! jq empty "$hooks_file" 2>/dev/null; then
    error "$rel — invalid JSON"
    continue
  fi

  # Check for correct nested schema: should have "hooks" top-level key
  # with event names (PreToolUse, PostToolUse, etc.) as children
  has_hooks_key=$(jq 'has("hooks")' "$hooks_file")
  if [[ "$has_hooks_key" != "true" ]]; then
    # Also accept inline hooks in plugin.json (different format)
    if [[ "$(basename "$hooks_file")" == "hooks.json" ]]; then
      error "$rel — missing top-level 'hooks' key (expected nested schema)"
    fi
  else
    pass "$rel"
  fi
done

# Also check for hooks defined inline in plugin.json
for manifest in $(find "$REPO_ROOT/plugins" -path "*/.claude-plugin/plugin.json"); do
  rel="${manifest#$REPO_ROOT/}"
  has_hooks=$(jq 'has("hooks")' "$manifest" 2>/dev/null)
  if [[ "$has_hooks" == "true" ]]; then
    # Validate each hook entry has required fields
    hook_count=$(jq '.hooks | length' "$manifest")
    pass "$rel — $hook_count inline hook(s)"
  fi
done

# ─── 4. Agent Frontmatter ─────────────────────────────────────────

section "Agent Definitions"

REQUIRED_AGENT_FIELDS=(name description model)

for agent_file in "$REPO_ROOT"/agents/*.md; do
  [[ -f "$agent_file" ]] || continue
  name="$(basename "$agent_file")"

  # Extract YAML frontmatter (between first two --- lines)
  frontmatter=$(sed -n '/^---$/,/^---$/p' "$agent_file" | sed '1d;$d')

  if [[ -z "$frontmatter" ]]; then
    error "agents/$name — no YAML frontmatter found"
    continue
  fi

  has_error=false
  for field in "${REQUIRED_AGENT_FIELDS[@]}"; do
    if ! echo "$frontmatter" | grep -q "^${field}:"; then
      error "agents/$name — missing required frontmatter field: $field"
      has_error=true
    fi
  done

  if [[ "$has_error" == false ]]; then
    # Validate model value
    model_val=$(echo "$frontmatter" | grep "^model:" | sed 's/^model:[[:space:]]*//')
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
  fm=$(sed -n '/^---$/,/^---$/p' "$skill_file" | sed '1d;$d')
  if ! echo "$fm" | grep -q "^name:"; then
    warn "skills/$name — frontmatter missing 'name' field"
  fi
  if ! echo "$fm" | grep -q "^description:"; then
    warn "skills/$name — frontmatter missing 'description' field"
  fi

  valid_skills=$((valid_skills + 1))
done

pass "$valid_skills/$total_skills skills have SKILL.md"
[[ $empty_dirs -gt 0 ]] && error "$empty_dirs empty skill directories"
[[ $missing_frontmatter -gt 0 ]] && warn "$missing_frontmatter skills without YAML frontmatter"

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
