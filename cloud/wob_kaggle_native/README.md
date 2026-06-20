# WOB Kaggle-Native Pipeline

This package prepares a Kaggle-native `WOB-P0` audit path using the official Kaggle datasets as
mounted notebook inputs. It does not require a 63 GiB local download and must not be used to
upload local WOB tar files back to Kaggle.

## Official Kaggle Inputs

Attach these Kaggle datasets to the notebook:

- `benedictwilkinsai/world-of-bugs-normal`
- `benedictwilkinsai/world-of-bugs-test`

The repository split metadata still governs which rows are allowed. Rows marked `split=test` in
`configs/wob_protocol/split.csv` remain locked and must stay excluded.

## Human Steps

1. Create a Kaggle Notebook.
2. Add the official datasets:
   - `World of Bugs - Train`
   - `World of Bugs - Test`
3. Do not upload 63 GiB from local storage.
4. CPU is enough for `WOB-P0`; T4 or newer is only for a future training phase.
5. Do not use P100 for future LeWM WOB training if the preflight requires `sm_70+`.
6. Run this single cell:

```bash
%%bash
set -Eeuo pipefail
REPO_URL="https://github.com/thanhdicode/glitch-world-model.git"
REPO_REF="main"
REPO_DIR="/kaggle/working/glitch-world-model"
rm -rf "$REPO_DIR"
git clone "$REPO_URL" "$REPO_DIR"
cd "$REPO_DIR"
git checkout "$REPO_REF"
bash cloud/wob_kaggle_native/run_kaggle_wob_p0_all.sh
```

7. Download only generated manifests and audit reports from `/kaggle/working`.
8. If the script fails, download `wob_p0_kaggle_failure_debug.tar.gz` and send it back.
9. Do not run `WOB-P1` training until a human explicitly authorizes it after the Kaggle-native
   `WOB-P0` pass.

## Outputs

- `/kaggle/working/wob_root`
- `/kaggle/working/wob_kaggle_native_outputs`
- `/kaggle/working/wob_p0_materialization_audit`
- `/kaggle/working/wob_p0_kaggle_audit_outputs.tar.gz`
- `/kaggle/working/wob_p0_kaggle_failure_debug.tar.gz` on failure

## Phase Behavior

- `WOB-P0`: `prepare_wob_root.sh` defaults to `WOB_PHASE=p0_full_nonlocked`, which selects all
  non-locked rows only.
- `WOB-P1` future-only prep: set `WOB_PHASE=p1_train_only` to build a train-normal plus
  validation-normal root without validation-buggy rows.
