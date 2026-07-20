# Eval: claudeception

Plugin path: plugins/claudeception

## Capability Evals

[CAPABILITY EVAL: claudeception-structure]
Task: Verify plugin has all required structural files and fields
Success Criteria:

- [ ] .claude-plugin/plugin.json exists and is valid JSON
- [ ] plugin.json has name, description, and version fields
- [ ] At least one SKILL.md file exists (skills/ or examples/)
- [ ] Each SKILL.md has YAML frontmatter with name and description
- [ ] No APM references (apm pack, apm marketplace, Agent Package Manager)
      Expected Output: All structural checks pass
      Grader: code-based (bash — see scripts/test-skills.sh)

[CAPABILITY EVAL: claudeception-skill-quality]
Task: Verify skill descriptions are specific and triggerable
Success Criteria:

- [ ] Description is specific (not generic boilerplate)
- [ ] Skill content is substantial (> 200 chars per SKILL.md)
- [ ] Triggering context is clear in the description
- [ ] No placeholder text (TODO, TBD) in production skills
      Expected Output: All skill quality checks pass
      Grader: manual (not implemented by scripts/test-skills.sh)

## Regression Evals

[REGRESSION EVAL: claudeception-claude-native]
Baseline: APM era (pre-migration)
Tests:

- plugin.json uses Claude-native format (not APM format): MUST PASS
- No APM CLI dependency for installation: MUST PASS
- Plugin installable by copying to ~/.claude/plugins/: MUST PASS
  Result: 3/3 must pass

## Plugin-Specific Checks

### Hook Architecture

claudeception is a multi-hook plugin with four active hooks:

| Hook             | Script                      | Timeout | Purpose                                                               |
| ---------------- | --------------------------- | ------- | --------------------------------------------------------------------- |
| PostToolUse      | hooks/signal_accumulator.py | 5s      | Accumulates signals from tool use events for skill extraction scoring |
| UserPromptSubmit | hooks/knowledge_handler.py  | 5s      | Detects teaching/correction patterns in user prompts                  |
| SessionEnd       | hooks/extraction_engine.py  | 30s     | Extracts and saves skills at session end                              |
| PreCompact       | hooks/extraction_engine.py  | 30s     | Extracts skills before context compaction                             |

Assertions:

- [ ] All four hook scripts exist under hooks/
- [ ] Hooks reference ${CLAUDE_PLUGIN_ROOT} (not hardcoded paths)
- [ ] SessionEnd and PreCompact share the same extraction_engine.py (correct deduplication)
- [ ] PostToolUse and UserPromptSubmit have short timeouts (≤5s) to avoid blocking

### Skills Inventory

The plugin ships with one skill at skills/claudeception/SKILL.md and three example skills under examples/:

| Skill name                         | Location                                             | Purpose                                                                             |
| ---------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------- |
| claudeception                      | skills/claudeception/SKILL.md                        | Meta-skill: how to extract and create reusable skills from sessions                 |
| nextjs-server-side-error-debugging | examples/nextjs-server-side-error-debugging/SKILL.md | Debug getServerSideProps/getStaticProps silent failures by checking terminal logs   |
| prisma-connection-pool-exhaustion  | examples/prisma-connection-pool-exhaustion/SKILL.md  | Fix Prisma P2024/too-many-connections errors in serverless environments             |
| typescript-circular-dependency     | examples/typescript-circular-dependency/SKILL.md     | Detect and resolve circular import dependencies causing undefined values at runtime |

Assertions for each skill:

- [ ] YAML frontmatter present with name, description, author, version fields
- [ ] Description contains specific error messages or trigger conditions (not vague)
- [ ] Body has at least a Problem, Solution, and Verification section
- [ ] No APM references or stale installation paths in skill body

### Meta-skill Behavior (claudeception SKILL.md)

The skill describes the skill extraction workflow itself. Additional assertions:

- [ ] Describes command trigger (/claudeception) and natural language triggers ("save this as a skill")
- [ ] Includes a quality gate checklist (non-obvious, investigation required, not just docs)
- [ ] Skill template embedded in the skill body is syntactically valid YAML frontmatter
- [ ] Script paths in the skill body use ${CLAUDE_PLUGIN_ROOT} (no hardcoded home paths)

### Supporting Infrastructure

- [ ] hooks/duplicate_detector.py exists (TF-IDF deduplication logic)
- [ ] hooks/taxonomy_classifier.py exists (user/project skill taxonomy)
- [ ] hooks/correction_detector.py and hooks/knowledge_detector.py exist (unified knowledge detection)
- [ ] observability/simple-stats.sh exists and is executable
- [ ] pyproject.toml present (uv-managed Python dependencies)
- [ ] setup.sh present for initial installation

## Metrics Target

- pass@1: 100% for structure (deterministic)
