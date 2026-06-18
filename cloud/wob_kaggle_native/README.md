# WOB Kaggle-Native Pipeline

This package prepares a Kaggle-native `WOB-P0` audit path using the official Kaggle datasets as
mounted notebook inputs. It does not require a 63 GiB local download and must not be used to
upload local WOB tar files back to Kaggle.

## Official Kaggle Inputs

Attach these Kaggle datasets to the notebook:

- `benedictwilkinsai/world-of-bugs-normal`
- `benedictwilkinsai/world-of-bugs-test`

The repository split metadata still governs which rows are allowed. Rows marked `split=test` in
`outputs/gate3/world_of_bugs/split.csv` remain locked and must stay excluded.

## Human Steps

1. Create a Kaggle Notebook.
2. Add the official datasets:
   - `benedictwilkinsai/world-of-bugs-normal`
   - `benedictwilkinsai/world-of-bugs-test`
3. Do not upload 63 GiB from local storage.
4. Use CPU for `WOB-P0` audit; use T4 or newer for any future training phase.
5. Do not use P100 for future LeWM WOB training if the preflight requires `sm_70+`.
6. Clone or upload this repository at the intended commit.
7. Run:

```bash
export LEWM_REPO_ROOT=/kaggle/working/glitch-world-model
export NORMAL_INPUT_ROOT=/kaggle/input/world-of-bugs-normal
export TEST_INPUT_ROOT=/kaggle/input/world-of-bugs-test
cd "$LEWM_REPO_ROOT"
bash cloud/wob_kaggle_native/setup_runtime.sh
bash cloud/wob_kaggle_native/preflight.sh
bash cloud/wob_kaggle_native/prepare_wob_root.sh
bash cloud/wob_kaggle_native/run_wob_p0_audit.sh
```

8. Download only generated manifests and audit reports from `/kaggle/working`.
9. Do not run `WOB-P1` training until a human explicitly authorizes it after the Kaggle-native
   `WOB-P0` pass.

## Outputs

- `/kaggle/working/wob_root`
- `/kaggle/working/wob_kaggle_native_outputs`
- `/kaggle/working/wob_p0_materialization_audit`

## Phase Behavior

- `WOB-P0`: `prepare_wob_root.sh` defaults to `WOB_PHASE=p0_full_nonlocked`, which selects all
  non-locked rows only.
- `WOB-P1` future-only prep: set `WOB_PHASE=p1_train_only` to build a train-normal plus
  validation-normal root without validation-buggy rows.
