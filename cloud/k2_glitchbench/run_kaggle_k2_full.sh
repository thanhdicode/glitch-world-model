#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="${REPO_DIR:-/kaggle/working/glitch-world-model}"
MANIFEST="${MANIFEST:-/kaggle/input/lewm-k2-glitchbench-inputs/combined_manifest.csv}"
SPLIT="${SPLIT:-/kaggle/input/lewm-k2-glitchbench-inputs/grouped_split.csv}"
CLIPS_ROOT="${CLIPS_ROOT:-/kaggle/input/lewm-k2-glitchbench-inputs/clips_root}"
LEWM_ROOT="${LEWM_ROOT:-/kaggle/input/lewm-k2-lewm-seed-artifacts}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/kaggle/working/glitchbench_k2}"
LOG_PATH="${LOG_PATH:-/kaggle/working/glitchbench_k2_full.log}"

cd "$REPO_DIR"

export PYTHONPATH="$REPO_DIR/src:$REPO_DIR:${PYTHONPATH:-}"

exec > >(tee -a "$LOG_PATH") 2>&1

echo "=== K2 GlitchBench full Kaggle run ==="
date -u +"timestamp_utc=%Y-%m-%dT%H:%M:%SZ"
echo "repo=$REPO_DIR"
echo "manifest=$MANIFEST"
echo "split=$SPLIT"
echo "clips_root=$CLIPS_ROOT"
echo "lewm_root=$LEWM_ROOT"
echo "output_root=$OUTPUT_ROOT"
git rev-parse HEAD
python --version

echo "=== Install isolated LeWM runtime ==="
python -m pip install -q --no-cache-dir --no-deps \
  "stable-worldmodel==0.1.1" \
  "lancedb==0.30.0" \
  "pylance==4.0.0" \
  "lance-namespace==0.7.7" \
  "lance-namespace-urllib3-client==0.7.7" \
  "loguru==0.7.3" \
  "hydra-core==1.3.3"
python -m pip install -q --no-cache-dir "stable-pretraining==0.1.7" "transformers==4.57.6"
python -m pip install -e "$REPO_DIR" --no-deps -q

echo "=== Verify runtime imports (fail fast) ==="
python - <<'PYCHECK'
import sys

errors = []

try:
    from stable_worldmodel.data import LanceDataset, LanceWriter  # noqa: F401
    print("  stable_worldmodel.data: OK")
except Exception as exc:  # noqa: BLE001
    errors.append(f"stable_worldmodel.data: {exc}")

try:
    from hydra._internal.utils import _locate

    _locate("stable_pretraining.backbone.utils.vit_hf")
    print("  hydra/stable_pretraining: OK")
except Exception as exc:  # noqa: BLE001
    errors.append(f"hydra/stable_pretraining: {exc}")

try:
    import lightning  # noqa: F401

    print("  lightning: OK")
except Exception as exc:  # noqa: BLE001
    errors.append(f"lightning: {exc}")

try:
    import glitch_detection.lewm_adapter  # noqa: F401
    import glitch_detection.lewm_surprise  # noqa: F401

    print("  glitch_detection K2 runner modules: OK")
except Exception as exc:  # noqa: BLE001
    errors.append(f"glitch_detection: {exc}")

if errors:
    print("\nIMPORT_VERIFICATION_FAILED:")
    for err in errors:
        print(f"  !! {err}")
    sys.exit(1)
print("\nIMPORT_VERIFICATION: ALL OK")
PYCHECK

mkdir -p "$OUTPUT_ROOT"

python scripts/run_kaggle_glitchbench_benchmark.py \
  --manifest "$MANIFEST" \
  --split "$SPLIT" \
  --clips-root "$CLIPS_ROOT" \
  --output-root "$OUTPUT_ROOT" \
  --device cuda \
  --lewm-seed-artifact-root "$LEWM_ROOT"

echo "=== K2 GlitchBench run complete ==="
echo "Download these files:"
echo "  ${OUTPUT_ROOT}"
echo "  ${LOG_PATH}"
