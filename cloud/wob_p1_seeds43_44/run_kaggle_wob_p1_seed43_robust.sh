#!/usr/bin/env bash
set -euo pipefail

export WOB_SEED=43
export WOB_SEED_NAME="wob_seed43"
export WOB_ACTION_MODE="real"
export WOB_ACTION_DIM=4
export WOB_P1_METADATA_ROOT="${WOB_P1_METADATA_ROOT:-/kaggle/working/wob_p1_seed43_metadata}"
export WOB_TRAIN_ROOT="${WOB_TRAIN_ROOT:-/kaggle/working/wob_p1_seed43_root}"
export WOB_LANCE_ROOT="${WOB_LANCE_ROOT:-/kaggle/working/wob_p1_seed43_lance}"
export WOB_LOG_DIR="${WOB_LOG_DIR:-/kaggle/working/wob_p1_seed43_logs}"
export WOB_ARTIFACT_TARBALL="${WOB_ARTIFACT_TARBALL:-/kaggle/working/wob_seed43_artifacts.tar.gz}"
export WOB_FAILURE_DEBUG_TARBALL="${WOB_FAILURE_DEBUG_TARBALL:-/kaggle/working/wob_seed43_failure_debug.tar.gz}"

bash cloud/wob_p1_seed42/run_kaggle_wob_p1_seed42_robust.sh "$@"
