#!/usr/bin/env bash
set -euo pipefail

ENDPOINT="${1:-/api/health}"
REPO="${2:-.}"
OUTPUT="${3:-./restored}"
RESULTS_DIR="${4:-.resplit}"

echo "resplit restore: $ENDPOINT"
echo "  repo:        $REPO"
echo "  results-dir: $RESULTS_DIR"
echo "  output:      $OUTPUT"
echo ""

resplit restore "$ENDPOINT" "$REPO" \
  --output "$OUTPUT" \
  --results-dir "$RESULTS_DIR"

# Wyznacz katalog projektu
SLUG="${ENDPOINT#/}"
SLUG="${SLUG//\//-}"
PROJECT_DIR="$OUTPUT/$SLUG"

if [ -d "$PROJECT_DIR/docker" ]; then
  echo ""
  echo "Uruchomienie przywróconego projektu:"
  echo "  cd $PROJECT_DIR/docker"
  echo "  docker compose up -d"
  echo "  curl http://localhost:8003$ENDPOINT"
fi
