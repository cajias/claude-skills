#!/bin/bash
# Collect comprehensive git statistics for effort estimation
# Usage: ./collect_git_stats.sh [repository_path] [output_file]

set -e

REPO_PATH="${1:-.}"
OUTPUT_FILE="${2:-git_stats.txt}"

cd "$REPO_PATH"

# Verify git repository
if [ ! -d ".git" ]; then
  echo "Error: Not a git repository: $REPO_PATH"
  exit 1
fi

echo "=== GIT STATISTICS ===" > "$OUTPUT_FILE"
echo "Repository: $REPO_PATH" >> "$OUTPUT_FILE"
echo "Generated: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Total commits
echo "Total Commits:" >> "$OUTPUT_FILE"
TOTAL_COMMITS=$(git log --all --oneline | wc -l)
echo "$TOTAL_COMMITS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Contributors and commit counts
echo "Contributors:" >> "$OUTPUT_FILE"
git shortlog -sn --all >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Contributor percentages
echo "Contributor Percentages:" >> "$OUTPUT_FILE"
git shortlog -sn --all | awk -v total="$TOTAL_COMMITS" '{
  commits=$1
  name=substr($0, index($0,$2))
  percentage=(commits/total)*100
  printf "%s: %d commits (%.1f%%)\n", name, commits, percentage
}' >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Active development days
echo "Active Development Days:" >> "$OUTPUT_FILE"
ACTIVE_DAYS=$(git log --all --format="%ad" --date=short | sort -u | wc -l)
echo "$ACTIVE_DAYS days with commits" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# First and last commit dates
echo "Timeline:" >> "$OUTPUT_FILE"
FIRST_COMMIT=$(git log --all --reverse --format="%ad" --date=iso | head -1)
LAST_COMMIT=$(git log --all --format="%ad" --date=iso | head -1)
echo "First commit: $FIRST_COMMIT" >> "$OUTPUT_FILE"
echo "Last commit: $LAST_COMMIT" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Calculate duration
FIRST_DATE=$(git log --all --reverse --format="%ad" --date=short | head -1)
LAST_DATE=$(git log --all --format="%ad" --date=short | head -1)

# Platform-independent date calculation
if date --version >/dev/null 2>&1; then
  # GNU date (Linux)
  DAYS_ELAPSED=$(( ( $(date -d "$LAST_DATE" +%s) - $(date -d "$FIRST_DATE" +%s) ) / 86400 ))
else
  # BSD date (macOS)
  DAYS_ELAPSED=$(( ( $(date -jf "%Y-%m-%d" "$LAST_DATE" +%s) - $(date -jf "%Y-%m-%d" "$FIRST_DATE" +%s) ) / 86400 ))
fi

MONTHS_ELAPSED=$(echo "scale=1; $DAYS_ELAPSED / 30.0" | bc)
echo "Duration: $DAYS_ELAPSED days (~$MONTHS_ELAPSED months)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Commit distribution by month
echo "Commits by Month (top 10):" >> "$OUTPUT_FILE"
git log --all --format="%ad" --date=format:'%Y-%m' | sort | uniq -c | sort -rn | head -10 >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "Git statistics saved to: $OUTPUT_FILE"
