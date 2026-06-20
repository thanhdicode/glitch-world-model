#!/usr/bin/env bash
# WOB controlled-expansion evaluation-readiness gate.
#
# This gate is a LOCAL CPU metadata-freeze: it needs no GPU and no Kaggle run. The script simply
# re-runs the freeze + validation. If the verified WOB-P1 seed42 artifact tarball happens to be
# mounted (e.g. on Kaggle), set WOB_SEED42_TARBALL and WOB_SEED42_SHA256 to additionally
# re-verify it with the existing seed42 artifact validator. Nothing here opens WOB evaluation,
# seed43/44 training, or the locked test.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_DIR}"

echo "[wob-expansion] freezing seed42 non-locked evaluation-readiness bundle"
python scripts/prepare_wob_expansion_readiness.py

echo "[wob-expansion] validating readiness gate"
python scripts/validate_wob_expansion_readiness.py

if [[ -n "${WOB_SEED42_TARBALL:-}" && -n "${WOB_SEED42_SHA256:-}" ]]; then
  echo "[wob-expansion] optional: re-verifying mounted seed42 artifact tarball"
  python scripts/validate_wob_seed42_artifacts.py \
    --tarball "${WOB_SEED42_TARBALL}" \
    --sha256 "${WOB_SEED42_SHA256}" \
    --expected-seed 42 \
    --expected-target-updates 15000
else
  echo "[wob-expansion] seed42 tarball not mounted; skipping optional artifact re-verification"
fi

echo "[wob-expansion] readiness gate complete"
