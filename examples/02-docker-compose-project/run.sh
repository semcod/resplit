#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"
DAYS="${2:-30}"
OUTPUT="${3:-.rebuild}"

echo "rebuild walk (docker-compose): $REPO (last $DAYS days)"

# 1. Pipeline execution with Docker isolation
python3 -m rebuild walk "$REPO" \
  --days "$DAYS" \
  --deploy docker-compose \
  --health-url "http://localhost:8003/api/health" \
  --base-url "http://localhost:8003" \
  --output "$OUTPUT" \
  --screenshots

# 2. Intelligence Layer
echo -e "\n--- Intelligence: Architecture Graph ---"
python3 -m rebuild analyze services

echo -e "\n--- Intelligence: Refactor Plan ---"
python3 -m rebuild refactor plan "$REPO"

# 3. Visualization
echo -e "\n--- Generating dashboard ---"
python3 -m rebuild dashboard --results-dir "$OUTPUT" --repo "$REPO"

echo -e "\n--- Done ---"
echo "  Timeline:  $OUTPUT/index.html"
echo "  Dashboard: $OUTPUT/dashboard.html"
