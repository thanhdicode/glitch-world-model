#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"

WOB_ROOT_OUTPUT="${WOB_ROOT_OUTPUT:-/kaggle/working/wob_root}"
AUDIT_OUTPUT_ROOT="${AUDIT_OUTPUT_ROOT:-/kaggle/working/wob_p0_materialization_audit}"

cd "$LEWM_REPO_ROOT"
python scripts/run_wob_p0_materialization_audit.py \
  --wob-root "$WOB_ROOT_OUTPUT" \
  --output-dir "$AUDIT_OUTPUT_ROOT" \
  --dry-run \
  --allow-materialization-check \
  --no-locked \
  --write-manifest-preview
