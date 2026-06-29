# Eval: session-mining

Plugin path: plugins/session-mining

## Capability Evals

[CAPABILITY EVAL: session-mining-structure]
Task: Verify plugin has all required structural files and fields
Success Criteria:

- [ ] .claude-plugin/plugin.json exists and is valid JSON
- [ ] plugin.json has name, description, and version fields
- [ ] At least one commands/ subdirectory with a .md command file
- [ ] Each command .md has YAML frontmatter with name and description
- [ ] No APM references (apm pack, apm marketplace, Agent Package Manager)
      Expected Output: All structural checks pass
      Grader: code-based (bash — see scripts/test-skills.sh)

[CAPABILITY EVAL: session-mining-skill-quality]
Task: Verify skill descriptions are specific and triggerable
Success Criteria:

- [ ] Description is specific (not generic boilerplate)
- [ ] Command content is substantial (> 200 chars per command .md)
- [ ] Triggering context is clear in the description
- [ ] No placeholder text (TODO, TBD) in production skills
      Expected Output: All skill quality checks pass
      Grader: code-based (char count, grep)

## Regression Evals

[REGRESSION EVAL: session-mining-claude-native]
Baseline: APM era (pre-migration)
Tests:

- plugin.json uses Claude-native format (not APM format): MUST PASS
- No APM CLI dependency for installation: MUST PASS
- Plugin installable by copying to ~/.claude/plugins/: MUST PASS
  Result: 3/3 must pass

## Plugin-Specific Checks

### Plugin Structure Note

session-mining uses a `commands/` directory (not `skills/`) and a `scripts/` directory.
It ships one command and one supporting script; it has no SKILL.md files.
The structure eval's SKILL.md checks are N/A — override with command-level assertions below.

### Commands Inventory

| Command       | File                      | Purpose                                                                                           |
| ------------- | ------------------------- | ------------------------------------------------------------------------------------------------- |
| mine-sessions | commands/mine-sessions.md | Invoke /claudeception on historical Claude Code sessions to extract reusable knowledge and skills |

Assertions for the command file:

- [ ] YAML frontmatter present with name and description fields
- [ ] description is specific: references claudeception, session history, and knowledge extraction
- [ ] arguments block defines at least one optional argument (options/flags)
- [ ] Body describes what the command does step-by-step (not just a one-liner)
- [ ] References `${CLAUDE_PLUGIN_ROOT}` for the script path (not a hardcoded path)
- [ ] Includes usage examples with concrete flag combinations

### Supporting Script

| Script                        | File                                  | Purpose                                                                                                     |
| ----------------------------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| claudeception-all-sessions.sh | scripts/claudeception-all-sessions.sh | Bash driver that scans ~/.claude/projects, filters sessions, and runs `claude --resume` with /claudeception |

Assertions for the script:

- [ ] Script is executable (has shebang and execute bit — or documented to be chmod +x'd on install)
- [ ] Uses `${CLAUDE_PLUGIN_ROOT}` or relative path — does NOT hardcode absolute paths to the plugin
- [ ] Supports --dry-run flag (safe preview mode with no side effects)
- [ ] Reads from `~/.claude/projects` (correct Claude Code session storage location)
- [ ] Writes results to `~/.claude/claudeception-results/` (not into the plugin directory)
- [ ] Session skipping logic: already-processed sessions (non-empty result file) are skipped without re-running
- [ ] --cleanup flag removes result files only (does not touch plugin files)
- [ ] No APM references in script body

### Plugin Metadata Assertions

plugin.json fields:

- [ ] name: "session-mining"
- [ ] description references both "mining" and "knowledge extraction" (not vague)
- [ ] version follows semver (e.g., "1.0.0")
- [ ] author.name is present
- [ ] keywords include "sessions", "claudeception", and "learning"

### Integration with claudeception

session-mining is a companion plugin to claudeception — it batch-drives the /claudeception skill.
Additional integration assertions:

- [ ] The command body correctly references `/claudeception` as the skill being invoked
- [ ] The script passes a prompt that invokes `/claudeception` (not a raw extraction prompt)
- [ ] The script uses `claude --resume <session_id> --no-session-persistence --print` (correct invocation pattern)
- [ ] The --exclude flag defaults to "I'm Ralph" to skip orchestration sessions (avoids noise)
- [ ] The --max-messages flag (default 100) prevents overloading large sessions

## Metrics Target

- pass@1: 100% for structure (deterministic)
- pass@3: > 90% for skill quality
