#!/usr/bin/env bash
# ============================================================================
# run_c2004_full.sh — Full 30-day walk against the c2004 case-study repository.
#
# This is the canonical reproducer for the c2004 showcase. It clones c2004 into
# a sibling directory (or reuses an existing checkout), runs ``rebuild walk``
# for 30 days with docker-compose deployment, and writes the timeline +
# dashboard to ``./.rebuild_c2004/``.
#
# Usage:
#     ./scripts/run_c2004_full.sh              # default: 30 days
#     DAYS=7 ./scripts/run_c2004_full.sh        # shorter
#     C2004_PATH=/path/to/c2004 ./scripts/run_c2004_full.sh
#     SKIP_DEPLOY=1 ./scripts/run_c2004_full.sh # dry-run only (no docker)
#
# Environment variables:
#     DAYS              — number of days to walk (default: 30)
#     C2004_PATH        — existing c2004 checkout (default: ../c2004)
#     C2004_REPO        — git URL for fresh clone (default: github.com/semcod/c2004)
#     OUTPUT_DIR        — output directory (default: .rebuild_c2004)
#     HEALTH_URL        — service health endpoint (default: http://localhost:8003/api/health)
#     BASE_URL          — service base URL (default: http://localhost:8003)
#     HEALTH_TIMEOUT    — seconds to wait for deploy health (default: 120)
#     SKIP_DEPLOY       — if set, run in --dry-run mode (no docker-compose)
#
# Exit codes:
#     0   success
#     1   prerequisite missing (rebuild, docker, git)
#     2   c2004 checkout failed
#     3   walk failed
# ============================================================================

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────
DAYS="${DAYS:-30}"
C2004_PATH="${C2004_PATH:-../c2004}"
C2004_REPO="${C2004_REPO:-https://github.com/semcod/c2004.git}"
OUTPUT_DIR="${OUTPUT_DIR:-.rebuild_c2004}"
HEALTH_URL="${HEALTH_URL:-http://localhost:8003/api/health}"
BASE_URL="${BASE_URL:-http://localhost:8003}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-120}"

# ── Pretty output ──────────────────────────────────────────────────────────
log() { printf '\033[36m[c2004]\033[0m %s\n' "$*"; }
ok()  { printf '\033[32m[ok]\033[0m %s\n'    "$*"; }
err() { printf '\033[31m[err]\033[0m %s\n'   "$*" >&2; }

# ── Pre-flight checks ──────────────────────────────────────────────────────
log "Pre-flight checks"

if ! command -v rebuild >/dev/null 2>&1; then
  err "rebuild CLI not found. Install with: pip install rebuild"
  exit 1
fi
ok "rebuild $(rebuild --version 2>&1 | head -1)"

if ! command -v git >/dev/null 2>&1; then
  err "git not found"
  exit 1
fi
ok "git $(git --version | awk '{print $3}')"

if [[ -z "${SKIP_DEPLOY:-}" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    err "docker not found (set SKIP_DEPLOY=1 to skip deploy)"
    exit 1
  fi
  ok "docker $(docker --version | awk '{print $3}' | tr -d ',')"
fi

# ── Obtain c2004 checkout ──────────────────────────────────────────────────
if [[ -d "$C2004_PATH/.git" ]]; then
  log "Reusing c2004 at $C2004_PATH"
  ( cd "$C2004_PATH" && git fetch --tags --quiet )
else
  log "Cloning $C2004_REPO → $C2004_PATH"
  if ! git clone --quiet "$C2004_REPO" "$C2004_PATH"; then
    err "git clone failed"
    exit 2
  fi
fi
ok "c2004 ready at $C2004_PATH"

# ── Walk arguments ─────────────────────────────────────────────────────────
walk_args=(
  walk "$C2004_PATH"
  --days "$DAYS"
  --output "$OUTPUT_DIR"
  --health-url "$HEALTH_URL"
  --base-url   "$BASE_URL"
  --health-timeout "$HEALTH_TIMEOUT"
)

if [[ -n "${SKIP_DEPLOY:-}" ]]; then
  walk_args+=( --dry-run --deploy none )
  log "Running in DRY-RUN mode (no docker)"
else
  walk_args+=( --deploy docker-compose )
fi

# ── Run walk ───────────────────────────────────────────────────────────────
log "rebuild ${walk_args[*]}"
start_ts=$(date +%s)
if ! rebuild "${walk_args[@]}"; then
  err "rebuild walk failed"
  exit 3
fi
elapsed=$(( $(date +%s) - start_ts ))
ok "Walk completed in ${elapsed}s"

# ── Generate dashboard ─────────────────────────────────────────────────────
log "Generating dashboard"
rebuild dashboard --results-dir "$OUTPUT_DIR" --repo "$C2004_PATH" || {
  err "dashboard generation failed (non-fatal)"
}

# ── Summary ────────────────────────────────────────────────────────────────
log "Summary"
if [[ -f "$OUTPUT_DIR/history.json" ]]; then
  python3 -c "
import json, sys
from pathlib import Path
data = json.loads(Path('$OUTPUT_DIR/history.json').read_text())
if not data:
    sys.exit(0)
total = len(data)
ok_days = sum(1 for d in data if d.get('deploy_success'))
mean_health = sum(d.get('health_pct', 0) for d in data) / max(1, total)
print(f'  Days walked:       {total}')
print(f'  Successful deploys: {ok_days}/{total} ({100*ok_days/total:.0f}%)')
print(f'  Mean health %:     {mean_health:.1f}%')
"
fi

echo
ok "Reports:"
echo "  Timeline:  $OUTPUT_DIR/index.html"
echo "  Dashboard: $OUTPUT_DIR/dashboard.html"
echo "  Per-day:   $OUTPUT_DIR/YYYY-MM-DD/report.html"
echo
ok "Open with: rebuild walk --serve --port 7821 (or 'python3 -m http.server' in $OUTPUT_DIR)"
