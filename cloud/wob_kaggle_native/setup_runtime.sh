#!/usr/bin/env bash
set -euo pipefail

: "${LEWM_REPO_ROOT:?Set LEWM_REPO_ROOT to the cloned repository path.}"

cd "$LEWM_REPO_ROOT"
python -m pip install --upgrade pip
python -m pip install -e .
