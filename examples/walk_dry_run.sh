#!/usr/bin/env bash
# Przykład: dry-run walk przez ostatnie 30 dni (bez deploy, bez docker)
set -euo pipefail

REPO="${1:-.}"

resplit walk "$REPO" \
  --days 30 \
  --deploy none \
  --dry-run \
  --output .resplit

echo "Raport: .resplit/index.html"
