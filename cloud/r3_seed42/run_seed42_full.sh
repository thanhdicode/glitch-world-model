#!/usr/bin/env bash
set -euo pipefail

export LEWM_SEED=42
exec bash cloud/r3_seed42/run_seed_full.sh
