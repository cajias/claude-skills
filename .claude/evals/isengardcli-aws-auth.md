# Eval: isengardcli-aws-auth

Plugin path: plugins/isengardcli-aws-auth

## Capability Evals

[CAPABILITY EVAL: isengardcli-aws-auth-structure]
Task: Verify plugin has all required structural files and fields
Success Criteria:

- [ ] .claude-plugin/plugin.json exists and is valid JSON
- [ ] plugin.json has name, description, and version fields
- [ ] At least one skills/ subdirectory with a SKILL.md file
- [ ] Each SKILL.md has YAML frontmatter with name and description
- [ ] No APM references (apm pack, apm marketplace, Agent Package Manager)
      Expected Output: All structural checks pass
      Grader: code-based (bash — see scripts/test-skills.sh)

[CAPABILITY EVAL: isengardcli-aws-auth-skill-quality]
Task: Verify skill descriptions are specific and triggerable
Success Criteria:

- [ ] Description is specific (not generic boilerplate)
- [ ] Skill content is substantial (> 200 chars per SKILL.md)
- [ ] Triggering context is clear in the description
- [ ] No placeholder text (TODO, TBD) in production skills
      Expected Output: All skill quality checks pass
      Grader: code-based (char count, grep)

## Regression Evals

[REGRESSION EVAL: isengardcli-aws-auth-claude-native]
Baseline: APM era (pre-migration)
Tests:

- plugin.json uses Claude-native format (not APM format): MUST PASS
- No APM CLI dependency for installation: MUST PASS
- Plugin installable by copying to ~/.claude/plugins/: MUST PASS
  Result: 3/3 must pass

## Plugin-Specific Checks

### Skills Inventory

#### isengardcli-usage

- Purpose: Guides use of Amazon's internal isengardcli tool to obtain temporary
  AWS credentials and execute commands against AWS accounts (DEV, BETA, GAMMA,
  PROD/RELEASE).
- Trigger phrases: "run AWS commands", "deploy to AWS", "get AWS credentials",
  "assume an AWS role", "run npm deploy", "run CDK commands", AWS credential
  errors, switching between AWS accounts.
- Key behaviors enforced:
  - Never hardcode or assume account IDs; always use environment variables ($DEV, $BETA, $GAMMA, $PROD, $RELEASE).
  - Always ask user for target environment when ambiguous or env var is unset.
  - Emit color-coded shell warnings before executing against non-DEV accounts: yellow for BETA/GAMMA, red for PROD/RELEASE.
  - Verify env vars are set before running isengardcli commands.
  - Handles Midway session expiry (directs user to run `mwinit`).

### Plugin-Specific Assertions

- [ ] isengardcli-usage SKILL.md exists at skills/isengardcli-usage/SKILL.md
- [ ] SKILL.md frontmatter `name` field equals "isengardcli-usage"
- [ ] SKILL.md frontmatter `description` includes trigger phrases for AWS deploy/credential scenarios
- [ ] SKILL.md body contains the `isengardcli run` command pattern with `--account` and `--role` flags
- [ ] SKILL.md body defines all four environment tiers: DEV, BETA/GAMMA, PROD/RELEASE
- [ ] SKILL.md body includes color-coded warning bash snippets (ANSI escape codes \033[1;33m and \033[1;31m)
- [ ] SKILL.md body includes Midway troubleshooting section (mwinit)
- [ ] SKILL.md body does NOT hardcode any AWS account IDs (no 12-digit numeric literals)
- [ ] plugin.json keywords include: aws, isengard, isengardcli, credentials, deploy, cdk, security

## Metrics Target

- pass@1: 100% for structure (deterministic)
- pass@3: > 90% for skill quality
