---
name: isengardcli-usage
description: This skill should be used when the user asks to "run AWS commands", "deploy to AWS", "get AWS credentials", "assume an AWS role", "run npm deploy", "run CDK commands", or needs to execute commands against an AWS account using Isengard authentication. Also use when encountering AWS credential errors or needing to switch between AWS accounts.
---

# Isengardcli Usage Guide

Isengardcli is Amazon's internal CLI tool for managing AWS account access through Isengard. It provides temporary AWS credentials for accessing AWS accounts.

## Critical: Account Selection Rules

**NEVER hardcode or assume account IDs.** Always use environment variables for account selection.

### Environment Variable Mapping

| Environment | Variable | Purpose |
|-------------|----------|---------|
| Development | `$DEV` | Personal/development account |
| Beta | `$BETA` | Beta testing environment |
| Gamma | `$GAMMA` | Pre-production staging |
| Production | `$PROD` or `$RELEASE` | Production environment |

### When to Ask for Clarification

**Always ask the user which environment** if:
- The user says "deploy" without specifying an environment
- The environment variable is not set (empty or undefined)
- The context is ambiguous (e.g., "run the tests" - dev or staging?)
- The user mentions an unfamiliar environment name

**Example clarification:**
> "Which environment should I deploy to? I have these configured:
> - DEV ($DEV) - Development
> - GAMMA ($GAMMA) - Staging
> - PROD ($PROD) - Production"

## Visual Warnings for Non-DEV Environments

When executing commands against non-DEV accounts, output colored warnings:

**For BETA/GAMMA (Yellow warning):**
```bash
echo -e "\033[1;33m⚠️  WARNING: Executing against GAMMA environment ($GAMMA)\033[0m"
```

**For PROD/RELEASE (Red warning):**
```bash
echo -e "\033[1;31m🚨 PRODUCTION ALERT: Executing against PROD environment ($PROD)\033[0m"
```

### Implementation Pattern

Before running any isengardcli command against non-DEV:

```bash
# For GAMMA/BETA
echo -e "\033[1;33m⚠️  WARNING: Running against GAMMA ($GAMMA)\033[0m"
isengardcli run --account "$GAMMA" --role Admin -- <command>

# For PROD
echo -e "\033[1;31m🚨 PRODUCTION: Running against PROD ($PROD)\033[0m"
isengardcli run --account "$PROD" --role Admin -- <command>
```

## The `run` Subcommand

The `run` subcommand executes any shell command with temporary AWS credentials injected into the environment.

### Basic Syntax

```bash
isengardcli run --account "$ENV_VAR" --role <ROLE_NAME> -- <command>
```

**Key components:**
- `--account`: Use environment variable like `"$DEV"`, `"$GAMMA"`, `"$PROD"`
- `--role`: IAM role to assume (typically `Admin` or `ReadOnly`)
- `--`: Separator between isengardcli args and the command to run
- `<command>`: Any shell command that needs AWS credentials

### Common Usage Patterns

**Deploy to development:**
```bash
isengardcli run --account "$DEV" --role Admin -- npm run deploy
```

**Deploy to gamma (with warning):**
```bash
echo -e "\033[1;33m⚠️  Deploying to GAMMA\033[0m"
isengardcli run --account "$GAMMA" --role Admin -- npm run deploy
```

**Run integration tests against dev:**
```bash
isengardcli run --account "$DEV" --role Admin -- npm run test:integration
```

## Checking Environment Variables

Before executing, verify the environment variable is set:

```bash
# Check if variable is set
if [ -z "$DEV" ]; then
  echo "Error: DEV environment variable not set"
  exit 1
fi
```

To see current values:
```bash
echo "DEV=$DEV"
echo "GAMMA=$GAMMA"
echo "PROD=$PROD"
```

## Other Useful Subcommands

### Get Credentials for Shell Export

```bash
eval $(isengardcli credentials --account "$DEV" --role Admin --shell sh)
```

### Open AWS Console

```bash
isengardcli webconsole --account "$DEV" --role Admin
```

### List Available Accounts

```bash
isengardcli ls --all              # List all accounts
isengardcli ls --output json      # JSON output for scripting
```

## Troubleshooting

### "You need to authenticate with Midway"

Midway session expired. Run:
```bash
mwinit
```

### Environment Variable Not Set

If `$DEV`, `$GAMMA`, or `$PROD` is empty:
1. Ask the user for the account ID
2. Suggest they add it to their shell profile:
   ```bash
   export DEV=123456789012
   export GAMMA=234567890123
   export PROD=345678901234
   ```

## Quick Reference

| Task | Command |
|------|---------|
| Run in DEV | `isengardcli run --account "$DEV" --role Admin -- cmd` |
| Run in GAMMA | `echo -e "\033[1;33m⚠️ GAMMA\033[0m" && isengardcli run --account "$GAMMA" --role Admin -- cmd` |
| Run in PROD | `echo -e "\033[1;31m🚨 PROD\033[0m" && isengardcli run --account "$PROD" --role Admin -- cmd` |
| Check env vars | `echo "DEV=$DEV GAMMA=$GAMMA PROD=$PROD"` |
| Refresh Midway | `mwinit` |

## Color Reference

| Environment | Color Code | Display |
|-------------|------------|---------|
| DEV | (none) | Normal output |
| BETA/GAMMA | `\033[1;33m` | Yellow/Orange |
| PROD/RELEASE | `\033[1;31m` | Red |
| Reset | `\033[0m` | Back to normal |
