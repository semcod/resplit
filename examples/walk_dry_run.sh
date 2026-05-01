#!/usr/bin/env bash
# Przykład: dry-run walk przez ostatnie 30 dni (bez deploy, bez docker)
set -euo pipefail

REPO="${1:-.}"

rebuild walk "$REPO" \
  --days 30 \
  --deploy none \
  --dry-run \
  --output .rebuild

echo "Raport: .rebuild/index.html"
