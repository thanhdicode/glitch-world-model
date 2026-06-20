# WOB-P1 Seed42 Kaggle Runner

This package prepares the first controlled World of Bugs training phase:
`WOB-P1` seed42, real-action, train-normal only for fitting and validation-normal only for
checkpoint selection.

It must not be run until a human explicitly authorizes WOB training after reviewing the completed
Kaggle-native `WOB-P0` audit evidence.

## Official Kaggle Inputs

Attach these Kaggle datasets to the notebook:

- `benedictwilkinsai/world-of-bugs-normal`
- `benedictwilkinsai/world-of-bugs-test`

The runner filters the frozen tracked split metadata down to:

- 48 train-normal rows
- 12 validation-normal rows

It excludes:

- all validation-buggy rows
- all locked-test rows

## One Kaggle Cell

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
bash cloud/wob_p1_seed42/run_kaggle_wob_p1_seed42_all.sh
```

## Expected Outputs

- `/kaggle/working/wob_outputs/wob_seed42/`
- `/kaggle/working/wob_seed42_artifacts.tar.gz`
- `/kaggle/working/wob_seed42_artifacts.tar.gz.sha256`
- `/kaggle/working/wob_seed42_failure_debug.tar.gz` on failure

## Safety Notes

- Seed42 only.
- Real-action mode only.
- Validation-buggy must stay excluded from fit and checkpoint selection.
- Locked test must stay closed.
- Do not run seed43/44 yet.
- Do not run WOB evaluation yet.
