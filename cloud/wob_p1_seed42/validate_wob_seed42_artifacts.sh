#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"
: "${WOB_OUTPUT_ROOT:?Set WOB_OUTPUT_ROOT to the WOB output directory.}"
: "${WOB_P1_METADATA_ROOT:?Set WOB_P1_METADATA_ROOT to the WOB metadata directory.}"
export WOB_SEED="${WOB_SEED:-42}"
export WOB_SEED_NAME="${WOB_SEED_NAME:-wob_seed${WOB_SEED}}"

cd "$LEWM_REPO_ROOT"

OUTPUT_ROOT="$WOB_OUTPUT_ROOT/$WOB_SEED_NAME"
RUN_CONFIG="$WOB_P1_METADATA_ROOT/${WOB_SEED_NAME}_run_config.json"

if [[ ! -f "$RUN_CONFIG" ]]; then
  echo "Missing WOB run config: $RUN_CONFIG" >&2
  exit 1
fi

TARGET_UPDATES="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["WOB_P1_METADATA_ROOT"]).joinpath(f"{os.environ['WOB_SEED_NAME']}_run_config.json").read_text(encoding="utf-8"))
print(payload["target_optimizer_updates"])
PY
)"

python scripts/validate_wob_seed_artifacts.py \
  --artifact-root "$OUTPUT_ROOT" \
  --expected-seed "$WOB_SEED" \
  --expected-target-updates "$TARGET_UPDATES" | tee "$OUTPUT_ROOT/validator_report.json"
