#!/bin/bash
# Master script to collect all metrics for effort estimation
# Usage: ./collect_all_metrics.sh [repository_path]

set -e

REPO_PATH="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="effort_estimation_output"

echo "======================================"
echo "Software Effort Estimation Data Collection"
echo "======================================"
echo ""
echo "Repository: $REPO_PATH"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Step 1: Collect git statistics
echo "[1/3] Collecting git statistics..."
"$SCRIPT_DIR/collect_git_stats.sh" "$REPO_PATH" "$OUTPUT_DIR/git_stats.txt"
echo "✓ Git statistics saved"
echo ""

# Step 2: Collect code metrics
echo "[2/3] Collecting code metrics (this may take a few minutes)..."
"$SCRIPT_DIR/collect_code_metrics.sh" "$REPO_PATH" "$OUTPUT_DIR/metrics"
echo "✓ Code metrics saved"
echo ""

# Step 3: Collect infrastructure inventory
echo "[3/3] Collecting infrastructure inventory..."
"$SCRIPT_DIR/collect_infrastructure.sh" "$REPO_PATH" "$OUTPUT_DIR/infrastructure.txt"
echo "✓ Infrastructure inventory saved"
echo ""

echo "======================================"
echo "Data collection complete!"
echo "======================================"
echo ""
echo "Output files:"
echo "  - $OUTPUT_DIR/git_stats.txt"
echo "  - $OUTPUT_DIR/infrastructure.txt"
echo "  - $OUTPUT_DIR/metrics/cloc_full.json"
echo "  - $OUTPUT_DIR/metrics/cloc_summary.txt"
echo "  - $OUTPUT_DIR/metrics/production_code.txt"
echo "  - $OUTPUT_DIR/metrics/test_code.txt"
echo "  - $OUTPUT_DIR/metrics/summary.txt"
echo ""
echo "Next steps:"
echo "  1. Review the collected data"
echo "  2. Apply the five estimation models (see SKILL.md)"
echo "  3. Calculate productivity multipliers"
echo "  4. Generate the final report"
