---
name: cdk-multiple-lock-file-bundling
description: |
  Fix AWS CDK bundling failures caused by multiple package lock files in the same
  project. Use when: (1) CDK synth/deploy fails with "ValidationError: Multiple
  package lock files found: pnpm-lock.yaml, package-lock.json", (2) NodejsFunction
  or other bundled Lambda fails during cdk synth, (3) CI pipeline fails on test
  stage with CDK bundling errors. Covers determining which lock file to keep based
  on project's actual package manager.
author: Claude Code
version: 1.0.0
date: 2026-01-27
---

# CDK Multiple Lock File Bundling Error

## Problem

AWS CDK's NodejsFunction bundling fails when multiple package manager lock files
exist in the repository. The error message doesn't indicate which package manager
the project actually uses, requiring investigation.

## Context / Trigger Conditions

- Error: `ValidationError: Multiple package lock files found: pnpm-lock.yaml, package-lock.json`
- Occurs during `cdk synth`, `cdk deploy`, or test runs that synthesize CDK stacks
- CI pipeline fails on build/test stages with CDK bundling
- Recently merged code from another contributor who uses a different package manager

## Solution

### Step 1: Identify the Project's Package Manager

Check for these indicators (in order of reliability):

```bash
# 1. Check for packageManager field in root package.json
grep -o '"packageManager"[^,]*' package.json

# 2. Check which lock file is in .gitignore (the OTHER one should be used)
grep -E "package-lock|pnpm-lock|yarn.lock" .gitignore

# 3. Check CI configuration for which package manager is used
grep -E "npm |pnpm |yarn " .gitlab-ci.yml .github/workflows/*.yml 2>/dev/null

# 4. Check scripts in package.json for package manager hints
grep -E "npm run|pnpm |yarn " package.json
```

### Step 2: Remove the Incorrect Lock File

```bash
# If project uses npm (has package-lock.json as source of truth):
git rm pnpm-lock.yaml  # or yarn.lock

# If project uses pnpm (has pnpm-lock.yaml as source of truth):
git rm package-lock.json

# If project uses yarn (has yarn.lock as source of truth):
git rm package-lock.json pnpm-lock.yaml
```

### Step 3: Prevent Future Occurrences

Add the unwanted lock files to `.gitignore`:

```bash
# For npm projects, add:
echo "pnpm-lock.yaml" >> .gitignore
echo "yarn.lock" >> .gitignore

# For pnpm projects, add:
echo "package-lock.json" >> .gitignore
echo "yarn.lock" >> .gitignore
```

### Step 4: Commit and Verify

```bash
git add -A
git commit -m "fix: remove incorrect lock file for CDK bundling"
# Run CDK synth to verify
npx cdk synth
```

## Verification

After removing the incorrect lock file:

1. `npx cdk synth` completes without bundling errors
2. CI pipeline passes the test stage
3. Only one lock file exists in the repository

## Example

**Scenario:** CI fails with this error after merging a PR:
```
ValidationError: Multiple package lock files found: pnpm-lock.yaml, package-lock.json.
Please ensure that only one of these files is present.
```

**Investigation:**
```bash
$ grep packageManager package.json
# No output - not defined

$ grep -E "npm|pnpm" .gitlab-ci.yml
  - npm ci
  - npm run build

$ ls *.lock* package-lock.json
package-lock.json  pnpm-lock.yaml
```

**Resolution:** Project uses npm (based on CI config). Remove pnpm-lock.yaml:
```bash
git rm pnpm-lock.yaml
git commit -m "fix: remove pnpm-lock.yaml from npm project"
```

## Notes

- This commonly happens when contributors use different package managers locally
- pnpm automatically creates pnpm-lock.yaml when running any pnpm command
- Some IDEs auto-run package managers, creating unexpected lock files
- CDK's esbuild bundler is strict about having exactly one lock file
- The error occurs at synth time, not deployment time

## Related

- See also: cdk-temp-folder-disk-bloat (another CDK bundling issue)
