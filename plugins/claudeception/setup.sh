#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.cajias.claudeception"
PLIST_SRC="${SCRIPT_DIR}/cron/${PLIST_NAME}.plist"
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
cp "${PLIST_SRC}" "${PLIST_DST}"

# Reload plist
launchctl unload "${PLIST_DST}" 2>/dev/null || true
launchctl load "${PLIST_DST}"

echo ""
echo "=== Setup complete! ==="
echo "Scheduled extraction runs hourly from 12:00-20:00."
echo ""
echo "Status:"
launchctl list | grep claudeception || echo "(not yet running)"
