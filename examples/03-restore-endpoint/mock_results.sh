#!/usr/bin/env bash
# Pomocniczy skrypt: tworzy przykładowe wyniki walk w .rebuild/
# żeby przetestować restore bez pełnego walk.
set -euo pipefail

RESULTS_DIR="${1:-.rebuild}"

echo "Tworzę przykładowe wyniki walk w $RESULTS_DIR ..."

# Dzień 1 — endpoint działa
D1=$(date -d "3 days ago" +%Y-%m-%d 2>/dev/null || date -v-3d +%Y-%m-%d)
mkdir -p "$RESULTS_DIR/$D1"
cat > "$RESULTS_DIR/$D1/results.json" <<EOF
[
  {"path": "/api/health", "method": "GET", "url": "http://localhost:8003/api/health",
   "status": "ok", "http_status": 200, "response_time_ms": 45.0, "error": null}
]
EOF
echo "abc123def456" > "$RESULTS_DIR/$D1/commit.txt"
echo "feat: add health endpoint" >> "$RESULTS_DIR/$D1/commit.txt"

# Dzień 2 — endpoint nie działa
D2=$(date -d "1 day ago" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
mkdir -p "$RESULTS_DIR/$D2"
cat > "$RESULTS_DIR/$D2/results.json" <<EOF
[
  {"path": "/api/health", "method": "GET", "url": "http://localhost:8003/api/health",
   "status": "fail", "http_status": 500, "response_time_ms": 12.0, "error": "Internal Server Error"}
]
EOF

echo ""
echo "Wyniki mock w: $RESULTS_DIR/"
echo "  $D1/ — status: ok"
echo "  $D2/ — status: fail"
echo ""
echo "Teraz możesz uruchomić: ./run.sh /api/health . ./restored $RESULTS_DIR"
