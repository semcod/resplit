#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"
DAYS="${2:-30}"
OUTPUT="${3:-.rebuild}"

echo "rebuild walk (docker-compose): $REPO (last $DAYS days)"

rebuild walk "$REPO" \
  --days "$DAYS" \
  --deploy docker-compose \
  --health-url "http://localhost:8003/api/health" \
  --base-url "http://localhost:8003" \
  --output "$OUTPUT" \
  --screenshots

echo ""
echo "Generating dashboard..."
rebuild dashboard --results-dir "$OUTPUT" --repo "$REPO"

echo ""
echo "Done."
echo "  Timeline:  $OUTPUT/index.html"
echo "  Dashboard: $OUTPUT/dashboard.html"
