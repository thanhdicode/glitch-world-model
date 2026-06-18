#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"

NORMAL_INPUT_ROOT="${NORMAL_INPUT_ROOT:-/kaggle/input/world-of-bugs-normal}"
TEST_INPUT_ROOT="${TEST_INPUT_ROOT:-/kaggle/input/world-of-bugs-test}"
SPLIT_CSV="${SPLIT_CSV:-$LEWM_REPO_ROOT/outputs/gate3/world_of_bugs/split.csv}"
WOB_ROOT_OUTPUT="${WOB_ROOT_OUTPUT:-/kaggle/working/wob_root}"
P0_OUTPUT_ROOT="${P0_OUTPUT_ROOT:-/kaggle/working/wob_kaggle_native_outputs}"
WOB_PHASE="${WOB_PHASE:-p0_full_nonlocked}"

mkdir -p "$WOB_ROOT_OUTPUT" "$P0_OUTPUT_ROOT"
cd "$LEWM_REPO_ROOT"

python cloud/wob_kaggle_native/prepare_wob_root.py \
  --split-csv "$SPLIT_CSV" \
  --normal-input-root "$NORMAL_INPUT_ROOT" \
  --test-input-root "$TEST_INPUT_ROOT" \
  --output-root "$WOB_ROOT_OUTPUT" \
  --mode symlink \
  --no-locked \
  --phase "$WOB_PHASE"
