#!/usr/bin/env bash
set -euo pipefail

# test-skills.sh — Validates each plugin in plugins/* for structural correctness.
# Usage:
#   bash scripts/test-skills.sh              # test all plugins
#   bash scripts/test-skills.sh claudeception # test single plugin

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGINS_DIR="$REPO_ROOT/plugins"

PASSED=0
FAILED=0

# ─── Colour helpers ────────────────────────────────────────────────
green()  { printf "\033[32m%s\033[0m\n" "$*"; }
red()    { printf "\033[31m%s\033[0m\n" "$*"; }
yellow() { printf "\033[33m%s\033[0m\n" "$*"; }
dim()    { printf "\033[2m%s\033[0m\n" "$*"; }

# ─── Per-plugin check ─────────────────────────────────────────────
check_plugin() {
  local plugin_dir="$1"
  local name
  name="$(basename "$plugin_dir")"
  local plugin_errors=()

  # (a) .claude-plugin/plugin.json exists and is valid JSON
  local manifest="$plugin_dir/.claude-plugin/plugin.json"
  if [[ ! -f "$manifest" ]]; then
    plugin_errors+=("missing .claude-plugin/plugin.json")
  elif ! jq empty "$manifest" 2>/dev/null; then
    plugin_errors+=("plugin.json is not valid JSON")
  else
    # (b) plugin.json has name, description, version fields
    for field in name description version; do
      local val
      val="$(jq -r ".$field // empty" "$manifest")"
      if [[ -z "$val" ]]; then
        plugin_errors+=("plugin.json missing required field: $field")
      fi
    done
  fi

  # (c) Count every component type a Claude Code plugin may provide.
  #     A plugin is valid with ANY of: skills, commands, agents, hooks, or an
  #     MCP server — not specifically skills. node_modules / .venv are excluded.
  local skill_count commands_count agents_count
  skill_count="$(find "$plugin_dir" -name "SKILL.md" -not -path '*/node_modules/*' -not -path '*/.venv/*' 2>/dev/null | wc -l | tr -d ' ')"
  commands_count="$(find "$plugin_dir" -path '*/commands/*.md' -not -path '*/node_modules/*' -not -path '*/.venv/*' 2>/dev/null | wc -l | tr -d ' ')"
  agents_count="$(find "$plugin_dir" -path '*/agents/*.md' -not -path '*/node_modules/*' -not -path '*/.venv/*' 2>/dev/null | wc -l | tr -d ' ')"

  # hooks: a hooks.json file anywhere, OR a .hooks key in plugin.json
  local hooks_file_count manifest_hooks has_hooks=0
  hooks_file_count="$(find "$plugin_dir" -name "hooks.json" -not -path '*/node_modules/*' -not -path '*/.venv/*' 2>/dev/null | wc -l | tr -d ' ')"
  manifest_hooks="$(jq -r 'if .hooks != null then "yes" else empty end' "$manifest" 2>/dev/null || true)"
  if [[ "$hooks_file_count" -gt 0 || -n "$manifest_hooks" ]]; then
    has_hooks=1
  fi

  # mcp: a .mcp.json file anywhere, OR an mcpServers/mcp key in plugin.json
  local mcp_file_count manifest_mcp has_mcp=0
  mcp_file_count="$(find "$plugin_dir" -name ".mcp.json" -not -path '*/node_modules/*' -not -path '*/.venv/*' 2>/dev/null | wc -l | tr -d ' ')"
  manifest_mcp="$(jq -r 'if (.mcpServers != null or .mcp != null) then "yes" else empty end' "$manifest" 2>/dev/null || true)"
  if [[ "$mcp_file_count" -gt 0 || -n "$manifest_mcp" ]]; then
    has_mcp=1
  fi

  # Collect the component types that are present (for the PASS summary).
  local components=()
  [[ "$skill_count" -gt 0 ]] && components+=("skills") || true
  [[ "$commands_count" -gt 0 ]] && components+=("commands") || true
  [[ "$agents_count" -gt 0 ]] && components+=("agents") || true
  [[ "$has_hooks" -eq 1 ]] && components+=("hooks") || true
  [[ "$has_mcp" -eq 1 ]] && components+=("mcp") || true

  local total=$((skill_count + commands_count + agents_count + has_hooks + has_mcp))
  if [[ "$total" -eq 0 ]]; then
    plugin_errors+=("no components found (needs at least one skill, command, agent, hook, or MCP server)")
  fi

  # (d) When skills exist, each SKILL.md first line must be "---" (YAML frontmatter)
  if [[ "$skill_count" -gt 0 ]]; then
    while IFS= read -r skill_file; do
      local first_line
      first_line="$(head -1 "$skill_file")"
      if [[ "$first_line" != "---" ]]; then
        local rel="${skill_file#"$plugin_dir"/}"
        plugin_errors+=("$rel — first line is not '---' (no YAML frontmatter)")
      fi
    done < <(find "$plugin_dir" -name "SKILL.md" -not -path '*/node_modules/*' -not -path '*/.venv/*')
  fi

  # (e) No APM references in any file under the plugin directory
  local apm_hits
  apm_hits="$(grep -rl --exclude-dir=node_modules --exclude-dir=.venv "apm pack\|apm marketplace\|Agent Package Manager" "$plugin_dir" 2>/dev/null || true)"
  if [[ -n "$apm_hits" ]]; then
    while IFS= read -r hit_file; do
      local rel="${hit_file#"$plugin_dir"/}"
      plugin_errors+=("APM reference found in $rel")
    done <<< "$apm_hits"
  fi

  # ─── Result ─────────────────────────────────────────────────────
  if [[ ${#plugin_errors[@]} -eq 0 ]]; then
    local comp_list=""
    if [[ ${#components[@]} -gt 0 ]]; then
      local c
      for c in "${components[@]}"; do
        if [[ -z "$comp_list" ]]; then comp_list="$c"; else comp_list="$comp_list, $c"; fi
      done
      green "  PASS  $name  [$comp_list]"
    else
      green "  PASS  $name"
    fi
    PASSED=$((PASSED + 1))
  else
    red "  FAIL  $name"
    for err in "${plugin_errors[@]}"; do
      yellow "        - $err"
    done
    FAILED=$((FAILED + 1))
  fi
}

# ─── Main ─────────────────────────────────────────────────────────
echo ""
printf "\033[1m[Plugin Checks]\033[0m\n"

if [[ $# -ge 1 ]]; then
  # Single-plugin mode
  target_dir="$PLUGINS_DIR/$1"
  if [[ ! -d "$target_dir" ]]; then
    red "ERROR: plugin directory not found: $target_dir"
    exit 1
  fi
  check_plugin "$target_dir"
else
  # All-plugins mode
  for plugin_dir in "$PLUGINS_DIR"/*/; do
    [[ -d "$plugin_dir" ]] || continue
    check_plugin "$plugin_dir"
  done
fi

# ─── Summary ──────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "  %s passed, %s failed\n" "$PASSED" "$FAILED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ $FAILED -gt 0 ]]; then
  exit 1
fi
