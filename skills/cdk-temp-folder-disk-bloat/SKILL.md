---
name: cdk-temp-folder-disk-bloat
description: |
  Fix disk space exhaustion caused by AWS CDK temp folder accumulation on macOS. Use when:
  (1) Disk is full or nearly full with no obvious cause,
  (2) Running CDK synth, deploy, or tests (especially in TDD loops),
  (3) /private/var/folders is consuming tens of gigabytes,
  (4) cdk.out folders accumulating in temp directory,
  (5) Standard cache cleanup (npm, go, homebrew) doesn't recover space,
  (6) Running parallel subagents with CDK operations in Claude Code.
  Covers diagnosis, cleanup, and prevention for CDK projects.
author: Claude Code
version: 1.1.0
date: 2025-01-26
---

# AWS CDK Temp Folder Disk Bloat

## Problem

AWS CDK creates temporary cdk.out folders during synth/deploy/test operations that are never
automatically cleaned up. On macOS, these accumulate in /private/var/folders/XX/XXXX/T/
(the per-user temp directory) and can consume tens or hundreds of gigabytes of disk space.

This is especially severe when:
- Running CDK tests repeatedly (TDD workflows, CI loops)
- Using cdk watch or similar continuous deployment tools
- Multiple CDK projects are active
- Tests spawn multiple parallel CDK synth operations

## Context / Trigger Conditions

Symptoms:
- Disk suddenly full or nearly full (100% usage)
- Standard cleanup commands (npm cache clean, go clean, brew cleanup) don't help
- df -h shows high usage but home directory seems normal
- CDK synth/deploy/tests become slow or fail with disk errors

Detection commands:
1. Count CDK temp folders: ls /private/var/folders/*/*/T/cdk.out* 2>/dev/null | wc -l
2. Check total size: du -sh /private/var/folders/*/*/T/cdk.out* 2>/dev/null | head -20

If you see hundreds or thousands of cdk.out folders, this is your problem.

## Solution

### Step 1: Stop Any Active CDK Processes

First, stop whatever is creating new folders:

Find CDK-related processes:
  ps aux | grep -E "jest|cdk|esbuild" | grep -v grep

Kill jest/test processes that run CDK:
  pkill -9 -f "jest-worker"
  pkill -9 -f "npm test"

If using Claude Code with TDD/ralph-loop, send Ctrl+C to the running session.

Important: If processes keep respawning, find and kill the parent orchestrator:
  pgrep -f "jest.*passWithNoTests" | xargs ps -o pid,ppid,command -p
Then kill the parent PID.

### Step 2: Clean Up Existing Folders

Find your temp folder path:
  echo $TMPDIR
Usually: /var/folders/XX/XXXXXXXXX/T/

Remove all CDK temp folders:
  rm -rf /private/var/folders/*/*/T/cdk.out*

This may take several minutes if there are thousands of folders.

### Step 3: Verify Recovery

Run: df -h /
Should show significantly more free space.

## Prevention

### Claude Code Subagent Patterns (CRITICAL)

When using Claude Code with parallel subagents (Task tool), NEVER run CDK operations in parallel:

**FORBIDDEN (will exhaust disk in minutes):**
```
# BAD - each subagent creates separate cdk.out folders
[
  Task(general-purpose: "Run npm test") ||
  Task(general-purpose: "Run npm run build") ||
  Task(general-purpose: "Run cdk synth -c dataPlane=fargate") ||
  Task(general-purpose: "Run cdk synth -c dataPlane=eks")
]
```

**REQUIRED (sequential execution):**
```
# GOOD - one CDK operation at a time
1. npm run build
2. npm run lint
3. npm test
4. cdk synth (one context at a time)
```

**In TDD plans and scratchpads, add this warning:**
```markdown
## CRITICAL: CDK Disk Bloat Prevention
⚠️ DO NOT run CDK operations in parallel!
Run validation commands SEQUENTIALLY, not in parallel.
```

### Option 1: Set a Consistent Output Directory

In your CDK app, set a consistent output directory that gets cleaned:

  const app = new cdk.App({
    outdir: 'cdk.out',  // Use project-relative path, not temp
  });

### Option 2: Add Clean Script to package.json

  "scripts": {
    "clean": "rm -rf cdk.out node_modules/.cache",
    "pretest": "rm -rf cdk.out"
  }

### Option 3: Periodic Cleanup Cron

Add to crontab (crontab -e) - clean CDK temp folders daily at 3am:
  0 3 * * * rm -rf /private/var/folders/*/*/T/cdk.out* 2>/dev/null

## Verification

After cleanup:
1. Run df -h / - should show recovered space
2. Count remaining folders - should be 0 or very low
3. Run a CDK test/synth and verify behavior

## Example

Scenario: Disk shows 100% full, 552MB free on a 461GB drive

Investigation showed standard caches only 20GB, but temp folders had 1000+ cdk.out
folders at 3.1GB each consuming 60+ GB.

Resolution:
1. Stopped the TDD loop creating folders (pkill jest-worker)
2. Cleaned up (rm -rf /private/var/folders/*/*/T/cdk.out*)
3. Result: 84GB recovered

## Notes

- The /private/var/folders directory is macOS per-user temp/cache location
- Standard TMPDIR points here, but tools often use it without cleanup
- CDK bundling (esbuild) creates additional temp files within each cdk.out folder
- Running multiple parallel CDK operations multiplies the problem
- This issue is more severe in monorepos with multiple CDK packages
- The rm process may run for several minutes with thousands of folders

## Related Issues

- Docker: ~/Library/Containers/com.docker.docker can also accumulate space
- Other temp folder bloat: Jest cache, webpack cache
- Check for orphaned node_modules in git worktrees

## See Also

- **cdk-test-optimization**: Speed up slow CDK tests by using beforeAll instead of beforeEach

## References

- AWS CDK CLI docs: https://docs.aws.amazon.com/cdk/v2/guide/cli.html
- macOS temp folders: /private/var/folders is real path, /var/folders is symlink
