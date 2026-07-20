# Eval: cc-plugin-authoring

Plugin path: plugins/cc-plugin-authoring

## Capability Evals

[CAPABILITY EVAL: cc-plugin-authoring-structure]
Task: Verify plugin has all required structural files and fields
Success Criteria:

- [ ] .claude-plugin/plugin.json exists and is valid JSON
- [ ] plugin.json has name, description, and version fields
- [ ] At least one skills/ subdirectory with a SKILL.md file
- [ ] Each SKILL.md has YAML frontmatter with name and description
- [ ] No APM references (apm pack, apm marketplace, Agent Package Manager)
      Expected Output: All structural checks pass
      Grader: code-based (bash — see scripts/test-skills.sh)

[CAPABILITY EVAL: cc-plugin-authoring-skill-quality]
Task: Verify skill descriptions are specific and triggerable
Success Criteria:

- [ ] Description is specific (not generic boilerplate)
- [ ] Skill content is substantial (> 200 chars per SKILL.md)
- [ ] Triggering context is clear in the description
- [ ] No placeholder text (TODO, TBD) in production skills
      Expected Output: All skill quality checks pass
      Grader: manual (not implemented by scripts/test-skills.sh)

## Regression Evals

[REGRESSION EVAL: cc-plugin-authoring-claude-native]
Baseline: APM era (pre-migration)
Tests:

- plugin.json uses Claude-native format (not APM format): MUST PASS
- No APM CLI dependency for installation: MUST PASS
- Plugin installable by copying to ~/.claude/plugins/: MUST PASS
  Result: 3/3 must pass

## Plugin-Specific Checks

This plugin contains one skill: `cc-slash-command-argument-hint-yaml`.

### Skill: cc-slash-command-argument-hint-yaml

**What it does:** Documents the YAML parse trap that occurs when authoring
Claude Code slash command files (`commands/<name>.md`) with `argument-hint:`
values that use square-bracketed placeholder tokens (e.g.,
`argument-hint: [working-dir] [team-name]`). Explains that these are
interpreted as YAML flow sequences and cause `yaml.safe_load` to raise
`ScannerError` or `ConstructorError`. The fix is to quote the value as a
single string (e.g., `argument-hint: "<working-dir> <team-name>"`).

**Trigger context:** Precisely specified — any of: (1) authoring commands in a
CC plugin with multi-token bracketed `argument-hint` values; (2) a YAML parse
test raising `ScannerError` or `ConstructorError` on frontmatter; (3) a slash
command silently absent from `/help` after install; (4) a marketplace test
asserting `description` is present failing with a YAML error rather than an
assertion error.

**Plugin-specific assertions:**

- [ ] SKILL.md frontmatter `argument-hint` example values are themselves
      quoted strings — the skill must not demonstrate the broken pattern as
      the recommended approach (meta: the fix must be shown correctly)
- [ ] The skill's `description` frontmatter field enumerates at least two
      distinct trigger conditions (currently lists three explicitly)
- [ ] The skill body includes a verified solution section with a Python
      `yaml.safe_load` round-trip test snippet
- [ ] The skill body includes a "full command file (corrected)" example
      with properly quoted `argument-hint`
- [ ] Content length: SKILL.md body exceeds 3000 characters (it is a
      substantial reference, not a stub)
- [ ] The skill does not advertise itself as fixing a bug in Claude Code —
      it documents a YAML spec behavior, framed as a gotcha for authors

**Regression assertion (specific to this skill):**

- [ ] `argument-hint:` in the SKILL.md _body_ examples that show the
      broken pattern are inside fenced code blocks labeled as broken, and the
      fixed pattern uses angle-bracket placeholders inside a quoted string
- [ ] No unquoted `argument-hint: [...]` appears outside a "broken example"
      code block anywhere in the SKILL.md

## Metrics Target

- pass@1: 100% for structure (deterministic)
