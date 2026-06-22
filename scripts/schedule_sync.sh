#!/usr/bin/env bash
# schedule_sync.sh — Run sync_from_github.sh on a repeating schedule.
#
# Usage:
#   bash scripts/schedule_sync.sh [--interval SECONDS] [--once] [--remote REMOTE] [--branch BRANCH]
#
# Options:
#   --interval SECONDS  Seconds between sync runs (default: 3600 = 1 hour).
#                       Also honoured via SYNC_INTERVAL_SECONDS env var.
#   --once              Run exactly one sync then exit (useful for CI / manual trigger).
#   --remote REMOTE     Passed through to sync_from_github.sh (default: origin).
#   --branch BRANCH     Passed through to sync_from_github.sh (default: current branch).
#
# Exit codes:
#   0   All sync runs completed successfully (--once mode).
#   1   A sync run failed (merge conflict, dirty tree, network error, etc.).
#       In loop mode the loop exits immediately on first failure so the error
#       is visible in logs rather than being silently retried.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync_from_github.sh"

INTERVAL="${SYNC_INTERVAL_SECONDS:-3600}"
ONCE=false
PASSTHROUGH_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interval)  INTERVAL="$2"; shift 2 ;;
    --once)      ONCE=true; shift ;;
    --remote|--branch)
                 PASSTHROUGH_ARGS+=("$1" "$2"); shift 2 ;;
    --allow-dirty)
                 PASSTHROUGH_ARGS+=("$1"); shift ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 [--interval SECONDS] [--once] [--remote REMOTE] [--branch BRANCH] [--allow-dirty]" >&2
      exit 1
      ;;
  esac
done

if [[ ! -x "$SYNC_SCRIPT" ]]; then
  echo "[ERROR] Sync script not found or not executable: $SYNC_SCRIPT" >&2
  exit 1
fi

run_sync() {
  local ts
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo ""
  echo "=========================================="
  echo "  GitHub sync — $ts"
  echo "=========================================="

  if bash "$SYNC_SCRIPT" "${PASSTHROUGH_ARGS[@]+"${PASSTHROUGH_ARGS[@]}"}"; then
    echo ""
    echo "[OK] Sync succeeded at $ts"
    return 0
  else
    local exit_code=$?
    echo "" >&2
    echo "[FAIL] Sync FAILED at $ts (exit code $exit_code)" >&2
    echo "       Check the output above for details." >&2
    echo "       Common causes: merge conflict, uncommitted local changes, network error." >&2
    return $exit_code
  fi
}

if [[ "$ONCE" == true ]]; then
  run_sync
  exit $?
fi

echo "=== Scheduled GitHub sync starting ==="
echo "Interval : ${INTERVAL}s ($(( INTERVAL / 60 )) min)"
echo "Script   : $SYNC_SCRIPT"
echo "Args     : ${PASSTHROUGH_ARGS[*]+"${PASSTHROUGH_ARGS[*]}"}"
echo ""
echo "First run begins immediately; subsequent runs every ${INTERVAL}s."
echo "This process must stay running for scheduled syncs to continue."
echo "Logs are visible in the Replit workflow console."
echo ""

RUN_COUNT=0
while true; do
  RUN_COUNT=$(( RUN_COUNT + 1 ))
  echo "--- Run #${RUN_COUNT} ---"

  if ! run_sync; then
    echo "" >&2
    echo "[FATAL] Sync run #${RUN_COUNT} failed. Stopping scheduler to prevent repeated failures." >&2
    echo "        Fix the issue (resolve conflicts, commit/stash changes) then restart the workflow." >&2
    exit 1
  fi

  NEXT_TS=$(date -u -d "@$(( $(date +%s) + INTERVAL ))" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null \
            || date -u -r "$(( $(date +%s) + INTERVAL ))" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null \
            || echo "in ${INTERVAL}s")
  echo ""
  echo "Next sync at approximately: $NEXT_TS"
  echo "Sleeping for ${INTERVAL}s ..."
  sleep "$INTERVAL"
done
