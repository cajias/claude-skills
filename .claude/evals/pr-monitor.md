# Eval: pr-monitor

Plugin path: plugins/pr-monitor

## Capability Evals

[CAPABILITY EVAL: pr-monitor-structure]
Task: Verify plugin has all required structural files and fields
Success Criteria:

- [ ] .claude-plugin/plugin.json exists and is valid JSON
- [ ] plugin.json has name, description, and version fields
- [ ] At least one skills/ subdirectory with a SKILL.md file
- [ ] Each SKILL.md has YAML frontmatter with name and description
- [ ] No APM references (apm pack, apm marketplace, Agent Package Manager)
      Expected Output: All structural checks pass
      Grader: code-based (bash — see scripts/test-skills.sh)

[CAPABILITY EVAL: pr-monitor-skill-quality]
Task: Verify skill descriptions are specific and triggerable
Success Criteria:

- [ ] Description is specific (not generic boilerplate)
- [ ] Skill content is substantial (> 200 chars per SKILL.md)
- [ ] Triggering context is clear in the description
- [ ] No placeholder text (TODO, TBD) in production skills
      Expected Output: All skill quality checks pass
      Grader: code-based (char count, grep)

## Regression Evals

[REGRESSION EVAL: pr-monitor-claude-native]
Baseline: APM era (pre-migration)
Tests:

- plugin.json uses Claude-native format (not APM format): MUST PASS
- No APM CLI dependency for installation: MUST PASS
- Plugin installable by copying to ~/.claude/plugins/: MUST PASS
  Result: 3/3 must pass

## Plugin-Specific Checks

This plugin contains one skill: `pr-monitor`, and ships a Stop hook that
enables automatic PR change detection.

### Skill: pr-monitor

**What it does:** Guides Claude through setting up automated GitHub PR monitoring
using a state file at `/tmp/claude_monitor_pr_<repo-name>_<pr-number>`. When
activated, a Stop hook (`hooks/Stop.sh`) intercepts each natural session end,
queries GitHub via `gh pr view`, compares the current commit SHA against the
recorded one, and auto-resumes the session with a new-commit notification if
the PR has been updated. Monitoring stops automatically when the PR is merged
or closed.

**Trigger context:** The skill is invoked when a user wants to:
(1) continuously watch a PR for new commits without manual polling;
(2) provide automated review feedback whenever a collaborator or bot (e.g.
GitHub Copilot) pushes changes to a PR;
(3) stay in a Claude Code session that self-resumes on PR activity.

**Plugin-specific assertions:**

- [ ] `hooks/hooks.json` registers a `Stop` hook that invokes
      `${CLAUDE_PLUGIN_ROOT}/scripts/Stop.sh` — this is the automation backbone;
      without it the skill is documentation only
- [ ] `hooks/Stop.sh` (symlinked or copied from `scripts/Stop.sh`) exists and
      is executable
- [ ] The SKILL.md describes all six phases: Identify, Setup, Initial Review,
      Wait, Auto-Resume, and Stop
- [ ] State file path convention (`/tmp/claude_monitor_pr_<repo>_<pr>`) is
      documented with all three required lines (repo_path, pr_number, last_sha)
- [ ] The skill documents automatic cleanup — PR merged/closed causes the Stop
      hook to remove the state file rather than resuming indefinitely
- [ ] The skill lists the `gh` CLI as a hard prerequisite with an install URL
- [ ] Content length: SKILL.md body exceeds 5000 characters (it is a
      multi-phase operational guide, not a stub)
- [ ] The skill's limitations section explicitly calls out polling-based
      (not real-time push) behavior and the dependency on an active Claude Code
      session

**Regression assertion (specific to this skill):**

- [ ] The state file write example in the SKILL.md uses a heredoc that
      correctly expands shell variables (no literal `$REPO_PATH` written verbatim
      into the file when the heredoc delimiter is quoted as `<<'EOF'`)
- [ ] No references to `apm`, `Agent Package Manager`, or APM marketplace
      commands appear anywhere in the plugin tree
- [ ] `plugin.json` `requirements` field lists `gh` with minimum version
      `v2.0.0` and an install URL — the hard runtime dependency is declared

## Metrics Target

- pass@1: 100% for structure (deterministic)
- pass@3: > 90% for skill quality
