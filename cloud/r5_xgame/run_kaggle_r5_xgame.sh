#!/usr/bin/env bash
# R5-XGAME: Cross-dataset comparison entrypoint.
#
# SKELETON ONLY — this script is CPU-only and aggregates previously validated
# R5 TempGlitch and R5 WOB metric files. It does not run any model or scorer.
#
# Prerequisites:
#   - R5 TempGlitch outputs validated
#   - R5-WOB outputs validated
#
# Usage:
#   bash cloud/r5_xgame/run_kaggle_r5_xgame.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== R5-XGAME Cross-Dataset Comparison ==="
echo "Repo root: $REPO_ROOT"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Default paths
TEMPGLITCH_METRICS="${REPO_ROOT}/outputs/r5_tempglitch_identical_episode/r5_metrics.json"
WOB_METRICS="${REPO_ROOT}/outputs/r5_wob_identical_episode/r5_wob_metrics.json"
OUTPUT_DIR="${REPO_ROOT}/outputs/r5_xgame_comparison"

# Check prerequisites
if [ ! -f "$TEMPGLITCH_METRICS" ]; then
    echo "ERROR: TempGlitch R5 metrics not found: $TEMPGLITCH_METRICS"
    exit 1
fi

if [ ! -f "$WOB_METRICS" ]; then
    echo "ERROR: R5-WOB metrics are required and must be validator-passed before R5-XGAME."
    exit 1
fi
echo "WOB metrics found: $WOB_METRICS"

# Run comparison
python "$REPO_ROOT/scripts/run_r5_xgame_comparison.py" \
    --tempglitch-metrics "$TEMPGLITCH_METRICS" \
    --wob-metrics "$WOB_METRICS" \
    --output-dir "$OUTPUT_DIR"

# Validate
python "$REPO_ROOT/scripts/validate_r5_xgame_comparison.py" \
    --output-dir "$OUTPUT_DIR"

echo "=== R5-XGAME complete ==="
