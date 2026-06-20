#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"
: "${NORMAL_INPUT_ROOT:?Set NORMAL_INPUT_ROOT to the mounted WOB normal dataset root.}"
: "${TEST_INPUT_ROOT:?Set TEST_INPUT_ROOT to the mounted WOB test dataset root.}"
: "${WOB_OUTPUT_ROOT:?Set WOB_OUTPUT_ROOT to the WOB output directory.}"
: "${WOB_P1_METADATA_ROOT:?Set WOB_P1_METADATA_ROOT to the WOB metadata directory.}"
: "${WOB_SPLIT_CSV:?Set WOB_SPLIT_CSV to the tracked WOB split CSV.}"
: "${WOB_SELECTED_SPLIT_CSV:?Set WOB_SELECTED_SPLIT_CSV to the filtered WOB split CSV output path.}"
: "${WOB_TRAIN_ROOT:?Set WOB_TRAIN_ROOT to the selected WOB root output path.}"
export WOB_SEED="${WOB_SEED:-42}"
export WOB_SEED_NAME="${WOB_SEED_NAME:-wob_seed${WOB_SEED}}"

cd "$LEWM_REPO_ROOT"
mkdir -p "$WOB_OUTPUT_ROOT/$WOB_SEED_NAME" "$WOB_P1_METADATA_ROOT" "$WOB_TRAIN_ROOT"

python scripts/validate_cloud_gpu_runtime.py \
  --output-root "$WOB_OUTPUT_ROOT/$WOB_SEED_NAME" \
  --min-compute-major 7 \
  --min-vram-gb 14

python - <<'PY'
import json
import os
from pathlib import Path

from cloud.wob_p1_seed42.common import load_research_schedule, write_selected_split_csv

repo_root = Path(os.environ["LEWM_REPO_ROOT"])
split_csv = Path(os.environ["WOB_SPLIT_CSV"])
selected_split_csv = Path(os.environ["WOB_SELECTED_SPLIT_CSV"])
summary = write_selected_split_csv(split_csv, selected_split_csv)
schedule = load_research_schedule(repo_root / "configs" / "lewm_research_mvp.yaml")
seed = int(os.environ["WOB_SEED"])
seed_name = os.environ["WOB_SEED_NAME"]
artifact_root = Path(os.environ["WOB_OUTPUT_ROOT"]) / seed_name
runtime = json.loads((artifact_root / "cloud_runtime_preflight.json").read_text(encoding="utf-8"))

payload = {
    "status": "passed",
    "phase": "p1_train_only",
    "seed": seed,
    "seed_name": seed_name,
    "normal_input_root": os.environ["NORMAL_INPUT_ROOT"],
    "test_input_root": os.environ["TEST_INPUT_ROOT"],
    "split_csv": str(split_csv),
    "selected_split_csv": str(selected_split_csv),
    "train_normal_count": summary["train_normal_count"],
    "validation_normal_count": summary["validation_normal_count"],
    "validation_buggy_excluded_count": summary["validation_buggy_excluded_count"],
    "locked_rows_skipped": summary["locked_rows_skipped"],
    "selected_rows": summary["train_normal_count"] + summary["validation_normal_count"],
    "batch_size": schedule["batch_size"],
    "target_optimizer_updates": schedule["target_optimizer_updates"],
    "evaluation_interval_updates": schedule["evaluation_interval_updates"],
    "checkpoint_interval_updates": schedule["checkpoint_interval_updates"],
    "early_stopping_patience": schedule["early_stopping_patience"],
    "checkpoint_selected_by": "validation_normal_only",
    "action_mode": "real",
    "action_dim": 4,
    "locked_test_materialized": False,
    "locked_test_scored": False,
    "validation_buggy_used_for_fit_select": False,
    "future_training_gpu_ok": runtime["status"] == "passed",
}
if payload["train_normal_count"] != 48:
    raise SystemExit("Expected 48 train-normal rows for WOB-P1.")
if payload["validation_normal_count"] != 12:
    raise SystemExit("Expected 12 validation-normal rows for WOB-P1.")
if payload["validation_buggy_excluded_count"] != 60:
    raise SystemExit("Expected 60 validation-buggy rows to remain excluded.")
if payload["locked_rows_skipped"] != 59:
    raise SystemExit("Expected 59 locked rows to remain skipped.")
(artifact_root / "preflight_passed.json").write_text(
    json.dumps(payload, indent=2) + "\n",
    encoding="utf-8",
)
(Path(os.environ["WOB_P1_METADATA_ROOT"]) / f"{seed_name}_run_config.json").write_text(
    json.dumps(schedule, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, indent=2))
PY
