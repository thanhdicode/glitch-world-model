# WOB R5 Non-Locked Evaluation Runner

This directory holds the Kaggle-oriented runner for the non-locked `R5-WOB` identical-episode
evaluation stage.

## Scope

This runner is authorized only for:

- non-locked WOB validation evaluation;
- the frozen 72-row manifest in `configs/wob_protocol/wob_expansion_eval_manifest.csv`;
- LeWM seeds42/43/44 plus `frame_diff` and train-normal-fitted `feature_distance`.

It is not authorized for:

- locked test;
- `R5-XGAME`;
- `R6`;
- broad paper claims.

## Required Kaggle Inputs

Attach these official WOB datasets:

- `benedictwilkinsai/world-of-bugs-normal`
- `benedictwilkinsai/world-of-bugs-test`

Attach one extra dataset that contains exactly these six files:

- `wob_seed42_artifacts.tar.gz`
- `wob_seed42_artifacts.tar.gz.sha256`
- `wob_seed43_artifacts.tar.gz`
- `wob_seed43_artifacts.tar.gz.sha256`
- `wob_seed44_artifacts.tar.gz`
- `wob_seed44_artifacts.tar.gz.sha256`

## One Notebook Cell

```bash
%%bash
set -Eeuo pipefail
REPO_URL="https://github.com/thanhdicode/glitch-world-model.git"
REPO_REF="2e0281ee94d6892fee062c1444cc86fe5878c588"
REPO_DIR="/kaggle/working/glitch-world-model"

if [[ -d "$REPO_DIR/.git" ]]; then
  cd "$REPO_DIR"
  git fetch origin
  git checkout "$REPO_REF"
  git reset --hard "$REPO_REF"
else
  git clone "$REPO_URL" "$REPO_DIR"
  cd "$REPO_DIR"
  git checkout "$REPO_REF"
fi

bash cloud/wob_r5_eval/run_kaggle_r5_wob_eval.sh
```

## Expected Outputs

- `/kaggle/working/r5_wob_identical_episode_outputs.tar.gz`
- `/kaggle/working/r5_wob_identical_episode_outputs.tar.gz.sha256`
- `/kaggle/working/r5_wob_identical_episode_failure_debug.tar.gz` only on failure

## Safety Notes

- The runner validates all three seed artifacts before evaluation.
- The frozen readiness manifest must match its recorded SHA256.
- Train rows remain excluded from evaluation.
- Locked rows remain excluded from materialization and scoring.
- No WOB performance claim is allowed until the output bundle passes local validation.
