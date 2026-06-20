#!/usr/bin/env bash
set -euo pipefail

echo "=== Sequential WOB-P1 seeds43/44 robust run ==="
echo "Seed43 starts first. Seed44 starts only after seed43 exits successfully."

bash cloud/wob_p1_seeds43_44/run_kaggle_wob_p1_seed43_robust.sh
bash cloud/wob_p1_seeds43_44/run_kaggle_wob_p1_seed44_robust.sh
