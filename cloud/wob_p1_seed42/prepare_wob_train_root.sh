#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"
: "${NORMAL_INPUT_ROOT:?Set NORMAL_INPUT_ROOT to the mounted WOB normal dataset root.}"
: "${TEST_INPUT_ROOT:?Set TEST_INPUT_ROOT to the mounted WOB test dataset root.}"
: "${WOB_TRAIN_ROOT:?Set WOB_TRAIN_ROOT to the WOB train root.}"
: "${WOB_P1_METADATA_ROOT:?Set WOB_P1_METADATA_ROOT to the WOB metadata directory.}"
: "${WOB_SPLIT_CSV:?Set WOB_SPLIT_CSV to the tracked WOB split CSV.}"

cd "$LEWM_REPO_ROOT"
mkdir -p "$WOB_TRAIN_ROOT" "$WOB_P1_METADATA_ROOT"

python cloud/wob_kaggle_native/prepare_wob_root.py \
  --split-csv "$WOB_SPLIT_CSV" \
  --normal-input-root "$NORMAL_INPUT_ROOT" \
  --test-input-root "$TEST_INPUT_ROOT" \
  --output-root "$WOB_TRAIN_ROOT" \
  --mode symlink \
  --no-locked \
  --phase p1_train_only

python - <<'PY'
import json
import os
from pathlib import Path

metadata = json.loads((Path(os.environ["WOB_TRAIN_ROOT"]) / "wob_root_metadata.json").read_text(encoding="utf-8"))
if metadata["selected_rows"] != 60:
    raise SystemExit("WOB-P1 root must materialize exactly 60 normal-only rows.")
if metadata["resolved_rows"] != 60 or metadata["missing_rows"] != 0:
    raise SystemExit("WOB-P1 root did not resolve all selected normal-only rows.")
print(json.dumps(metadata, indent=2))
PY
