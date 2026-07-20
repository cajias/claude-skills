#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.cajias.claudeception"
PLIST_DST="${HOME}/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "=== Claudeception Setup ==="

# Check prerequisites
echo "Checking prerequisites..."
which claude || { echo "ERROR: claude CLI not found in PATH"; exit 1; }
which python3 || { echo "ERROR: python3 not found in PATH"; exit 1; }

# Create directories
echo "Creating directories..."
mkdir -p ~/.claude/claudeception-metrics/processed

# Make cron scripts executable
echo "Making cron scripts executable..."
chmod +x "${SCRIPT_DIR}"/cron/*.sh "${SCRIPT_DIR}"/cron/*.py 2>/dev/null || true

# Install launchd plist
echo "Installing launchd plist..."
mkdir -p ~/Library/LaunchAgents
# launchd agents do not inherit the interactive shell environment, so capture
# CLAUDE_CODE_USE_BEDROCK at install time only if the installer already uses it.
BEDROCK_ENV=""
if [ -n "${CLAUDE_CODE_USE_BEDROCK:-}" ]; then
	BEDROCK_ENV=$'\t<key>EnvironmentVariables</key>\n\t<dict>\n\t\t<key>CLAUDE_CODE_USE_BEDROCK</key>\n\t\t<string>'"${CLAUDE_CODE_USE_BEDROCK}"$'</string>\n\t</dict>'
fi
cat > "${PLIST_DST}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>${PLIST_NAME}</string>

	<key>ProgramArguments</key>
	<array>
		<string>${SCRIPT_DIR}/cron/extract-from-archives.sh</string>
	</array>

	<key>StartCalendarInterval</key>
	<array>
		<dict><key>Hour</key><integer>12</integer></dict>
		<dict><key>Hour</key><integer>13</integer></dict>
		<dict><key>Hour</key><integer>14</integer></dict>
		<dict><key>Hour</key><integer>15</integer></dict>
		<dict><key>Hour</key><integer>16</integer></dict>
		<dict><key>Hour</key><integer>17</integer></dict>
		<dict><key>Hour</key><integer>18</integer></dict>
		<dict><key>Hour</key><integer>19</integer></dict>
		<dict><key>Hour</key><integer>20</integer></dict>
	</array>

${BEDROCK_ENV}

	<key>StandardOutPath</key>
	<string>${HOME}/.claude/claudeception-cron.log</string>

	<key>StandardErrorPath</key>
	<string>${HOME}/.claude/claudeception-cron.log</string>

	<key>WorkingDirectory</key>
	<string>${SCRIPT_DIR}/cron</string>

	<key>RunAtLoad</key>
	<false/>

	<key>Nice</key>
	<integer>10</integer>
</dict>
</plist>
EOF

# Reload plist
[ -x "${SCRIPT_DIR}/cron/extract-from-archives.sh" ] || { echo "ERROR: extract-from-archives.sh missing or not executable"; exit 1; }
launchctl unload "${PLIST_DST}" 2>/dev/null || true
launchctl load "${PLIST_DST}"

echo ""
echo "=== Setup complete! ==="
echo "Scheduled extraction runs hourly from 12:00-20:00."
echo ""
echo "Status:"
launchctl list | grep claudeception || echo "(not yet running)"
