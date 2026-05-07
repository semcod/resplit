#!/usr/bin/env bash
# ============================================================================
# run_mutation_tests.sh — Sprint 4b nightly mutation testing wrapper.
#
# Runs ``mutmut run`` against ``rebuild/domain/`` (the smallest, most stable
# layer — ideal for mutation analysis), then prints a summary and writes a
# Markdown report to ``docs/mutation_results.md``.
#
# Usage:
#     ./scripts/run_mutation_tests.sh                    # full run
#     PATHS=rebuild/domain/endpoint.py ./scripts/run_mutation_tests.sh
#     FAST=1 ./scripts/run_mutation_tests.sh             # cheap tests only
#
# Environment variables:
#     PATHS    — paths to mutate (default: rebuild/domain/)
#     FAST     — if set, runs ``pytest -x -q -k 'not slow'`` (faster but
#                less thorough)
#     OUTPUT   — output Markdown file (default: docs/mutation_results.md)
#
# Exit codes:
#     0    success — mutation score acceptable
#     1    mutmut not installed
#     2    test suite already failing (no point mutating)
#     3    too many surviving mutants (score < 80%)
# ============================================================================
set -euo pipefail

PATHS="${PATHS:-rebuild/domain/}"
OUTPUT="${OUTPUT:-docs/mutation_results.md}"
SCORE_THRESHOLD="${SCORE_THRESHOLD:-80}"

log() { printf '\033[36m[mutmut]\033[0m %s\n' "$*"; }
ok()  { printf '\033[32m[ok]\033[0m %s\n'    "$*"; }
err() { printf '\033[31m[err]\033[0m %s\n'   "$*" >&2; }

# ── Pre-flight ─────────────────────────────────────────────────────────────
if ! command -v mutmut >/dev/null 2>&1; then
  err "mutmut not installed. Install with: pip install 'rebuild[dev]'"
  exit 1
fi
ok "mutmut $(mutmut --version 2>&1 | head -1)"

log "Running test suite first to confirm baseline is green"
if [[ -n "${FAST:-}" ]]; then
  pytest -x -q -k 'not slow' >/dev/null 2>&1 || {
    err "Baseline test suite failing — fix tests before running mutation analysis"
    exit 2
  }
else
  pytest -x -q >/dev/null 2>&1 || {
    err "Baseline test suite failing — fix tests before running mutation analysis"
    exit 2
  }
fi
ok "Baseline green"

# ── Run mutation tests ─────────────────────────────────────────────────────
log "Mutating $PATHS (this can take 10-60 min depending on layer size)"
start_ts=$(date +%s)

# mutmut returns non-zero when any mutant survives — we capture & analyse.
set +e
mutmut run --paths-to-mutate "$PATHS"
mutmut_exit=$?
set -e

elapsed=$(( $(date +%s) - start_ts ))
log "mutmut completed in ${elapsed}s (exit=$mutmut_exit)"

# ── Parse results ──────────────────────────────────────────────────────────
log "Parsing results"
mutmut results > /tmp/mutmut_results.txt 2>&1 || true

# mutmut prints a summary like:
#   Mutation testing finished in 123 seconds
#   Killed: 84 mutants
#   Survived: 16 mutants
killed=$(grep -oP '(?<=killed:\s)\d+' /tmp/mutmut_results.txt | head -1 || echo 0)
survived=$(grep -oP '(?<=survived:\s)\d+' /tmp/mutmut_results.txt | head -1 || echo 0)
total=$(( killed + survived ))
if [[ $total -gt 0 ]]; then
  score=$(( 100 * killed / total ))
else
  score=0
fi

ok "Killed: $killed / Survived: $survived / Total: $total"
ok "Mutation score: ${score}% (threshold: ${SCORE_THRESHOLD}%)"

# ── Write Markdown report ──────────────────────────────────────────────────
log "Writing report to $OUTPUT"
mkdir -p "$(dirname "$OUTPUT")"
{
  echo "# Mutation testing results"
  echo
  echo "_Generated: $(date -Iseconds) by \`scripts/run_mutation_tests.sh\`_"
  echo
  echo "## Summary"
  echo
  echo "| Metric          | Value         |"
  echo "|-----------------|---------------|"
  echo "| Paths           | \`$PATHS\`     |"
  echo "| Killed mutants  | $killed       |"
  echo "| Survived mutants| $survived     |"
  echo "| Total           | $total        |"
  echo "| **Score**       | **${score}%** |"
  echo "| Threshold       | ${SCORE_THRESHOLD}%        |"
  echo "| Duration        | ${elapsed}s   |"
  echo
  echo "## Surviving mutants"
  echo
  if [[ $survived -gt 0 ]]; then
    echo "Run \`mutmut show <id>\` to inspect each:"
    echo
    echo '```'
    mutmut results 2>&1 | tail -60
    echo '```'
  else
    echo "_None — all mutants killed._"
  fi
} > "$OUTPUT"
ok "Report: $OUTPUT"

# ── Exit code based on threshold ───────────────────────────────────────────
if [[ $score -lt $SCORE_THRESHOLD ]]; then
  err "Score ${score}% < threshold ${SCORE_THRESHOLD}% — investigate surviving mutants"
  exit 3
fi
ok "Score acceptable"
