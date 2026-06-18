#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"
: "${WOB_OUTPUT_ROOT:?Set WOB_OUTPUT_ROOT to the WOB output directory.}"
: "${WOB_P1_METADATA_ROOT:?Set WOB_P1_METADATA_ROOT to the WOB metadata directory.}"

cd "$LEWM_REPO_ROOT"

OUTPUT_ROOT="$WOB_OUTPUT_ROOT/wob_seed42"
RUN_CONFIG="$WOB_P1_METADATA_ROOT/wob_seed42_run_config.json"

if [[ ! -f "$RUN_CONFIG" ]]; then
  echo "Missing WOB seed42 run config: $RUN_CONFIG" >&2
  exit 1
fi

TARGET_UPDATES="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["WOB_P1_METADATA_ROOT"]).joinpath("wob_seed42_run_config.json").read_text(encoding="utf-8"))
print(payload["target_optimizer_updates"])
PY
)"

python scripts/validate_wob_seed42_artifacts.py \
  --artifact-root "$OUTPUT_ROOT" \
  --expected-seed 42 \
  --expected-target-updates "$TARGET_UPDATES" | tee "$OUTPUT_ROOT/validator_report.json"
