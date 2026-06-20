#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"

cd "$LEWM_REPO_ROOT"

NORMAL_INPUT_ROOT="${NORMAL_INPUT_ROOT:-/kaggle/input/world-of-bugs-normal}"
TEST_INPUT_ROOT="${TEST_INPUT_ROOT:-/kaggle/input/world-of-bugs-test}"
P0_OUTPUT_ROOT="${P0_OUTPUT_ROOT:-/kaggle/working/wob_kaggle_native_outputs}"
if [[ -z "${SPLIT_CSV:-}" ]]; then
  SPLIT_CSV="$(python - <<'PY'
from pathlib import Path
from cloud.wob_kaggle_native.common import resolve_split_csv
import os
print(resolve_split_csv(Path(os.environ["LEWM_REPO_ROOT"])))
PY
)"
fi
export NORMAL_INPUT_ROOT TEST_INPUT_ROOT SPLIT_CSV P0_OUTPUT_ROOT
mkdir -p "$P0_OUTPUT_ROOT"

python - <<'PY'
import json
import os
import platform
import sys
from pathlib import Path

payload = {
    "python_version": sys.version,
    "platform": platform.platform(),
    "repo_root": os.environ["LEWM_REPO_ROOT"],
    "normal_input_root": os.environ.get("NORMAL_INPUT_ROOT", "/kaggle/input/world-of-bugs-normal"),
    "test_input_root": os.environ.get("TEST_INPUT_ROOT", "/kaggle/input/world-of-bugs-test"),
    "split_csv": os.environ.get("SPLIT_CSV", ""),
    "cuda_available": False,
    "gpu_name": None,
    "gpu_compute_capability": None,
    "future_training_gpu_ok": None,
    "locked_test_materialized": False,
    "locked_test_scored": False,
}
try:
    import torch
    payload["cuda_available"] = bool(torch.cuda.is_available())
    if torch.cuda.is_available():
        payload["gpu_name"] = torch.cuda.get_device_name(0)
        major, minor = torch.cuda.get_device_capability(0)
        payload["gpu_compute_capability"] = f"sm_{major}{minor}"
        payload["future_training_gpu_ok"] = major >= 7
except Exception as exc:
    payload["torch_probe_error"] = str(exc)

for env_key in ["repo_root", "normal_input_root", "test_input_root", "split_csv"]:
    if not Path(payload[env_key]).exists():
        raise SystemExit(f"Missing required path: {payload[env_key]}")

Path(os.environ.get("P0_OUTPUT_ROOT", "/kaggle/working/wob_kaggle_native_outputs")).mkdir(parents=True, exist_ok=True)
(Path(os.environ.get("P0_OUTPUT_ROOT", "/kaggle/working/wob_kaggle_native_outputs")) / "preflight.json").write_text(
    json.dumps(payload, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, indent=2))
PY
