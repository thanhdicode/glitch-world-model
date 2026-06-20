#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="${REPO_DIR:-/kaggle/working/glitch-world-model}"
cd "$REPO_DIR"

export PYTHONPATH="$REPO_DIR:${PYTHONPATH:-}"
export R5_WOB_OUTPUT_DIR="${R5_WOB_OUTPUT_DIR:-$REPO_DIR/outputs/r5_wob_identical_episode}"
export R5_WOB_FAILURE_DEBUG="${R5_WOB_FAILURE_DEBUG:-/kaggle/working/r5_wob_identical_episode_failure_debug.tar.gz}"
export R5_WOB_FAILURE_DEBUG_DIR="${R5_WOB_FAILURE_DEBUG_DIR:-/kaggle/working/r5_wob_identical_episode_failure_debug}"
export R5_WOB_SUCCESS_TARBALL="${R5_WOB_SUCCESS_TARBALL:-/kaggle/working/r5_wob_identical_episode_outputs.tar.gz}"
export KAGGLE_INPUT_ROOT="${KAGGLE_INPUT_ROOT:-/kaggle/input}"
export R5_WOB_DEVICE="${R5_WOB_DEVICE:-cuda}"
export R5_WOB_BATCH_SIZE="${R5_WOB_BATCH_SIZE:-8}"

mkdir -p "$R5_WOB_FAILURE_DEBUG_DIR"
R5_WOB_RUN_LOG="$R5_WOB_FAILURE_DEBUG_DIR/runner.log"
CURRENT_PHASE="initialization"
exec > >(tee -a "$R5_WOB_RUN_LOG") 2>&1

find_one() {
  local pattern="$1"
  python - "$KAGGLE_INPUT_ROOT" "$pattern" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
pattern = sys.argv[2]
matches = sorted(root.rglob(pattern))
if not matches:
    raise SystemExit(1)
print(matches[0])
PY
}

cleanup_failure_debug() {
  rm -f "$R5_WOB_FAILURE_DEBUG" "${R5_WOB_FAILURE_DEBUG}.sha256"
  rm -rf "$R5_WOB_FAILURE_DEBUG_DIR"
}

write_failure_debug() {
  local exit_code="$1"
  local line_number="$2"
  local failed_command="$3"
  if ! python - "$R5_WOB_FAILURE_DEBUG" "$R5_WOB_FAILURE_DEBUG_DIR" "$R5_WOB_OUTPUT_DIR" "$CURRENT_PHASE" "$exit_code" "$line_number" "$failed_command" <<'PY'
from pathlib import Path
import json
import os
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
debug_dir.mkdir(parents=True, exist_ok=True)
git_sha = subprocess.run(
    ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
).stdout.strip()
(debug_dir / "failure_summary.json").write_text(
    json.dumps(
        {
            "schema_version": 1,
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
if output_dir.exists():
    roots.append((output_dir, "r5_wob_identical_episode"))
write_debug_tarball(failure_tar, roots, exclude_suffixes=(".tar", ".tar.gz", ".pt", ".pth", ".ckpt", ".lance"))
PY
  then
    echo "WARNING: failed to package the R5-WOB debug bundle." >&2
    return 0
  fi
  if [[ -f "$R5_WOB_FAILURE_DEBUG" ]]; then
    if ! sha256sum "$R5_WOB_FAILURE_DEBUG" > "${R5_WOB_FAILURE_DEBUG}.sha256"; then
      echo "WARNING: failed to hash the R5-WOB debug bundle." >&2
    fi
  fi
}

trap 'write_failure_debug "$?" "$LINENO" "$BASH_COMMAND"' ERR

CURRENT_PHASE="detect_kaggle_roots"
R5_WOB_ROOT_OUTPUT="$(python - <<'PY'
from pathlib import Path
from cloud.wob_kaggle_native.common import detect_kaggle_roots
normal_root, test_root = detect_kaggle_roots(Path("/kaggle/input"))
print(normal_root)
print(test_root)
PY
)"
mapfile -t R5_WOB_INPUT_ROOTS <<< "$R5_WOB_ROOT_OUTPUT"
if [[ "${#R5_WOB_INPUT_ROOTS[@]}" -ne 2 ]]; then
  echo "ERROR: expected exactly two Kaggle WOB input roots, found ${#R5_WOB_INPUT_ROOTS[@]}."
  false
fi
NORMAL_INPUT_ROOT="${R5_WOB_INPUT_ROOTS[0]}"
TEST_INPUT_ROOT="${R5_WOB_INPUT_ROOTS[1]}"

CURRENT_PHASE="find_seed_artifacts"
SEED42_TARBALL="$(find_one "wob_seed42_artifacts.tar.gz")"
SEED42_SHA="$(find_one "wob_seed42_artifacts.tar.gz.sha256")"
SEED43_TARBALL="$(find_one "wob_seed43_artifacts.tar.gz")"
SEED43_SHA="$(find_one "wob_seed43_artifacts.tar.gz.sha256")"
SEED44_TARBALL="$(find_one "wob_seed44_artifacts.tar.gz")"
SEED44_SHA="$(find_one "wob_seed44_artifacts.tar.gz.sha256")"

CURRENT_PHASE="validate_seed_artifacts"
python scripts/validate_wob_seed_artifacts.py --tarball "$SEED42_TARBALL" --sha256 "$SEED42_SHA" --expected-seed 42
python scripts/validate_wob_seed_artifacts.py --tarball "$SEED43_TARBALL" --sha256 "$SEED43_SHA" --expected-seed 43
python scripts/validate_wob_seed_artifacts.py --tarball "$SEED44_TARBALL" --sha256 "$SEED44_SHA" --expected-seed 44

CURRENT_PHASE="run_r5_wob_evaluation"
python scripts/run_r5_wob_identical_episode_evaluation.py \
  --normal-root "$NORMAL_INPUT_ROOT" \
  --test-root "$TEST_INPUT_ROOT" \
  --output-dir "$R5_WOB_OUTPUT_DIR" \
  --seed-artifact-tar "42=$SEED42_TARBALL" \
  --seed-artifact-sha256 "42=$SEED42_SHA" \
  --seed-artifact-tar "43=$SEED43_TARBALL" \
  --seed-artifact-sha256 "43=$SEED43_SHA" \
  --seed-artifact-tar "44=$SEED44_TARBALL" \
  --seed-artifact-sha256 "44=$SEED44_SHA" \
  --device "$R5_WOB_DEVICE" \
  --batch-size "$R5_WOB_BATCH_SIZE"

CURRENT_PHASE="validate_r5_wob_output"
python scripts/validate_r5_wob_evaluation.py --output-dir "$R5_WOB_OUTPUT_DIR"

CURRENT_PHASE="package_success_output"
cleanup_failure_debug
tar -czf "$R5_WOB_SUCCESS_TARBALL" -C "$R5_WOB_OUTPUT_DIR" .
sha256sum "$R5_WOB_SUCCESS_TARBALL" > "${R5_WOB_SUCCESS_TARBALL}.sha256"
