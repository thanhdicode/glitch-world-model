#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="${REPO_DIR:-/kaggle/working/glitch-world-model}"
INPUT_ROOT="${INPUT_ROOT:-/kaggle/input}"
OUTPUT_DIR="${OUTPUT_DIR:-/kaggle/working/r5_xgame}"
MANIFEST="${MANIFEST:-${REPO_DIR}/configs/wob_protocol/r5_xgame_split.csv}"
LOG_PATH="${LOG_PATH:-/kaggle/working/r5_xgame_staged.log}"

cd "$REPO_DIR"

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
