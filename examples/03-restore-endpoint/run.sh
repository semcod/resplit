#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"
ENDPOINT="${2:-/api/health}"
RESULTS_DIR="${3:-.rebuild}"

echo "rebuild restore: $ENDPOINT from $RESULTS_DIR"

# 1. Analyze "Truth" for this function/endpoint
echo -e "\n--- Analysis: Historical Truth ---"
# Assuming we want to analyze a handler in the repo
python3 -m rebuild analyze truth rebuild/application/services/restore_service.py find_last_working_day --repo "$REPO"

# 2. Execute restoration
python3 -m rebuild restore "$ENDPOINT" "$REPO" \
  --results-dir "$RESULTS_DIR" \
  --output restored/

echo -e "\n--- Done ---"
echo "  Restored project: restored/$(echo $ENDPOINT | sed 's/\//-/g' | sed 's/^-//')"
