#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="${LEWM_REPO_ROOT:-$(pwd)}"
if [[ ! -f "$REPO_ROOT/pyproject.toml" ]]; then
  if [[ -f "$(pwd)/pyproject.toml" ]]; then
    REPO_ROOT="$(pwd)"
  else
    echo "Could not resolve LEWM_REPO_ROOT; run from the repository root or export LEWM_REPO_ROOT." >&2
    exit 1
  fi
fi
export LEWM_REPO_ROOT="$REPO_ROOT"
cd "$LEWM_REPO_ROOT"

INPUT_ROOT="${INPUT_ROOT:-/kaggle/input}"
export WOB_PHASE="${WOB_PHASE:-p0_full_nonlocked}"
export WOB_ROOT_OUTPUT="${WOB_ROOT_OUTPUT:-/kaggle/working/wob_root}"
export P0_OUTPUT_ROOT="${P0_OUTPUT_ROOT:-/kaggle/working/wob_kaggle_native_outputs}"
export AUDIT_OUTPUT_ROOT="${AUDIT_OUTPUT_ROOT:-/kaggle/working/wob_p0_materialization_audit}"

DETECTION_JSON="$P0_OUTPUT_ROOT/detected_inputs.json"
export DETECTION_JSON
mkdir -p "$P0_OUTPUT_ROOT" "$AUDIT_OUTPUT_ROOT"

python - <<'PY'
import json
import os
from pathlib import Path
from cloud.wob_kaggle_native.common import detect_kaggle_roots, resolve_split_csv

repo_root = Path(os.environ["LEWM_REPO_ROOT"])
input_root = Path(os.environ.get("INPUT_ROOT", "/kaggle/input"))
normal_root, test_root = detect_kaggle_roots(input_root)
split_csv = resolve_split_csv(repo_root)
payload = {
    "normal_input_root": str(normal_root),
    "test_input_root": str(test_root),
    "split_csv": str(split_csv),
    "phase": os.environ["WOB_PHASE"],
    "wob_root_output": os.environ["WOB_ROOT_OUTPUT"],
    "p0_output_root": os.environ["P0_OUTPUT_ROOT"],
    "audit_output_root": os.environ["AUDIT_OUTPUT_ROOT"],
}
Path(os.environ["P0_OUTPUT_ROOT"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["DETECTION_JSON"]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
PY

export NORMAL_INPUT_ROOT="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["DETECTION_JSON"]).read_text(encoding="utf-8"))
print(payload["normal_input_root"])
PY
)"
export TEST_INPUT_ROOT="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["DETECTION_JSON"]).read_text(encoding="utf-8"))
print(payload["test_input_root"])
PY
)"
export SPLIT_CSV="$(python - <<'PY'
import json, os
from pathlib import Path
payload = json.loads(Path(os.environ["DETECTION_JSON"]).read_text(encoding="utf-8"))
print(payload["split_csv"])
PY
)"
export PROTOCOL_AUDIT_PATH="$LEWM_REPO_ROOT/configs/wob_protocol/protocol_audit.json"
export SPLIT_AUDIT_PATH="$LEWM_REPO_ROOT/configs/wob_protocol/split.audit.json"

echo "Detected NORMAL_INPUT_ROOT=$NORMAL_INPUT_ROOT"
echo "Detected TEST_INPUT_ROOT=$TEST_INPUT_ROOT"
echo "Using SPLIT_CSV=$SPLIT_CSV"
echo "Selected WOB_PHASE=$WOB_PHASE"
echo "WOB_ROOT_OUTPUT=$WOB_ROOT_OUTPUT"
echo "P0_OUTPUT_ROOT=$P0_OUTPUT_ROOT"
echo "AUDIT_OUTPUT_ROOT=$AUDIT_OUTPUT_ROOT"

failure() {
  set +e
  python - <<'PY'
import os
from pathlib import Path
from cloud.wob_kaggle_native.common import write_debug_tarball

roots = []
for env_name, prefix in [
    ("P0_OUTPUT_ROOT", "wob_kaggle_native_outputs"),
    ("AUDIT_OUTPUT_ROOT", "wob_p0_materialization_audit"),
]:
    root = Path(os.environ.get(env_name, ""))
    if root:
        roots.append((root, prefix))
write_debug_tarball(Path("/kaggle/working/wob_p0_kaggle_failure_debug.tar.gz"), roots)
PY
  if [[ -f /kaggle/working/wob_p0_kaggle_failure_debug.tar.gz ]]; then
    sha256sum /kaggle/working/wob_p0_kaggle_failure_debug.tar.gz > /kaggle/working/wob_p0_kaggle_failure_debug.tar.gz.sha256
  fi
}
trap failure ERR

cd "$LEWM_REPO_ROOT"
bash cloud/wob_kaggle_native/setup_runtime.sh
bash cloud/wob_kaggle_native/preflight.sh
bash cloud/wob_kaggle_native/prepare_wob_root.sh
bash cloud/wob_kaggle_native/run_wob_p0_audit.sh

python - <<'PY'
import os
from pathlib import Path
from cloud.wob_kaggle_native.common import write_debug_tarball

roots = []
for env_name, prefix in [
    ("P0_OUTPUT_ROOT", "wob_kaggle_native_outputs"),
    ("AUDIT_OUTPUT_ROOT", "wob_p0_materialization_audit"),
]:
    root = Path(os.environ[env_name])
    roots.append((root, prefix))
write_debug_tarball(Path("/kaggle/working/wob_p0_kaggle_audit_outputs.tar.gz"), roots)
PY
sha256sum /kaggle/working/wob_p0_kaggle_audit_outputs.tar.gz > /kaggle/working/wob_p0_kaggle_audit_outputs.tar.gz.sha256

if [[ -f "$AUDIT_OUTPUT_ROOT/wob_p0_audit.json" ]]; then
  python - <<'PY'
import json
import os
from pathlib import Path
report = json.loads((Path(os.environ["AUDIT_OUTPUT_ROOT"]) / "wob_p0_audit.json").read_text(encoding="utf-8"))
print(f"Final audit status: {report.get('status')}")
PY
fi
