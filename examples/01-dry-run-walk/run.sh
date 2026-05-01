#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"
DAYS="${2:-30}"

echo "rebuild walk (dry-run): $REPO"

# 1. Pipeline execution
python3 -m rebuild walk "$REPO" --days "$DAYS" --dry-run --output .rebuild_dry

# 2. Analysis
echo -e "\n--- Analysis: Duplicates ---"
python3 -m rebuild analyze duplicates "$REPO"

echo -e "\n--- Analysis: Service Overlap ---"
python3 -m rebuild analyze services

echo -e "\n--- Done ---"
echo "  Report: .rebuild_dry/index.html"
