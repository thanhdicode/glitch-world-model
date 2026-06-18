#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"
: "${WOB_LANCE_ROOT:?Set WOB_LANCE_ROOT to the WOB Lance root.}"
: "${WOB_OUTPUT_ROOT:?Set WOB_OUTPUT_ROOT to the WOB output directory.}"
: "${WOB_P1_METADATA_ROOT:?Set WOB_P1_METADATA_ROOT to the WOB metadata directory.}"

cd "$LEWM_REPO_ROOT"

TRAIN_DATASET="$WOB_LANCE_ROOT/wob_train_normal.lance"
VALIDATION_DATASET="$WOB_LANCE_ROOT/wob_validation_normal.lance"
OUTPUT_ROOT="$WOB_OUTPUT_ROOT/wob_seed42"
RUN_CONFIG="$WOB_P1_METADATA_ROOT/wob_seed42_run_config.json"

if [[ ! -d "$TRAIN_DATASET" ]]; then
  echo "Missing WOB train-normal Lance dataset: $TRAIN_DATASET" >&2
  exit 1
fi
if [[ ! -d "$VALIDATION_DATASET" ]]; then
  echo "Missing WOB validation-normal Lance dataset: $VALIDATION_DATASET" >&2
  exit 1
fi
if [[ ! -f "$RUN_CONFIG" ]]; then
  echo "Missing WOB seed42 run config: $RUN_CONFIG" >&2
  exit 1
fi

mkdir -p "$OUTPUT_ROOT"

export WOB_BATCH_SIZE="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["WOB_P1_METADATA_ROOT"]).joinpath("wob_seed42_run_config.json").read_text(encoding="utf-8"))
print(payload["batch_size"])
PY
)"
export WOB_TARGET_UPDATES="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["WOB_P1_METADATA_ROOT"]).joinpath("wob_seed42_run_config.json").read_text(encoding="utf-8"))
print(payload["target_optimizer_updates"])
PY
)"
export WOB_EVAL_INTERVAL="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["WOB_P1_METADATA_ROOT"]).joinpath("wob_seed42_run_config.json").read_text(encoding="utf-8"))
print(payload["evaluation_interval_updates"])
PY
)"
export WOB_CHECKPOINT_INTERVAL="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["WOB_P1_METADATA_ROOT"]).joinpath("wob_seed42_run_config.json").read_text(encoding="utf-8"))
print(payload["checkpoint_interval_updates"])
PY
)"
export WOB_EARLY_STOPPING="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["WOB_P1_METADATA_ROOT"]).joinpath("wob_seed42_run_config.json").read_text(encoding="utf-8"))
print(payload["early_stopping_patience"])
PY
)"

EXTRA_ARGS=("$@")

python scripts/run_kaggle_lewm.py \
  --train-dataset "$TRAIN_DATASET" \
  --validation-dataset "$VALIDATION_DATASET" \
  --output-root "$OUTPUT_ROOT" \
  --device cuda \
  --run-kind research \
  --batch-size "$WOB_BATCH_SIZE" \
  --seed 42 \
  --num-workers 0 \
  --pin-memory \
  --mixed-precision \
  --target-optimizer-updates "$WOB_TARGET_UPDATES" \
  --evaluation-interval-updates "$WOB_EVAL_INTERVAL" \
  --checkpoint-interval-updates "$WOB_CHECKPOINT_INTERVAL" \
  --early-stopping-patience "$WOB_EARLY_STOPPING" \
  "${EXTRA_ARGS[@]}"
