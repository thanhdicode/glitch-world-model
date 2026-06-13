#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"

cd "$LEWM_REPO_ROOT"
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install \
  stable-worldmodel==0.1.1 \
  stable-pretraining==0.1.7 \
  transformers==4.57.6

python - <<'PY'
import json
import sys

try:
    import torch
    payload = {
        "python": sys.version,
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
    }
except Exception as exc:
    payload = {"python": sys.version, "torch_import_error": str(exc)}
print(json.dumps(payload, indent=2))
PY
