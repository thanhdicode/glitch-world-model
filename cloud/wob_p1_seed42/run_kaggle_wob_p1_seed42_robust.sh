#!/usr/bin/env bash
# Hardened WOB-P1 seed42 Kaggle runner — interruption-safe and rerun-safe.
#
# Features vs the original run_kaggle_wob_p1_seed42_all.sh:
#   - Log capture to /kaggle/working/wob_p1_seed42_logs/
#   - Heartbeat logging every 2 minutes during long stages
#   - Stage-level progress markers (skip completed stages on rerun)
#   - Resume-safe training (passes --resume when checkpoint exists)
#   - No blind rm -rf; partial outputs are preserved by default
#   - Comprehensive preflight checks
#   - Fail-closed safety (refuses locked-test, evaluation, missing data)
#   - Artifact finalization with manifest JSON and SHA256 hashes
#   - Environment and disk snapshots
set -Eeuo pipefail

# ---------------------------------------------------------------------------
# Resolve repo root
# ---------------------------------------------------------------------------
REPO_ROOT="${LEWM_REPO_ROOT:-$(pwd)}"
if [[ ! -f "$REPO_ROOT/pyproject.toml" ]]; then
  if [[ -f "$(pwd)/pyproject.toml" ]]; then
    REPO_ROOT="$(pwd)"
  else
    echo "ERROR: Could not resolve LEWM_REPO_ROOT; run from the repository root or export LEWM_REPO_ROOT." >&2
    exit 1
  fi
fi
export LEWM_REPO_ROOT="$REPO_ROOT"
cd "$LEWM_REPO_ROOT"

# ---------------------------------------------------------------------------
# Output / log directories
# ---------------------------------------------------------------------------
INPUT_ROOT="${INPUT_ROOT:-/kaggle/input}"
export WOB_OUTPUT_ROOT="${WOB_OUTPUT_ROOT:-/kaggle/working/wob_outputs}"
export WOB_P1_METADATA_ROOT="${WOB_P1_METADATA_ROOT:-/kaggle/working/wob_p1_metadata}"
export WOB_TRAIN_ROOT="${WOB_TRAIN_ROOT:-/kaggle/working/wob_p1_root}"
export WOB_LANCE_ROOT="${WOB_LANCE_ROOT:-/kaggle/working/wob_lance}"
export WOB_SPLIT_CSV="$LEWM_REPO_ROOT/configs/wob_protocol/split.csv"
export WOB_SELECTED_SPLIT_CSV="$WOB_P1_METADATA_ROOT/wob_p1_selected_split.csv"

LOG_DIR="${WOB_LOG_DIR:-/kaggle/working/wob_p1_seed42_logs}"
STAGE_DIR="$LOG_DIR/stages"
RUN_TS="$(date -u +%Y%m%dT%H%M%SZ 2>/dev/null || echo unknown)"
LOG_FILE="$LOG_DIR/run_${RUN_TS}.log"

mkdir -p "$WOB_OUTPUT_ROOT" "$WOB_P1_METADATA_ROOT" "$WOB_TRAIN_ROOT" \
         "$WOB_LANCE_ROOT" "$LOG_DIR" "$STAGE_DIR"

# ---------------------------------------------------------------------------
# Tee stdout+stderr into a log file while keeping console output
# ---------------------------------------------------------------------------
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=========================================="
echo "WOB-P1 seed42 ROBUST runner"
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date)"
echo "Log file: $LOG_FILE"
echo "Repo root: $LEWM_REPO_ROOT"
echo "=========================================="

# ---------------------------------------------------------------------------
# Heartbeat: background process that prints a timestamp every 120 seconds
# ---------------------------------------------------------------------------
_heartbeat_pid=""
start_heartbeat() {
  local label="${1:-idle}"
  stop_heartbeat
  (
    while true; do
      sleep 120
      echo "[HEARTBEAT $(date -u +%H:%M:%S 2>/dev/null || date)] stage=$label alive pid=$$ disk=$(df -h /kaggle/working 2>/dev/null | tail -1 | awk '{print $4}' || echo '?')"
    done
  ) &
  _heartbeat_pid=$!
}
stop_heartbeat() {
  if [[ -n "${_heartbeat_pid:-}" ]]; then
    kill "$_heartbeat_pid" 2>/dev/null || true
    wait "$_heartbeat_pid" 2>/dev/null || true
    _heartbeat_pid=""
  fi
}
trap stop_heartbeat EXIT

# ---------------------------------------------------------------------------
# Stage gate helpers — skip already-completed stages on rerun
# ---------------------------------------------------------------------------
stage_done() {
  [[ -f "$STAGE_DIR/$1.done" ]]
}
mark_stage_done() {
  date -u +%Y-%m-%dT%H:%M:%SZ > "$STAGE_DIR/$1.done" 2>/dev/null || echo "done" > "$STAGE_DIR/$1.done"
  echo "[STAGE] $1 completed at $(cat "$STAGE_DIR/$1.done")"
}

# ---------------------------------------------------------------------------
# Failure handler — package partial outputs for debugging
# ---------------------------------------------------------------------------
failure() {
  set +e
  echo "=== FAILURE HANDLER TRIGGERED ==="
  stop_heartbeat
  python - <<'PY'
import os
from pathlib import Path

from cloud.wob_p1_seed42.common import package_artifacts

roots = []
for env_name, prefix in [
    ("WOB_OUTPUT_ROOT", "wob_outputs"),
    ("WOB_P1_METADATA_ROOT", "wob_p1_metadata"),
]:
    root = Path(os.environ.get(env_name, ""))
    if root.exists():
        roots.append((root, prefix))
log_dir = Path(os.environ.get("WOB_LOG_DIR", "/kaggle/working/wob_p1_seed42_logs"))
if log_dir.exists():
    roots.append((log_dir, "logs"))
package_artifacts(Path("/kaggle/working/wob_seed42_failure_debug.tar.gz"), roots)
PY
  echo "Failure debug tarball written to /kaggle/working/wob_seed42_failure_debug.tar.gz"
}
trap failure ERR

# ---------------------------------------------------------------------------
# STAGE 0: Fail-closed safety checks
# ---------------------------------------------------------------------------
echo ""
echo "=== STAGE 0: Fail-closed safety checks ==="
# Refuse locked-test paths
if [[ -d "/kaggle/working/locked_test" ]] || [[ -d "/kaggle/working/test_outputs" ]]; then
  echo "FATAL: Locked-test output paths detected. Refusing to continue." >&2
  exit 1
fi
# Refuse evaluation/test scoring
for arg in "$@"; do
  if echo "$arg" | grep -qiE "(evaluate|test_scor|locked)"; then
    echo "FATAL: Evaluation/locked-test argument detected: $arg. Refusing to continue." >&2
    exit 1
  fi
done
echo "[SAFETY] No locked-test or evaluation paths detected."

# ---------------------------------------------------------------------------
# STAGE 1: Environment snapshot
# ---------------------------------------------------------------------------
echo ""
echo "=== STAGE 1: Environment snapshot ==="
start_heartbeat "env_snapshot"
{
  echo "--- Python ---"
  python --version 2>&1 || echo "Python not found"
  echo "--- GPU ---"
  nvidia-smi 2>&1 || echo "nvidia-smi not available"
  echo "--- Disk ---"
  df -h /kaggle/working 2>/dev/null || df -h . 2>/dev/null || echo "df not available"
  echo "--- Git SHA ---"
  git -C "$LEWM_REPO_ROOT" rev-parse HEAD 2>/dev/null || echo "not a git repo"
  echo "--- Date ---"
  date -u 2>/dev/null || date
} > "$LOG_DIR/env_snapshot_${RUN_TS}.txt" 2>&1
cat "$LOG_DIR/env_snapshot_${RUN_TS}.txt"
stop_heartbeat

# ---------------------------------------------------------------------------
# STAGE 2: Detect Kaggle inputs
# ---------------------------------------------------------------------------
echo ""
echo "=== STAGE 2: Detect Kaggle inputs ==="
if ! stage_done "detect_inputs"; then
  python - <<'PY'
import json
import os
from pathlib import Path

from cloud.wob_kaggle_native.common import detect_kaggle_roots

normal_root, test_root = detect_kaggle_roots(Path(os.environ.get("INPUT_ROOT", "/kaggle/input")))
if not normal_root.exists():
    raise SystemExit(f"FATAL: Normal input root does not exist: {normal_root}")
if not test_root.exists():
    raise SystemExit(f"FATAL: Test input root does not exist: {test_root}")
payload = {
    "normal_input_root": str(normal_root),
    "test_input_root": str(test_root),
    "phase": "p1_train_only",
    "seed": 42,
}
Path(os.environ["WOB_P1_METADATA_ROOT"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["WOB_P1_METADATA_ROOT"]).joinpath("detected_inputs.json").write_text(
    json.dumps(payload, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, indent=2))
PY
  mark_stage_done "detect_inputs"
else
  echo "[SKIP] detect_inputs already done"
fi

export NORMAL_INPUT_ROOT="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["WOB_P1_METADATA_ROOT"]).joinpath("detected_inputs.json").read_text(encoding="utf-8"))
print(payload["normal_input_root"])
PY
)"
export TEST_INPUT_ROOT="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["WOB_P1_METADATA_ROOT"]).joinpath("detected_inputs.json").read_text(encoding="utf-8"))
print(payload["test_input_root"])
PY
)"
echo "NORMAL_INPUT_ROOT=$NORMAL_INPUT_ROOT"
echo "TEST_INPUT_ROOT=$TEST_INPUT_ROOT"

# ---------------------------------------------------------------------------
# STAGE 3: Setup runtime
# ---------------------------------------------------------------------------
echo ""
echo "=== STAGE 3: Setup runtime ==="
if ! stage_done "setup_runtime"; then
  start_heartbeat "setup_runtime"
  bash cloud/wob_p1_seed42/setup_runtime.sh
  stop_heartbeat
  mark_stage_done "setup_runtime"
else
  echo "[SKIP] setup_runtime already done"
fi

# ---------------------------------------------------------------------------
# STAGE 4: Preflight checks
# ---------------------------------------------------------------------------
echo ""
echo "=== STAGE 4: Preflight checks ==="
if ! stage_done "preflight"; then
  start_heartbeat "preflight"
  # Run the comprehensive Python preflight
  python cloud/wob_p1_seed42/preflight_robust.py \
    --repo-root "$LEWM_REPO_ROOT" \
    --output-root "$WOB_OUTPUT_ROOT/wob_seed42" \
    --log-dir "$LOG_DIR" 2>&1
  # Run the original preflight for split validation and config generation
  bash cloud/wob_p1_seed42/preflight.sh
  stop_heartbeat
  mark_stage_done "preflight"
else
  echo "[SKIP] preflight already done"
fi

# ---------------------------------------------------------------------------
# STAGE 5: Prepare WOB train root
# ---------------------------------------------------------------------------
echo ""
echo "=== STAGE 5: Prepare WOB train root ==="
if ! stage_done "prepare_train_root"; then
  start_heartbeat "prepare_train_root"
  bash cloud/wob_p1_seed42/prepare_wob_train_root.sh
  stop_heartbeat
  mark_stage_done "prepare_train_root"
else
  echo "[SKIP] prepare_train_root already done"
fi

# ---------------------------------------------------------------------------
# STAGE 6: Build Lance datasets
# ---------------------------------------------------------------------------
echo ""
echo "=== STAGE 6: Build Lance datasets ==="
if ! stage_done "build_lance"; then
  start_heartbeat "build_lance"
  bash cloud/wob_p1_seed42/build_wob_lance_train_seed42.sh
  stop_heartbeat
  mark_stage_done "build_lance"
else
  echo "[SKIP] build_lance already done"
fi

# ---------------------------------------------------------------------------
# STAGE 7: Training (resume-safe)
# ---------------------------------------------------------------------------
echo ""
echo "=== STAGE 7: Training ==="
CHECKPOINT_FILE="$WOB_OUTPUT_ROOT/wob_seed42/checkpoint_weights.pt"
TRAINING_META="$WOB_OUTPUT_ROOT/wob_seed42/training_metadata.json"
RESUME_FLAG=""

if [[ -f "$TRAINING_META" ]]; then
  echo "[SKIP] Training already completed (training_metadata.json exists)"
  echo "  To force retraining, remove $TRAINING_META and rerun."
elif [[ -f "$CHECKPOINT_FILE" ]]; then
  echo "[RESUME] Found existing checkpoint at $CHECKPOINT_FILE"
  echo "  Will attempt to resume training from checkpoint."
  RESUME_FLAG="--resume"
  start_heartbeat "training_resume"
  bash cloud/wob_p1_seed42/run_wob_seed42_train.sh $RESUME_FLAG
  stop_heartbeat
else
  echo "[START] No checkpoint found. Starting training from scratch."
  start_heartbeat "training"
  bash cloud/wob_p1_seed42/run_wob_seed42_train.sh
  stop_heartbeat
fi

# ---------------------------------------------------------------------------
# STAGE 8: Validate artifacts
# ---------------------------------------------------------------------------
echo ""
echo "=== STAGE 8: Validate artifacts ==="
start_heartbeat "validate"
bash cloud/wob_p1_seed42/validate_wob_seed42_artifacts.sh
stop_heartbeat

# ---------------------------------------------------------------------------
# STAGE 9: Artifact finalization
# ---------------------------------------------------------------------------
echo ""
echo "=== STAGE 9: Artifact finalization ==="
python cloud/wob_p1_seed42/finalize_artifacts.py \
  --output-root "$WOB_OUTPUT_ROOT/wob_seed42" \
  --metadata-root "$WOB_P1_METADATA_ROOT" \
  --log-dir "$LOG_DIR" \
  --tarball-path "/kaggle/working/wob_seed42_artifacts.tar.gz" \
  --failure-debug-path "/kaggle/working/wob_seed42_failure_debug.tar.gz"

if [[ -f /kaggle/working/wob_seed42_artifacts.tar.gz ]]; then
  sha256sum /kaggle/working/wob_seed42_artifacts.tar.gz > /kaggle/working/wob_seed42_artifacts.tar.gz.sha256
  echo "Tarball SHA256:"
  cat /kaggle/working/wob_seed42_artifacts.tar.gz.sha256
fi

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "WOB-P1 seed42 ROBUST runner completed"
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date)"
echo "Log file: $LOG_FILE"
echo "=========================================="

python - <<'PY'
import json
import os
from pathlib import Path

preflight_path = Path(os.environ["WOB_OUTPUT_ROOT"]) / "wob_seed42" / "preflight_passed.json"
if preflight_path.is_file():
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    print(
        "\n".join(
            [
                f"P1 selected rows: {preflight['selected_rows']}",
                f"train-normal count: {preflight['train_normal_count']}",
                f"validation-normal count: {preflight['validation_normal_count']}",
                f"validation-buggy excluded: {preflight['validation_buggy_excluded_count']}",
                f"locked rows skipped: {preflight['locked_rows_skipped']}",
                "checkpoint selected by validation-normal only",
                "locked_test_materialized=false",
                "locked_test_scored=false",
            ]
        )
    )
else:
    print("WARNING: preflight_passed.json not found; cannot print summary.")
PY

stop_heartbeat
echo "Done."
