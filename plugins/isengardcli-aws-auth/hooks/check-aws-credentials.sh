#!/bin/bash
# Hook: check-aws-credentials.sh
# Ensures AWS commands are wrapped with isengardcli for proper authentication
#
# Environment variables for accounts:
#   DEV   - Development/personal account
#   BETA  - Beta testing environment
#   GAMMA - Pre-production staging
#   PROD  - Production environment

# Read the tool input from stdin
INPUT=$(cat)

# Extract the command from the Bash tool input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# If no command found, allow (not a Bash command)
if [ -z "$COMMAND" ]; then
  exit 0
fi

# Patterns that require isengardcli
AWS_PATTERNS=(
  "npm run deploy"
  "npm run cdk"
  "npx cdk"
  "cdk deploy"
  "cdk synth"
  "cdk diff"
  "aws "
  "aws-cdk"
)

# Check if command contains any AWS patterns
NEEDS_ISENGARD=false
MATCHED_PATTERN=""
for pattern in "${AWS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -q "$pattern"; then
    NEEDS_ISENGARD=true
    MATCHED_PATTERN="$pattern"
    break
  fi
done

# If doesn't need isengard, allow
if [ "$NEEDS_ISENGARD" = false ]; then
  exit 0
fi

# Check if already wrapped with isengardcli
if echo "$COMMAND" | grep -q "isengardcli run"; then
  # Already wrapped - check which environment and warn if non-DEV

  # Extract account variable used
  if echo "$COMMAND" | grep -q '\$PROD\|"$PROD"\|${PROD}'; then
    echo -e "\033[1;31m🚨 PRODUCTION DEPLOYMENT DETECTED\033[0m" >&2
    echo -e "\033[1;31m   Proceeding with PROD account...\033[0m" >&2
  elif echo "$COMMAND" | grep -q '\$GAMMA\|"$GAMMA"\|${GAMMA}\|\$RELEASE\|"$RELEASE"\|${RELEASE}'; then
    echo -e "\033[1;33m⚠️  STAGING DEPLOYMENT DETECTED\033[0m" >&2
    echo -e "\033[1;33m   Proceeding with GAMMA account...\033[0m" >&2
  elif echo "$COMMAND" | grep -q '\$BETA\|"$BETA"\|${BETA}'; then
    echo -e "\033[1;33m⚠️  BETA DEPLOYMENT DETECTED\033[0m" >&2
    echo -e "\033[1;33m   Proceeding with BETA account...\033[0m" >&2
  fi

  exit 0
fi

# Command needs isengardcli but isn't wrapped - BLOCK
echo ""
echo -e "\033[1;31m╔══════════════════════════════════════════════════════════════════╗\033[0m"
echo -e "\033[1;31m║  🛑 AWS COMMAND BLOCKED - CREDENTIALS REQUIRED                   ║\033[0m"
echo -e "\033[1;31m╚══════════════════════════════════════════════════════════════════╝\033[0m"
echo ""
echo -e "\033[1mDetected AWS command:\033[0m $MATCHED_PATTERN"
echo ""
echo -e "\033[1mThis command requires AWS credentials via isengardcli.\033[0m"
echo ""
echo -e "\033[1;36mCorrect usage:\033[0m"
echo -e "  isengardcli run --account \"\$DEV\" --role Admin -- $COMMAND"
echo ""
echo -e "\033[1;33mEnvironment variables:\033[0m"
echo -e "  \$DEV   = ${DEV:-\033[1;31m(not set)\033[0m}"
echo -e "  \$BETA  = ${BETA:-\033[1;31m(not set)\033[0m}"
echo -e "  \$GAMMA = ${GAMMA:-\033[1;31m(not set)\033[0m}"
echo -e "  \$PROD  = ${PROD:-\033[1;31m(not set)\033[0m}"
echo ""
echo -e "\033[1mAsk the user which environment to use if unclear.\033[0m"
echo ""

# Exit with error to block the command
exit 1
