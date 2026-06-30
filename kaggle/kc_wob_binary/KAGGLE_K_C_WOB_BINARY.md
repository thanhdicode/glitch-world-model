# K-C WOB Binary Evaluation Kaggle Runbook

This runbook launches the full non-locked World of Bugs binary validation job for Topic A.
It reuses the staged R5-WOB pipeline but writes K-C-named outputs so the Kaggle notebook is easier
to audit. It does not open or score locked test rows.

## Required Kaggle Inputs

Attach these five datasets before starting a background run:

| Slot | Expected contents |
| --- | --- |
| WOB normal | A dataset root containing `NORMAL-TRAIN/` |
| WOB test | A dataset root containing `TEST/` |
| seed42 artifact | `wob_seed42_artifacts.tar.gz` and `wob_seed42_artifacts.tar.gz.sha256`, or extracted `wob_seed42_artifacts/wob_outputs/wob_seed42/` |
| seed43 artifact | `wob_seed43_artifacts.tar.gz` and `wob_seed43_artifacts.tar.gz.sha256`, or extracted `wob_seed43_artifacts/wob_outputs/wob_seed43/` |
| seed44 artifact | `wob_seed44_artifacts.tar.gz` and `wob_seed44_artifacts.tar.gz.sha256`, or extracted `wob_seed44_artifacts/wob_outputs/wob_seed44/` |

Known working slugs from the previous runbook were:
`phmnhtngha/world-of-bugs-normal`, `phmnhtngha/world-of-bugs-test`,
`phmnhtngha/wob-seed42-artifacts`, `phmnhtngha/wob-seed43-artifacts`,
and `phmnhtngha/wob-seed44-artifacts`. If your Kaggle UI mounts them under
`/kaggle/input/datasets/<owner>/<slug>`, the runner auto-detects that layout.

Use **GPU T4 x2** or better. P100 is not acceptable for the current CUDA/runtime floor.

## Cell 1: Clone Main And Install Runtime

```bash
%%bash
set -euo pipefail

cd /kaggle/working
rm -rf glitch-world-model
git clone --branch main https://github.com/thanhdicode/glitch-world-model.git
cd glitch-world-model

echo "=== repo ==="
git rev-parse HEAD
git log -1 --oneline
python --version

echo "=== install isolated LeWM runtime ==="
python -m pip install -q --no-cache-dir --no-deps \
  "stable-worldmodel==0.1.1" \
  "lancedb==0.30.0" \
  "pylance==4.0.0" \
  "lance-namespace==0.7.7" \
  "lance-namespace-urllib3-client==0.7.7" \
  "loguru==0.7.3" \
  "hydra-core==1.3.3"
python -m pip install -q --no-cache-dir \
  "stable-pretraining==0.1.7" \
  "transformers==4.57.6"
python -m pip install -e . --no-deps -q

python - <<'PY'
from stable_worldmodel.data import LanceDataset, LanceWriter
from hydra._internal.utils import _locate
import glitch_detection
_locate("stable_pretraining.backbone.utils.vit_hf")
print("K-C runtime OK")
PY
```

## Cell 2: Preflight Mounted Inputs

```bash
%%bash
set -euo pipefail

cd /kaggle/working/glitch-world-model
export PYTHONPATH="$PWD/src:$PWD:${PYTHONPATH:-}"

echo "=== /kaggle/input roots ==="
find /kaggle/input -maxdepth 4 -type d | sort | head -200

echo "=== auto-detected K-C inputs ==="
python - <<'PY'
from pathlib import Path
from glitch_detection.wob_kaggle_common import discover_r5_wob_input_overrides

overrides = discover_r5_wob_input_overrides(Path("/kaggle/input"))
for key, value in overrides.items():
    print(f"{key}={value}")
PY
```

Stop here if this cell cannot find both WOB roots and all three seed artifacts. Do not edit the
frozen manifest to force the run.

## Cell 3: Optional Smoke Check

Smoke mode is not paper-valid. It only confirms that discovery, Lance materialization, baselines,
and the three LeWM seeds can execute on a tiny subset.

```bash
%%bash
set -euo pipefail

cd /kaggle/working/glitch-world-model
export PYTHONPATH="$PWD/src:$PWD:${PYTHONPATH:-}"

rm -rf /kaggle/working/kc_wob_binary_smoke
python scripts/run_kc_wob_binary.py \
  --input-root /kaggle/input \
  --output-dir /kaggle/working/kc_wob_binary_smoke \
  --success-tarball /kaggle/working/kc_wob_binary_smoke_outputs.tar.gz \
  --device cuda \
  --baseline-batch-size 4 \
  --lewm-batch-size 2 \
  --n-bootstrap 100 \
  --smoke
```

Expected final status: `kc_wob_binary_smoke_complete`.

## Cell 4: Full Background Run

Run this as the Kaggle background job. Estimated runtime depends on the Kaggle GPU allocation and
input I/O, but the job is resumable through stage markers if the session stops.

```bash
%%bash
set -euo pipefail

cd /kaggle/working/glitch-world-model
export PYTHONPATH="$PWD/src:$PWD:${PYTHONPATH:-}"

rm -rf /kaggle/working/kc_wob_binary
rm -f /kaggle/working/kc_wob_binary_outputs.tar.gz /kaggle/working/kc_wob_binary_outputs.tar.gz.sha256

python scripts/run_kc_wob_binary.py \
  --input-root /kaggle/input \
  --output-dir /kaggle/working/kc_wob_binary \
  --success-tarball /kaggle/working/kc_wob_binary_outputs.tar.gz \
  --device cuda \
  --baseline-batch-size 4 \
  --lewm-batch-size 2 \
  --bootstrap-seed 42 \
  --n-bootstrap 1000
```

If a CUDA OOM occurs in a LeWM seed stage, rerun the same cell with `--lewm-batch-size 1`. Do not
change readiness JSON, eval manifest, split CSV, or seed artifacts.

## Cell 5: Validate And Package Download Bundle

```bash
%%bash
set -euo pipefail

cd /kaggle/working/glitch-world-model
export PYTHONPATH="$PWD/src:$PWD:${PYTHONPATH:-}"

python scripts/validate_kc_wob_binary_output.py \
  --output-dir /kaggle/working/kc_wob_binary \
  --readiness-json configs/wob_protocol/wob_expansion_readiness.json

python scripts/validate_r5_wob_stage_outputs.py \
  --output-dir /kaggle/working/kc_wob_binary

test -f /kaggle/working/kc_wob_binary_outputs.tar.gz
test -f /kaggle/working/kc_wob_binary_outputs.tar.gz.sha256

echo "=== download these two files ==="
ls -lh /kaggle/working/kc_wob_binary_outputs.tar.gz
ls -lh /kaggle/working/kc_wob_binary_outputs.tar.gz.sha256
```

Download both files from the Kaggle Output tab:

- `/kaggle/working/kc_wob_binary_outputs.tar.gz`
- `/kaggle/working/kc_wob_binary_outputs.tar.gz.sha256`

## Local Intake After Download

Run this locally after downloading the two files:

```powershell
python scripts/verify_r5_wob_upload.py `
  --tarball C:\path\to\kc_wob_binary_outputs.tar.gz `
  --sha256-file C:\path\to\kc_wob_binary_outputs.tar.gz.sha256 `
  --extract-dir C:\Users\ADMIN\Downloads\kc_wob_binary_validated
```

Only a `VALID_OUTPUT_BUNDLE` result promotes K-C into verified paper evidence. Until that passes,
K-C remains pending and must not be used as a performance claim.

## Expected Valid Output Files

The success tarball should contain:

- `r5_wob_manifest.csv`
- `episode_scores.csv`
- `baseline_scores.csv`
- `r5_wob_metrics.json`
- `r5_wob_comparison.csv`
- `r5_wob_provenance.json`
- `R5_WOB_REPORT.md`

The validated full run has 12 calibration-normal WOB episodes and 60 evaluation-buggy WOB episodes.
It is non-locked binary evidence, not locked-test evidence and not a cross-game generalization claim
by itself.
