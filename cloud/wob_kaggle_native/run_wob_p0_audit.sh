#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"

cd "$LEWM_REPO_ROOT"

WOB_ROOT_OUTPUT="${WOB_ROOT_OUTPUT:-/kaggle/working/wob_root}"
AUDIT_OUTPUT_ROOT="${AUDIT_OUTPUT_ROOT:-/kaggle/working/wob_p0_materialization_audit}"
if [[ -z "${SPLIT_CSV:-}" ]]; then
  SPLIT_CSV="$(python - <<'PY'
from pathlib import Path
from cloud.wob_kaggle_native.common import resolve_split_csv
import os
print(resolve_split_csv(Path(os.environ["LEWM_REPO_ROOT"])))
PY
)"
fi
if [[ -z "${PROTOCOL_AUDIT_PATH:-}" ]]; then
  PROTOCOL_AUDIT_PATH="$(python - <<'PY'
from pathlib import Path
from cloud.wob_kaggle_native.common import resolve_protocol_audit
import os
print(resolve_protocol_audit(Path(os.environ["LEWM_REPO_ROOT"])))
PY
)"
fi
if [[ -z "${SPLIT_AUDIT_PATH:-}" ]]; then
  SPLIT_AUDIT_PATH="$(python - <<'PY'
from pathlib import Path
from cloud.wob_kaggle_native.common import resolve_split_audit
import os
print(resolve_split_audit(Path(os.environ["LEWM_REPO_ROOT"])))
PY
)"
fi
python scripts/run_wob_p0_materialization_audit.py \
  --wob-root "$WOB_ROOT_OUTPUT" \
  --output-dir "$AUDIT_OUTPUT_ROOT" \
  --split-path "$SPLIT_CSV" \
  --protocol-audit-path "$PROTOCOL_AUDIT_PATH" \
  --split-audit-path "$SPLIT_AUDIT_PATH" \
  --dry-run \
  --allow-materialization-check \
  --no-locked \
  --write-manifest-preview
