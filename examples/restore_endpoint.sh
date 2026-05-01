#!/usr/bin/env bash
# Przykład: przywróć endpoint /api/health jako izolowany projekt
set -euo pipefail

ENDPOINT="${1:-/api/health}"
REPO="${2:-.}"
OUTPUT="${3:-./restored}"

resplit restore "$ENDPOINT" "$REPO" \
  --output "$OUTPUT" \
  --results-dir .resplit

echo "Przywrócono do: $OUTPUT"
