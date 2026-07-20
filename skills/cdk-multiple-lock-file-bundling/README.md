# cdk-multiple-lock-file-bundling

Fix AWS CDK bundling failures caused by multiple package lock files in the same
project. Use when: (1) CDK synth/deploy fails with "ValidationError: Multiple
package lock files found: pnpm-lock.yaml, package-lock.json", (2) NodejsFunction
or other bundled Lambda fails during cdk synth, (3) CI pipeline fails on test
stage with CDK bundling errors. Covers determining which lock file to keep based
on project's actual package manager.
