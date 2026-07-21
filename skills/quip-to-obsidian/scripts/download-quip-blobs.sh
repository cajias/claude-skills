#!/bin/bash
# Download all Quip blobs for Obsidian migration
#
# Environment variables:
#   QUIP_API_TOKEN - Required. Quip API token from https://quip-amazon.com/dev/token
#   OUTPUT_DIR     - Required. Directory to save downloaded images
#   BLOB_LIST      - Required. File containing blob paths (one per line)
#   QUIP_API_BASE  - Optional. API base URL (default: https://platform.quip-amazon.com)
#
# Usage:
#   export QUIP_API_TOKEN="your-token"
#   export OUTPUT_DIR="/path/to/attachments"
#   export BLOB_LIST="/tmp/quip-blobs.txt"
#   bash download-quip-blobs.sh

set -euo pipefail

# Configuration
QUIP_TOKEN="${QUIP_API_TOKEN:-}"
OUTPUT_DIR="${OUTPUT_DIR:-}"
BLOB_LIST="${BLOB_LIST:-}"
QUIP_API_BASE="${QUIP_API_BASE:-https://platform.quip-amazon.com}"

# Validation
if [[ -z "$QUIP_TOKEN" ]]; then
    echo "Error: QUIP_API_TOKEN environment variable is required"
    echo "Get your token from: https://quip-amazon.com/dev/token"
    exit 1
fi

if [[ -z "$OUTPUT_DIR" ]]; then
    echo "Error: OUTPUT_DIR environment variable is required"
    exit 1
fi

if [[ -z "$BLOB_LIST" ]] || [[ ! -f "$BLOB_LIST" ]]; then
    echo "Error: BLOB_LIST must point to a valid file"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Counters
downloaded=0
failed=0
total=$(wc -l < "$BLOB_LIST" | tr -d ' ')

echo "=== Quip Blob Downloader ==="
echo "Output directory: $OUTPUT_DIR"
echo "Blob list: $BLOB_LIST"
echo "Total blobs to download: $total"
echo ""

while IFS= read -r blob_path; do
    # Skip empty lines
    [[ -z "$blob_path" ]] && continue

    # Extract thread_id and blob_id from path like /blob/YPB9AAFeXJF/-YJg5mj0jDMMpAoTT-X06w
    thread_id=$(echo "$blob_path" | cut -d'/' -f3)
    blob_id=$(echo "$blob_path" | cut -d'/' -f4)

    # Skip if extraction failed
    if [[ -z "$thread_id" ]] || [[ -z "$blob_id" ]]; then
        echo "[SKIP] Invalid blob path: $blob_path"
        failed=$((failed + 1))
        continue
    fi

    # Create filename from thread_id and blob_id
    filename="${thread_id}_${blob_id}"

    # Download the blob
    http_code=$(curl -s -o "$OUTPUT_DIR/${filename}.tmp" -w "%{http_code}" \
        -H "Authorization: Bearer $QUIP_TOKEN" \
        "${QUIP_API_BASE}/1/blob/${thread_id}/${blob_id}" 2>/dev/null || echo "000")

    if [[ "$http_code" == "200" ]]; then
        # Detect file type and rename with correct extension
        file_type=$(file -b --mime-type "$OUTPUT_DIR/${filename}.tmp" 2>/dev/null || echo "application/octet-stream")
        case "$file_type" in
            image/png) ext="png" ;;
            image/jpeg) ext="jpg" ;;
            image/gif) ext="gif" ;;
            image/svg+xml) ext="svg" ;;
            image/webp) ext="webp" ;;
            application/pdf) ext="pdf" ;;
            *) ext="bin" ;;
        esac
        mv "$OUTPUT_DIR/${filename}.tmp" "$OUTPUT_DIR/${filename}.${ext}"
        downloaded=$((downloaded + 1))
        echo "[$downloaded/$total] Downloaded: ${filename}.${ext}"
    else
        rm -f "$OUTPUT_DIR/${filename}.tmp"
        failed=$((failed + 1))
        echo "[FAILED] $blob_path (HTTP $http_code)"
    fi
done < "$BLOB_LIST"

echo ""
echo "=== Download Complete ==="
echo "Downloaded: $downloaded"
echo "Failed: $failed"
echo "Total: $total"

if [[ $failed -gt 0 ]]; then
    echo ""
    echo "Note: Some blobs failed to download. They may be deleted or inaccessible."
fi
