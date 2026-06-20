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
export WOB_OUTPUT_ROOT="${WOB_OUTPUT_ROOT:-/kaggle/working/wob_outputs}"
export WOB_P1_METADATA_ROOT="${WOB_P1_METADATA_ROOT:-/kaggle/working/wob_p1_metadata}"
export WOB_TRAIN_ROOT="${WOB_TRAIN_ROOT:-/kaggle/working/wob_p1_root}"
export WOB_LANCE_ROOT="${WOB_LANCE_ROOT:-/kaggle/working/wob_lance}"
export WOB_SPLIT_CSV="$LEWM_REPO_ROOT/configs/wob_protocol/split.csv"
export WOB_SELECTED_SPLIT_CSV="$WOB_P1_METADATA_ROOT/wob_p1_selected_split.csv"

mkdir -p "$WOB_OUTPUT_ROOT" "$WOB_P1_METADATA_ROOT" "$WOB_TRAIN_ROOT" "$WOB_LANCE_ROOT"

python - <<'PY'
import json
import os
from pathlib import Path

from cloud.wob_kaggle_native.common import detect_kaggle_roots

normal_root, test_root = detect_kaggle_roots(Path(os.environ.get("INPUT_ROOT", "/kaggle/input")))
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

failure() {
  set +e
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
package_artifacts(Path("/kaggle/working/wob_seed42_failure_debug.tar.gz"), roots)
PY
}
trap failure ERR

bash cloud/wob_p1_seed42/setup_runtime.sh
bash cloud/wob_p1_seed42/preflight.sh
bash cloud/wob_p1_seed42/prepare_wob_train_root.sh
bash cloud/wob_p1_seed42/build_wob_lance_train_seed42.sh
bash cloud/wob_p1_seed42/run_wob_seed42_train.sh
bash cloud/wob_p1_seed42/validate_wob_seed42_artifacts.sh

python - <<'PY'
import os
from pathlib import Path

from cloud.wob_p1_seed42.common import package_artifacts

roots = [
    (Path(os.environ["WOB_OUTPUT_ROOT"]) / "wob_seed42", "wob_outputs/wob_seed42"),
    (Path(os.environ["WOB_P1_METADATA_ROOT"]), "wob_p1_metadata"),
]
package_artifacts(Path("/kaggle/working/wob_seed42_artifacts.tar.gz"), roots)
PY
sha256sum /kaggle/working/wob_seed42_artifacts.tar.gz > /kaggle/working/wob_seed42_artifacts.tar.gz.sha256

python - <<'PY'
import json
import os
from pathlib import Path

preflight = json.loads((Path(os.environ["WOB_OUTPUT_ROOT"]) / "wob_seed42" / "preflight_passed.json").read_text(encoding="utf-8"))
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
PY
