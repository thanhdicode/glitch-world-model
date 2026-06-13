#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"
: "${LEWM_DATA_ROOT:?Set LEWM_DATA_ROOT to the Lance dataset root.}"
: "${LEWM_OUTPUT_ROOT:?Set LEWM_OUTPUT_ROOT to the output directory.}"

cd "$LEWM_REPO_ROOT"

if [[ ! -f "$LEWM_OUTPUT_ROOT/preflight_passed.json" ]]; then
  echo "Refusing full R3 seed42 run: preflight_passed.json is missing." >&2
  exit 1
fi

TRAIN_DATASET="$LEWM_DATA_ROOT/tempglitch_train_normal_all_local.lance"
VALIDATION_DATASET="$LEWM_DATA_ROOT/tempglitch_validation_normal_all_local.lance"
LOG_PATH="$LEWM_OUTPUT_ROOT/r3_seed42_run.log"

python scripts/run_kaggle_lewm.py \
  --train-dataset "$TRAIN_DATASET" \
  --validation-dataset "$VALIDATION_DATASET" \
  --output-root "$LEWM_OUTPUT_ROOT" \
  --device cuda \
  --run-kind research \
  --batch-size 8 \
  --seed 42 \
  --num-workers 0 \
  --pin-memory \
  --mixed-precision \
  --early-stopping-patience 5 \
  --target-optimizer-updates 15000 \
  --evaluation-interval-updates 500 \
  --checkpoint-interval-updates 500 \
  2>&1 | tee "$LOG_PATH"
