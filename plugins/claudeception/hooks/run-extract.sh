#!/bin/bash
# Claudeception - pipe skill JSON to create skills
# Usage: echo '{"skills": [...]}' | ./run-extract.sh

SCRIPT_DIR="$(dirname "$0")"
python3 "$SCRIPT_DIR/extract-skills.py"
