#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"
: "${WOB_SELECTED_SPLIT_CSV:?Set WOB_SELECTED_SPLIT_CSV to the filtered WOB split CSV.}"
: "${WOB_TRAIN_ROOT:?Set WOB_TRAIN_ROOT to the WOB train root.}"
: "${WOB_LANCE_ROOT:?Set WOB_LANCE_ROOT to the WOB Lance root.}"

cd "$LEWM_REPO_ROOT"
mkdir -p "$WOB_LANCE_ROOT"

python scripts/build_wob_lewm_lance.py \
  --split "$WOB_SELECTED_SPLIT_CSV" \
  --dataset-root "$WOB_TRAIN_ROOT" \
  --output "$WOB_LANCE_ROOT/wob_train_normal.lance" \
  --partition train

python scripts/build_wob_lewm_lance.py \
  --split "$WOB_SELECTED_SPLIT_CSV" \
  --dataset-root "$WOB_TRAIN_ROOT" \
  --output "$WOB_LANCE_ROOT/wob_validation_normal.lance" \
  --partition validation
