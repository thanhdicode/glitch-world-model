#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"
: "${LEWM_DATA_ROOT:?Set LEWM_DATA_ROOT to the Lance dataset root.}"
: "${LEWM_OUTPUT_ROOT:?Set LEWM_OUTPUT_ROOT to the output directory.}"

cd "$LEWM_REPO_ROOT"
mkdir -p "$LEWM_OUTPUT_ROOT"

TRAIN_DATASET="$LEWM_DATA_ROOT/tempglitch_train_normal_all_local.lance"
VALIDATION_DATASET="$LEWM_DATA_ROOT/tempglitch_validation_normal_all_local.lance"

if [[ ! -d "$TRAIN_DATASET" ]]; then
  echo "Missing train-normal Lance dataset: $TRAIN_DATASET" >&2
  exit 1
fi
if [[ ! -d "$VALIDATION_DATASET" ]]; then
  echo "Missing validation-normal Lance dataset: $VALIDATION_DATASET" >&2
  exit 1
fi

python scripts/validate_cloud_gpu_runtime.py --output-root "$LEWM_OUTPUT_ROOT"

set +e
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
  --target-optimizer-updates 1 \
  --evaluation-interval-updates 1 \
  --checkpoint-interval-updates 1 \
  --max-validation-steps 1
status=$?
set -e

if [[ "$status" -ne 0 ]]; then
  python - <<'PY'
import json
import os
from pathlib import Path

output = Path(os.environ["LEWM_OUTPUT_ROOT"])
(output / "preflight_failed.json").write_text(json.dumps({
    "status": "failed",
    "reason": "one_update_training_failed",
    "locked_test_materialized": False,
    "locked_test_scored": False,
}, indent=2) + "\n", encoding="utf-8")
PY
  exit "$status"
fi

python - <<'PY'
import json
import os
from pathlib import Path

output = Path(os.environ["LEWM_OUTPUT_ROOT"])
runtime = json.loads((output / "cloud_runtime_preflight.json").read_text(encoding="utf-8"))
metadata = json.loads((output / "training_metadata.json").read_text(encoding="utf-8"))
passed = {
    "status": "passed",
    "runtime": runtime,
    "updates_completed": metadata["updates_completed"],
    "target_optimizer_updates": metadata["target_optimizer_updates"],
    "checkpoint_reload_verified": (
        metadata["checkpoint_reload"]["weights_reload_verified"]
        and metadata["checkpoint_reload"]["optimizer_reload_verified"]
        and metadata["checkpoint_reload"]["scheduler"]["reload_verified"]
        and metadata["checkpoint_reload"]["reloaded_global_step"] == 1
    ),
    "train_normal_readable": True,
    "validation_normal_readable": True,
    "validation_buggy_used_for_fit_select": False,
    "locked_test_materialized": False,
    "locked_test_scored": False,
}
if passed["updates_completed"] != 1 or passed["target_optimizer_updates"] != 1:
    raise SystemExit("Preflight did not complete exactly one optimizer update.")
if not passed["checkpoint_reload_verified"]:
    raise SystemExit("Preflight checkpoint reload was not verified.")
(output / "preflight_passed.json").write_text(
    json.dumps(passed, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps(passed, indent=2))
PY
