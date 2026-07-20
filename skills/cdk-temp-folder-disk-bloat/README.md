# cdk-temp-folder-disk-bloat

Fix disk space exhaustion caused by AWS CDK temp folder accumulation on macOS. Use when:
(1) Disk is full or nearly full with no obvious cause,
(2) Running CDK synth, deploy, or tests (especially in TDD loops),
(3) /private/var/folders is consuming tens of gigabytes,
(4) cdk.out folders accumulating in temp directory,
(5) Standard cache cleanup (npm, go, homebrew) doesn't recover space,
(6) Running parallel subagents with CDK operations in Claude Code.
Covers diagnosis, cleanup, and prevention for CDK projects.
