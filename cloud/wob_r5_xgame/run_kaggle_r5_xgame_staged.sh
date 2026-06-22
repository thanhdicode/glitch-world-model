#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="${REPO_DIR:-/kaggle/working/glitch-world-model}"
INPUT_ROOT="${INPUT_ROOT:-/kaggle/input}"
OUTPUT_DIR="${OUTPUT_DIR:-/kaggle/working/r5_xgame}"
MANIFEST="${MANIFEST:-${REPO_DIR}/configs/wob_protocol/r5_xgame_split.csv}"
LOG_PATH="${LOG_PATH:-/kaggle/working/r5_xgame_staged.log}"

cd "$REPO_DIR"

export PYTHONPATH="$REPO_DIR/src:$REPO_DIR:${PYTHONPATH:-}"

exec > >(tee -a "$LOG_PATH") 2>&1

echo "=== R5-XGame staged Kaggle run ==="
date -u +"timestamp_utc=%Y-%m-%dT%H:%M:%SZ"
echo "repo=$REPO_DIR"
echo "input_root=$INPUT_ROOT"
echo "output_dir=$OUTPUT_DIR"
git rev-parse HEAD
python --version

if find "$INPUT_ROOT" -maxdepth 3 \( -iname '*r5_wob*' -o -iname '*wob_seed*artifacts*' -o -iname '*checkpoint*' \) | grep -q .; then
  echo "ERROR: Refusing old R5-WOB/checkpoint-looking mounted inputs."
  exit 2
fi

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
    import glitch_detection.r5_xgame_live  # noqa: F401
    import glitch_detection.lewm_data  # noqa: F401

    print("  glitch_detection R5-XGame runner modules: OK")
except Exception as exc:  # noqa: BLE001
    errors.append(f"glitch_detection: {exc}")

if errors:
    print("\nIMPORT_VERIFICATION_FAILED:")
    for err in errors:
        print(f"  !! {err}")
    sys.exit(1)
print("\nIMPORT_VERIFICATION: ALL OK")
PYCHECK

mkdir -p "$OUTPUT_DIR"

python scripts/audit_r5_xgame_split.py \
  --manifest "$MANIFEST" \
  --output "${OUTPUT_DIR}/r5_xgame_leakage_audit.json"

python scripts/run_r5_xgame_staged.py \
  --manifest "$MANIFEST" \
  --input-root "$INPUT_ROOT" \
  --output-dir "$OUTPUT_DIR" \
  --stage preflight

for stage in materialize baseline_score train_lewm lewm_score aggregate_episode calibrate_thresholds evaluate_binary bootstrap_ci package validate_package; do
  echo "=== R5-XGame stage: ${stage} ==="
  python scripts/run_r5_xgame_staged.py \
    --manifest "$MANIFEST" \
    --input-root "$INPUT_ROOT" \
    --output-dir "$OUTPUT_DIR" \
    --stage "$stage" \
    --device cuda \
    --seeds 42 43 44
done

python scripts/validate_r5_xgame_output_bundle.py \
  --output-dir "$OUTPUT_DIR" \
  --frozen-manifest "$MANIFEST"

echo "=== R5-XGame staged run complete ==="
echo "Download these files:"
echo "  ${OUTPUT_DIR}/r5_xgame_outputs.tar.gz"
echo "  ${OUTPUT_DIR}/r5_xgame_outputs.tar.gz.sha256"
echo "  ${LOG_PATH}"
