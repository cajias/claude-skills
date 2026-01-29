---
name: gitlab-ci-debugging
description: |
  Debug common GitLab CI/CD pipeline failures. Use when:
  (1) Pipeline fails with unclear error messages,
  (2) Jobs fail with AWS credential or permission errors,
  (3) Node/npm jobs fail in CI but work locally,
  (4) Format/lint checks fail in pipeline,
  (5) MR pipeline behaves differently than branch pipeline.
  Covers common failure patterns and diagnostic approaches.
author: Claude Code
version: 1.0.0
date: 2026-01-26
tags: [gitlab, ci-cd, debugging, pipelines]
---

# GitLab CI/CD Pipeline Debugging

## Problem

GitLab CI pipelines fail with various error patterns that aren't always obvious to diagnose. This skill covers common failure modes and their solutions.

## Context / Trigger Conditions

Use this skill when:
- Pipeline jobs fail with unclear errors
- AWS credential errors (`target_role_access_denied`)
- Jobs work locally but fail in CI
- Lint/format checks fail unexpectedly
- MR pipelines behave differently than branch pipelines

## Solution

### 1. AWS Credential Errors

**Symptom**: `AWS Credential Vendor -- Error -- {"error":"target_role_access_denied"}`

**Causes & Fixes**:

| Cause | Fix |
|-------|-----|
| Missing CI variable | Set `$BEDROCK_ROLE_ARN` or required role ARN in CI/CD settings |
| Wrong IAM trust policy | Update trust policy to allow GitLab OIDC provider |
| Protected variable on unprotected branch | Make variable available to all branches or protect the branch |
| Different image missing AWS CLI | Use image with AWS CLI pre-installed |

**Diagnostic**:
```bash
glab ci view --job JOB_NAME  # View job logs
```

### 2. Node/npm Job Failures

**Symptom**: Node jobs fail with missing packages or wrong version

**Common Issues**:

```yaml
# Problem: Using wrong Node version
job:
  image: node:18  # May need node:20 for newer features

# Fix: Specify correct version
job:
  image: node:20

# Problem: npm ci fails
# Fix: Ensure package-lock.json is committed
```

**Node version check**:
```yaml
before_script:
  - node --version
  - npm --version
```

### 3. Lint/Format Check Failures

**Symptom**: format_check or lint jobs fail

**Debugging steps**:
```bash
# Run locally first
npm run lint
npm run format:check

# Check what files are different
git diff

# Auto-fix and commit
npm run format
git add -A && git commit -m "fix: format"
```

**Common `.gitlab-ci.yml` pattern**:
```yaml
format_check:
  script:
    - npm ci
    - npm run format:check
  allow_failure: true  # Won't block pipeline
```

### 4. MR vs Branch Pipeline Differences

**Symptom**: Pipeline works on branch but fails on MR

**Causes**:
- MR pipelines use `CI_MERGE_REQUEST_*` variables
- Different rules apply to MR pipelines
- Protected variables may not be available

**Debug**:
```yaml
debug_job:
  script:
    - echo "CI_PIPELINE_SOURCE=$CI_PIPELINE_SOURCE"
    - echo "CI_MERGE_REQUEST_IID=$CI_MERGE_REQUEST_IID"
    - env | grep CI_ | sort
```

### 5. YAML Validation Errors

**Symptom**: Pipeline fails to start with YAML error

**Diagnostic**:
```bash
# Validate locally
glab ci lint

# Check for common issues:
# - Duplicate keys
# - Invalid !reference syntax
# - Incorrect indentation
```

**Fix duplicate keys** (common with `rules:`):
```yaml
# Wrong - duplicate rules key
job:
  rules:
    - if: $CI_COMMIT_BRANCH
  rules:  # Duplicate!
    - if: $CI_MERGE_REQUEST_IID

# Right - single rules with multiple conditions
job:
  rules:
    - if: $CI_COMMIT_BRANCH
    - if: $CI_MERGE_REQUEST_IID
```

### 6. Quick Diagnostic Commands

```bash
# View pipeline status
glab ci status

# View specific job logs
glab ci view --job JOB_NAME

# Retry failed job
glab ci retry --job JOB_NAME

# View MR pipelines
glab mr view MR_NUMBER

# Check CI variables (masked values hidden)
glab variable list
```

## Verification

Pipeline debugging is working when you can:
1. Identify the failing job and error message
2. Reproduce the issue (locally or understand why it's CI-specific)
3. Apply a fix and verify the pipeline passes

## Example

**Failed Pipeline Investigation**:
```bash
# 1. Check which job failed
glab ci status
# Output: ❌ format_check failed

# 2. View job logs
glab ci view --job format_check
# Shows: "prettier found 3 files with formatting issues"

# 3. Fix locally
npm run format

# 4. Commit and push
git add -A && git commit -m "fix: format" && git push
```

## Notes

- Use `allow_failure: true` for non-blocking checks during development
- Protected CI variables only available on protected branches
- MR pipelines have different variable scope than branch pipelines
- Cache npm dependencies to speed up pipelines:
  ```yaml
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
  ```

## References

- [GitLab CI/CD Variables](https://docs.gitlab.com/ee/ci/variables/)
- [GitLab CI/CD Pipeline Architecture](https://docs.gitlab.com/ee/ci/pipelines/)
- [Troubleshooting GitLab CI/CD](https://docs.gitlab.com/ee/ci/troubleshooting.html)
