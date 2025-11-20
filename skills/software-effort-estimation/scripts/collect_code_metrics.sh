#!/bin/bash
# Collect code metrics using cloc
# Usage: ./collect_code_metrics.sh [repository_path] [output_dir]

set -e

REPO_PATH="${1:-.}"
OUTPUT_DIR="${2:-metrics}"

cd "$REPO_PATH"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if cloc is installed
if ! command -v cloc &> /dev/null; then
    echo "Error: cloc is not installed"
    echo "Install with: brew install cloc (macOS) or apt-get install cloc (Linux)"
    exit 1
fi

echo "Collecting code metrics from: $REPO_PATH"
echo "Output directory: $OUTPUT_DIR"

# Full codebase analysis
echo "Running full codebase analysis..."
cloc . \
  --exclude-dir=node_modules,dist,build,cdk.out,vendor,target,.git,.next,out,coverage \
  --json \
  --report-file="$OUTPUT_DIR/cloc_full.json"

cloc . \
  --exclude-dir=node_modules,dist,build,cdk.out,vendor,target,.git,.next,out,coverage \
  > "$OUTPUT_DIR/cloc_summary.txt"

# Production code only (exclude tests)
echo "Analyzing production code..."
cloc . \
  --exclude-dir=node_modules,dist,build,cdk.out,vendor,target,.git,.next,out,coverage \
  --not-match-f='test|spec|__tests__|mock|.test.|.spec.' \
  > "$OUTPUT_DIR/production_code.txt"

# Test code only
echo "Analyzing test code..."
cloc . \
  --exclude-dir=node_modules,dist,build,cdk.out,vendor,target,.git,.next,out,coverage \
  --match-f='test|spec|__tests__|mock|.test.|.spec.' \
  > "$OUTPUT_DIR/test_code.txt"

# Extract summary statistics
echo "" > "$OUTPUT_DIR/summary.txt"
echo "=== CODE METRICS SUMMARY ===" >> "$OUTPUT_DIR/summary.txt"
echo "Generated: $(date)" >> "$OUTPUT_DIR/summary.txt"
echo "" >> "$OUTPUT_DIR/summary.txt"

# Total lines
TOTAL_LINES=$(grep "SUM:" "$OUTPUT_DIR/cloc_summary.txt" | awk '{print $5}')
echo "Total code lines: $TOTAL_LINES" >> "$OUTPUT_DIR/summary.txt"

# Production lines
PROD_LINES=$(grep "SUM:" "$OUTPUT_DIR/production_code.txt" 2>/dev/null | awk '{print $5}')
echo "Production code lines: ${PROD_LINES:-0}" >> "$OUTPUT_DIR/summary.txt"

# Test lines
TEST_LINES=$(grep "SUM:" "$OUTPUT_DIR/test_code.txt" 2>/dev/null | awk '{print $5}')
echo "Test code lines: ${TEST_LINES:-0}" >> "$OUTPUT_DIR/summary.txt"

echo ""
echo "Code metrics saved to: $OUTPUT_DIR/"
echo "  - cloc_full.json: Complete analysis in JSON format"
echo "  - cloc_summary.txt: Human-readable summary"
echo "  - production_code.txt: Production code analysis"
echo "  - test_code.txt: Test code analysis"
echo "  - summary.txt: Quick summary statistics"
