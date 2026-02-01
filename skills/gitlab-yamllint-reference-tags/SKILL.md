---
name: gitlab-yamllint-reference-tags
description: |
  Fix yamllint failures on GitLab CI `!reference` tags. Use when:
  (1) yamllint fails with "unknown tag" on `.gitlab-ci.yml`,
  (2) Pre-commit hooks reject valid GitLab CI syntax,
  (3) CI lint job fails but GitLab accepts the YAML,
  (4) Error mentions `!reference` or custom YAML tags.
  Covers yamllint configuration for GitLab-specific tags.
author: Claude Code
version: 1.0.0
date: 2026-01-26
tags: [gitlab, yamllint, ci-cd, yaml]
---

# GitLab yamllint !reference Tag Fix

## Problem

yamllint rejects GitLab CI files containing `!reference` tags with errors like:

```text
.gitlab-ci.yml:42:5: error: unknown tag '!reference'
```

GitLab's `!reference` tag is valid GitLab CI syntax for reusing configuration, but yamllint doesn't recognize it by default.

## Context / Trigger Conditions

Use this skill when:

- yamllint fails on `.gitlab-ci.yml` with "unknown tag" errors
- Pre-commit hooks reject valid GitLab CI YAML
- CI lint jobs fail but GitLab's own validator accepts the file
- You see `!reference` in error messages

## Solution

### 1. Create or Update `.yamllint.yaml`

Add custom tag configuration to allow GitLab-specific tags:

```yaml
# .yamllint.yaml
extends: default

rules:
  line-length:
    max: 120
  truthy:
    allowed-values: ["true", "false", "yes", "no"]

# Allow GitLab CI custom tags
yaml-files:
  - "*.yaml"
  - "*.yml"
  - ".yamllint"

ignore: |
  node_modules/
  .git/

# Custom tags configuration
custom-tags:
  - "!reference"
  - "!reference sequence"
```

### 2. Alternative: Inline Comment Disable

For one-off cases, disable the rule inline:

```yaml
# yamllint disable rule:custom-tags
script:
  - !reference [.common, script]
# yamllint enable rule:custom-tags
```

### 3. Pre-commit Hook Configuration

If using pre-commit, ensure yamllint uses your config:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        args: ["-c", ".yamllint.yaml"]
```

## Verification

After applying the fix:

```bash
yamllint -c .yamllint.yaml .gitlab-ci.yml
```

Should pass without "unknown tag" errors.

## Example

**Before** (fails):

```yaml
# .gitlab-ci.yml
.common:
  script:
    - echo "shared script"

job:
  script:
    - !reference [.common, script] # yamllint error here
```

**After** (with `.yamllint.yaml` config): Same file passes.

## Notes

- GitLab supports several custom tags: `!reference`, `!include`, etc.
- The `sequence` variant (`!reference sequence`) may need separate allowlisting
- Some older yamllint versions use different syntax for custom tags
- Consider adding all GitLab custom tags you use to the allow list

## References

- [GitLab CI !reference docs](https://docs.gitlab.com/ee/ci/yaml/#reference-tags)
- [yamllint custom-tags rule](https://yamllint.readthedocs.io/en/stable/rules.html)
