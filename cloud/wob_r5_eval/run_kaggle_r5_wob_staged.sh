#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="${REPO_DIR:-/kaggle/working/glitch-world-model}"
cd "$REPO_DIR"

export PYTHONPATH="$REPO_DIR/src:$REPO_DIR:${PYTHONPATH:-}"
export R5_WOB_OUTPUT_DIR="${R5_WOB_OUTPUT_DIR:-$REPO_DIR/outputs/r5_wob_identical_episode}"
export R5_WOB_FAILURE_DEBUG="${R5_WOB_FAILURE_DEBUG:-/kaggle/working/r5_wob_identical_episode_failure_debug.tar.gz}"
export R5_WOB_FAILURE_DEBUG_DIR="${R5_WOB_FAILURE_DEBUG_DIR:-/kaggle/working/r5_wob_identical_episode_failure_debug}"
export R5_WOB_SUCCESS_TARBALL="${R5_WOB_SUCCESS_TARBALL:-/kaggle/working/r5_wob_identical_episode_outputs.tar.gz}"
export R5_WOB_LOG="${R5_WOB_LOG:-/kaggle/working/r5_wob_staged.log}"
export KAGGLE_INPUT_ROOT="${KAGGLE_INPUT_ROOT:-/kaggle/input}"
export R5_WOB_DEVICE="${R5_WOB_DEVICE:-cuda}"
export R5_WOB_BASELINE_BATCH_SIZE="${R5_WOB_BASELINE_BATCH_SIZE:-4}"
export R5_WOB_LEWM_BATCH_SIZE="${R5_WOB_LEWM_BATCH_SIZE:-2}"
export R5_WOB_BOOTSTRAP_SEED="${R5_WOB_BOOTSTRAP_SEED:-42}"
export R5_WOB_N_BOOTSTRAP="${R5_WOB_N_BOOTSTRAP:-1000}"
export R5_WOB_FORCE="${R5_WOB_FORCE:-0}"
export R5_WOB_SMOKE="${R5_WOB_SMOKE:-0}"

mkdir -p /kaggle/working "$R5_WOB_FAILURE_DEBUG_DIR"
rm -f "$R5_WOB_LOG" "$R5_WOB_SUCCESS_TARBALL" "${R5_WOB_SUCCESS_TARBALL}.sha256" "$R5_WOB_FAILURE_DEBUG" "${R5_WOB_FAILURE_DEBUG}.sha256"

CURRENT_PHASE="initialization"
exec > >(tee -a "$R5_WOB_LOG") 2>&1

force_arg=()
smoke_arg=()
if [[ "$R5_WOB_FORCE" == "1" ]]; then
  force_arg+=(--force)
fi
if [[ "$R5_WOB_SMOKE" == "1" ]]; then
  smoke_arg+=(--smoke)
fi

write_failure_debug() {
  local exit_code="$1"
  local line_number="$2"
  local failed_command="$3"
  if ! python - "$R5_WOB_FAILURE_DEBUG" "$R5_WOB_FAILURE_DEBUG_DIR" "$R5_WOB_OUTPUT_DIR" "$CURRENT_PHASE" "$exit_code" "$line_number" "$failed_command" "$R5_WOB_LOG" <<'PY'
from pathlib import Path
import json
import subprocess
import sys

from cloud.wob_kaggle_native.common import write_debug_tarball

failure_tar = Path(sys.argv[1])
debug_dir = Path(sys.argv[2])
output_dir = Path(sys.argv[3])
phase = sys.argv[4]
exit_code = int(sys.argv[5])
line_number = sys.argv[6]
failed_command = sys.argv[7]
run_log = Path(sys.argv[8])

debug_dir.mkdir(parents=True, exist_ok=True)
git_sha = subprocess.run(
    ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
).stdout.strip()
(debug_dir / "failure_summary.json").write_text(
    json.dumps(
        {
            "schema_version": 1,
            "failure_class": "UNKNOWN_NEEDS_MORE_LOGS",
            "phase": phase,
            "exit_code": exit_code,
            "line_number": line_number,
            "failed_command": failed_command,
            "git_sha": git_sha,
            "output_dir_exists": output_dir.exists(),
            "locked_test_materialized": False,
            "locked_test_scored": False,
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
roots = [(debug_dir, "failure_debug")]
if run_log.exists():
    roots.append((run_log.parent, "working_logs"))
if output_dir.exists():
    roots.append((output_dir, "r5_wob_identical_episode"))
write_debug_tarball(
    failure_tar,
    roots,
    exclude_suffixes=(".tar", ".tar.gz", ".pt", ".pth", ".ckpt", ".lance"),
)
PY
  then
    echo "WARNING: failed to package the R5-WOB staged debug bundle." >&2
    return 0
  fi
  if [[ -f "$R5_WOB_FAILURE_DEBUG" ]]; then
    sha256sum "$R5_WOB_FAILURE_DEBUG" > "${R5_WOB_FAILURE_DEBUG}.sha256" || true
  fi
}

trap 'write_failure_debug "$?" "$LINENO" "$BASH_COMMAND"' ERR

echo "=== 1. Install lean staged R5-WOB runtime ==="
CURRENT_PHASE="install_runtime"
python -m pip install -q --no-cache-dir --no-deps \
  "stable-worldmodel==0.1.1" \
  "lancedb==0.33.0" \
  "pylance==7.0.0" \
  "lance-namespace==0.7.7" \
  "lance-namespace-urllib3-client==0.7.7" \
  "loguru==0.7.3" \
  "hydra-core==1.3.3"
python -m pip install -e "$REPO_DIR" --no-deps -q

run_stage() {
  local stage="$1"
  CURRENT_PHASE="$stage"
  python scripts/run_r5_wob_stage.py \
    --stage "$stage" \
    --input-root "$KAGGLE_INPUT_ROOT" \
    --output-dir "$R5_WOB_OUTPUT_DIR" \
    --success-tarball "$R5_WOB_SUCCESS_TARBALL" \
    --baseline-batch-size "$R5_WOB_BASELINE_BATCH_SIZE" \
    --lewm-batch-size "$R5_WOB_LEWM_BATCH_SIZE" \
    --device "$R5_WOB_DEVICE" \
    --bootstrap-seed "$R5_WOB_BOOTSTRAP_SEED" \
    --n-bootstrap "$R5_WOB_N_BOOTSTRAP" \
    "${force_arg[@]}" \
    "${smoke_arg[@]}"
}

echo "=== 2. Preflight ==="
run_stage preflight

echo "=== 3. Materialize Lance datasets ==="
run_stage materialize_lance

echo "=== 4. Baseline scores ==="
run_stage baseline_scores

echo "=== 5. LeWM seed42 ==="
run_stage lewm_seed42

echo "=== 6. LeWM seed43 ==="
run_stage lewm_seed43

echo "=== 7. LeWM seed44 ==="
run_stage lewm_seed44

echo "=== 8. Aggregate metrics ==="
run_stage aggregate_metrics

if [[ "$R5_WOB_SMOKE" == "1" ]]; then
  echo
  echo "=== SMOKE MODE COMPLETE ==="
  echo "$R5_WOB_OUTPUT_DIR"
  exit 0
fi

echo "=== 9. Validate and package ==="
run_stage validate_package

echo "=== 10. Validate stage markers ==="
CURRENT_PHASE="validate_stage_outputs"
python scripts/validate_r5_wob_stage_outputs.py --output-dir "$R5_WOB_OUTPUT_DIR"

rm -rf "$R5_WOB_FAILURE_DEBUG_DIR" "$R5_WOB_FAILURE_DEBUG" "${R5_WOB_FAILURE_DEBUG}.sha256"

echo
echo "=== DOWNLOAD SUCCESS FILES ==="
echo "$R5_WOB_SUCCESS_TARBALL"
echo "${R5_WOB_SUCCESS_TARBALL}.sha256"
