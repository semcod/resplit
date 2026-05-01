#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"
DAYS="${2:-30}"
OUTPUT="${3:-.rebuild}"

echo "rebuild dry-run walk: $REPO (last $DAYS days)"

rebuild walk "$REPO" \
  --days "$DAYS" \
  --deploy none \
  --dry-run \
  --output "$OUTPUT" \
  --no-screenshots

echo ""
echo "Done. Open: $OUTPUT/index.html"
