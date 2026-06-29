# Eval: md-to-pdf

Plugin path: plugins/md-to-pdf

## Capability Evals

[CAPABILITY EVAL: md-to-pdf-structure]
Task: Verify plugin has all required structural files and fields
Success Criteria:

- [ ] .claude-plugin/plugin.json exists and is valid JSON
- [ ] plugin.json has name, description, and version fields
- [ ] At least one commands/ subdirectory with a .md command file
- [ ] Each command .md has YAML frontmatter with name and description
- [ ] No APM references (apm pack, apm marketplace, Agent Package Manager)
      Expected Output: All structural checks pass
      Grader: code-based (bash — see scripts/test-skills.sh)

[CAPABILITY EVAL: md-to-pdf-skill-quality]
Task: Verify command descriptions are specific and triggerable
Success Criteria:

- [ ] Description is specific (not generic boilerplate)
- [ ] Command content is substantial (> 200 chars per command .md)
- [ ] Triggering context is clear in the description
- [ ] No placeholder text (TODO, TBD) in production commands
      Expected Output: All skill quality checks pass
      Grader: code-based (char count, grep)

## Regression Evals

[REGRESSION EVAL: md-to-pdf-claude-native]
Baseline: APM era (pre-migration)
Tests:

- plugin.json uses Claude-native format (not APM format): MUST PASS
- No APM CLI dependency for installation: MUST PASS
- Plugin installable by copying to ~/.claude/plugins/: MUST PASS
  Result: 3/3 must pass

## Plugin-Specific Checks

This plugin contains one command: `md-to-pdf`, defined in `commands/md-to-pdf.md`.

### Command: md-to-pdf

**What it does:** Converts a directory of markdown files into a single PDF document. It
discovers all `.md` files (excluding README.md, CHANGELOG.md, LICENSE.md, PLAN.md),
sorts them alphabetically (numeric prefix convention supported), strips YAML frontmatter,
fetches Mermaid diagrams from the mermaid.ink API and embeds them as PNG images, generates
HTML via pandoc, then converts to PDF via weasyprint. The user is prompted for an output
path before conversion begins.

**Trigger context:** Invoked directly as a slash command `/md-to-pdf <directory-path>`.
The `argument-hint` field is `"<directory-path>"`, making the required argument explicit.
Also triggered when a user wants to export a playbook, runbook, or documentation tree to
a distributable PDF with rendered diagrams.

**Dependencies:** pandoc (external, must be pre-installed via `brew install pandoc`);
weasyprint (auto-installed via `pipx` if missing); internet access to mermaid.ink for
diagram rendering.

**Plugin-specific assertions:**

- [ ] `commands/md-to-pdf.md` frontmatter includes `allowed-tools` listing at minimum
      Bash, Read, Write, and AskUserQuestion
- [ ] `argument-hint` in the command frontmatter is a quoted string
      (`"<directory-path>"`), not an unquoted bracketed token (YAML flow sequence trap)
- [ ] The command workflow section documents all five steps: validate input, ask output
      location, check dependencies, run conversion, open result
- [ ] The script path reference uses `$CLAUDE_PLUGIN_ROOT/scripts/md-to-pdf.py` (not a
      hardcoded absolute path)
- [ ] `scripts/md-to-pdf.py` exists alongside the command file
- [ ] The command documents graceful fallback for mermaid.ink failures (keeps original
      code blocks rather than aborting)
- [ ] Excluded files list (README.md, CHANGELOG.md, LICENSE.md, PLAN.md) is documented
      either in the command or in the README
- [ ] Content length: `commands/md-to-pdf.md` body exceeds 1500 characters (it is a
      substantive workflow guide, not a stub)

**Regression assertions (specific to this command):**

- [ ] No hardcoded user home paths or absolute paths appear outside code-block examples
- [ ] The `argument-hint` value does not use unquoted square brackets (would cause YAML
      parse failure and silently drop the command from `/help`)
- [ ] weasyprint installation is attempted non-destructively (`pipx install`, not `pip
install --system` or `sudo pip install`)

## Metrics Target

- pass@1: 100% for structure (deterministic)
- pass@3: > 90% for skill quality
