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

## Recommended Notebook Cell

```bash
%%bash
set -Eeuo pipefail
REPO_URL="https://github.com/thanhdicode/glitch-world-model.git"
REPO_REF="<use-the-commit-sha-from-the-staged-retry-branch>"
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

export R5_WOB_BASELINE_BATCH_SIZE=4
export R5_WOB_LEWM_BATCH_SIZE=2
export R5_WOB_DEVICE=cuda

bash cloud/wob_r5_eval/run_kaggle_r5_wob_staged.sh
```

## Expected Outputs

- `/kaggle/working/r5_wob_identical_episode_outputs.tar.gz`
- `/kaggle/working/r5_wob_identical_episode_outputs.tar.gz.sha256`
- `/kaggle/working/r5_wob_identical_episode_failure_debug.tar.gz` only on failure
- `/kaggle/working/r5_wob_identical_episode_failure_debug.tar.gz.sha256` only on failure
- `/kaggle/working/r5_wob_staged.log`

## Safety Notes

- The runner validates all three seed artifacts before evaluation.
- The runner detects Kaggle dataset mounts and repacks auto-extracted seed-artifact folders when
  needed.
- The frozen readiness manifest must match its recorded SHA256.
- Train rows remain excluded from evaluation.
- Locked rows remain excluded from materialization and scoring.
- No WOB performance claim is allowed until the output bundle passes local validation.
- The staged runner is resumable within the same Kaggle session through per-stage markers.

## Stages

The staged path runs these phases:

1. `preflight`
2. `materialize_lance`
3. `baseline_scores`
4. `lewm_seed42`
5. `lewm_seed43`
6. `lewm_seed44`
7. `aggregate_metrics`
8. `validate_package`

Each stage writes a `stage_<name>.json` marker inside the output directory. Re-running the same
cell in the same Kaggle session will skip completed stages whose hashes still validate.

Before `preflight`, the staged runner now prints the exact discovered `NORMAL_INPUT_ROOT`,
`TEST_INPUT_ROOT`, and per-seed artifact locations so silent Kaggle mount discovery stalls are
fail-fast and observable.

## Optional Smoke Mode

For end-to-end sanity checking only:

```bash
export R5_WOB_SMOKE=1
bash cloud/wob_r5_eval/run_kaggle_r5_wob_staged.sh
```

Smoke mode limits the workload to a tiny subset, writes `smoke=true` into stage markers and
metrics, and does not produce a package-valid output tarball.

## Legacy Runner

`run_kaggle_r5_wob_eval.sh` is retained only as a historical monolithic entrypoint for forensic
comparison. New Kaggle retries should use `run_kaggle_r5_wob_staged.sh`.
