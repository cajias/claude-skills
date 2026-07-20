# Eval: dev

Plugin path: plugins/dev

## Capability Evals

[CAPABILITY EVAL: dev-structure]
Task: Verify plugin has all required structural files and fields
Success Criteria:

- [ ] .claude-plugin/plugin.json exists and is valid JSON
- [ ] plugin.json has name, description, and version fields
- [ ] At least one commands/ subdirectory entry with a .md file (plugin uses commands/, not skills/)
- [ ] Each command .md has YAML frontmatter with description field
- [ ] No APM references (apm pack, apm marketplace, Agent Package Manager)
      Expected Output: All structural checks pass
      Grader: code-based (bash — see scripts/test-skills.sh)

[CAPABILITY EVAL: dev-skill-quality]
Task: Verify skill descriptions are specific and triggerable
Success Criteria:

- [ ] Description is specific (not generic boilerplate)
- [ ] Component content is substantial (> 200 chars per command/agent .md)
- [ ] Triggering context is clear in the description
- [ ] No placeholder text (TODO, TBD) in production skills
      Expected Output: All skill quality checks pass
      Grader: manual (not implemented by scripts/test-skills.sh)

## Regression Evals

[REGRESSION EVAL: dev-claude-native]
Baseline: APM era (pre-migration)
Tests:

- plugin.json uses Claude-native format (not APM format): MUST PASS
- No APM CLI dependency for installation: MUST PASS
- Plugin installable by copying to ~/.claude/plugins/: MUST PASS
  Result: 3/3 must pass

## Plugin-Specific Checks

### Plugin Structure Notes

The `dev` plugin does NOT use a `skills/` directory. Instead it uses:

- `commands/` — slash command definitions (invokable via `/dev:<name>`)
- `agents/` — agent persona definitions
- `config/` — configuration schemas and defaults
- `examples/` — workflow documentation

This is a command-first plugin, not a skill-first plugin. Eval harnesses should
check `commands/*.md` rather than `skills/*/SKILL.md`.

### Commands

#### `review-readme` (`commands/review-readme.md`)

- Invoked as `/dev:review-readme [mode]`
- Modes: `generate`, `improve` (default), `evaluate`
- Frontmatter: has `description` and `argument-hint` fields — both must be present
- Content: 759 lines of detailed phase-by-phase workflow — well above 200-char threshold
- Implements a 7-phase iterative README improvement loop:
  1. Context gathering (codebase analysis via bash)
  2. Initial generation or improvement
  3. Quality evaluation (scored 0-100)
  4. Improvement planning (JSON priority buckets)
  5. Apply improvements (surgical edits)
  6. Re-evaluation loop
  7. Final report with score breakdown
- Quality scoring weights: essential_sections 40%, content_quality 30%, examples 20%, formatting 10%
- Default quality threshold: 85/100 (configurable)
- Default max iterations: 5 (configurable)
- No APM references present

#### Plugin-Specific Assertions for `review-readme`

- [ ] `commands/review-readme.md` YAML frontmatter has `description` field
- [ ] `commands/review-readme.md` YAML frontmatter has `argument-hint` field
- [ ] Content describes all three modes: generate, improve, evaluate
- [ ] Content references the config file path `config/readme-generator/default.config.json`
- [ ] Scoring formula present: `essential_sections * 0.4 + content_quality * 0.3 + examples * 0.2 + formatting * 0.1`
- [ ] Default score threshold (85) documented
- [ ] Default max_iterations (5) documented

### Agents

#### `orchestrator` (`agents/orchestrator.md`)

- Frontmatter: has `name`, `description`, `model`, `color` fields
- Model: sonnet
- Purpose: Plan-and-delegate orchestration for tasks involving 2+ files/steps
- No APM references present

#### Plugin-Specific Assertions for `orchestrator`

- [ ] `agents/orchestrator.md` YAML frontmatter has `name` field
- [ ] `agents/orchestrator.md` YAML frontmatter has `description` field
- [ ] `agents/orchestrator.md` YAML frontmatter has `model` field set to `sonnet`
- [ ] Content describes core orchestration loop (understand, plan, dispatch, review, simplify, report)

### Configuration

#### `config/readme-generator/default.config.json`

- [ ] File is valid JSON
- [ ] `max_iterations` present and equals 5
- [ ] `score_threshold` present and equals 85
- [ ] `require_sections` array contains at least `highlights`, `installation`, `usage`
- [ ] `evaluation_weights` sum to 1.0 (0.4 + 0.3 + 0.2 + 0.1)

#### `config/readme-generator/config.schema.json`

- [ ] File is valid JSON
- [ ] Schema covers all fields used in default.config.json

### Plugin-Level Assertions

- [ ] `plugin.json` name is `"dev"`
- [ ] `plugin.json` version is `"1.0.0"`
- [ ] Manual installation documented in README.md (copy to ~/.claude/plugins/dev/)
- [ ] README.md does NOT reference APM or Agent Package Manager for core installation
- [ ] No `skills/` directory exists (plugin uses commands/, not skills/)

## Metrics Target

- pass@1: 100% for structure (deterministic)
