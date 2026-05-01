#!/usr/bin/env bash
# Przykład: przywróć endpoint /api/health jako izolowany projekt
set -euo pipefail

ENDPOINT="${1:-/api/health}"
REPO="${2:-.}"
OUTPUT="${3:-./restored}"

rebuild restore "$ENDPOINT" "$REPO" \
  --output "$OUTPUT" \
  --results-dir .rebuild

echo "Przywrócono do: $OUTPUT"
