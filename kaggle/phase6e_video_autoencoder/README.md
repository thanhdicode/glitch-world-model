# Phase 6E Kaggle GPU Launch

This package launches the optional **Conv3D video autoencoder learned baseline** on Kaggle. It is
not LeWorldModel or JEPA integration. Training uses train-normal clips and scores validation only;
locked test remains untouched.

## 1. Prepare The Private Kaggle Dataset

From the repo root, audit the local source package:

```powershell
python scripts\prepare_phase6e_kaggle_dataset.py --dry-run
```

Expected current audit:

- `5,572` manifest clips
- `179,199` files
- approximately `4.734 GiB`
- zero missing clip directories
- test scored: `false`

Create the upload folder only when ready to upload about 4.7 GB:

```powershell
python scripts\prepare_phase6e_kaggle_dataset.py --copy
```

Generated gitignored layout:

```text
outputs/kaggle_phase6e_dataset/
  tempglitch_phase3b/
    manifest.csv
    <source>/clips/<clip_id>/<frames>
  split.csv
  dataset-metadata.template.json
  UPLOAD_README.md
```

Create a **private** Kaggle Dataset from this folder. Replace
`YOUR_KAGGLE_USERNAME` in `dataset-metadata.template.json`. The template uses license `other`
because this repo must not relicense processed TempGlitch data; review the upstream license
before upload.

Recommended CLI upload after authenticating locally without sharing the token:

```powershell
python -m pip install kaggle
kaggle auth login
Copy-Item outputs\kaggle_phase6e_dataset\dataset-metadata.template.json `
  outputs\kaggle_phase6e_dataset\dataset-metadata.json
kaggle datasets create -p outputs\kaggle_phase6e_dataset
```

Do not add `--public`; the dataset must remain private.

## Automated State-Machine Option

The orchestrator defaults to dry-run, saves resumable state under
`outputs/kaggle_phase6e_automation/`, and stops before each live side effect:

```powershell
python scripts\run_phase6e_kaggle_automation.py --dry-run
```

Expected first stop:

- `current_step`: `dataset_upload_approval`
- `requires_approval`: `dataset_upload_approval`
- no dataset upload
- no kernel push

Approvals are one-time and bound to the current fingerprint:

```powershell
python scripts\run_phase6e_kaggle_automation.py --live
python scripts\run_phase6e_kaggle_automation.py --live --approve-step dataset_upload_approval
python scripts\run_phase6e_kaggle_automation.py --live
python scripts\run_phase6e_kaggle_automation.py --live --approve-step kernel_push_approval
python scripts\run_phase6e_kaggle_automation.py --live
```

An approval is consumed immediately when its live action starts. If dataset, kernel, config,
branch, or commit fingerprints change, prior approval is invalidated. Logs are redacted before
being saved under `outputs/kaggle_phase6e_automation/logs/`.

The first `--live` invocation resets any lightweight dry-run package state, prepares and
fingerprints the real upload package, then requests a new live approval. `--live` is
intentionally explicit. Do not use it during implementation verification.

## 2. Create The Kaggle Notebook

1. Create a new Kaggle Notebook.
2. Attach the private Phase 6E Dataset.
3. Open Notebook Settings.
4. Set Accelerator to `GPU T4` or `GPU P100`.
5. Set Internet to `On` so the notebook can clone this GitHub branch.

## 3. Run The Notebook

Open [phase6e_kaggle_cells.md](phase6e_kaggle_cells.md) and run the five cells in order:

1. Clone and install.
2. Verify CUDA.
3. Run protocol dry-run.
4. Train the model and score validation.
5. Verify generated artifacts.

Replace `TEN-DATASET` with the actual Kaggle dataset slug mounted below `/kaggle/input/`.

The dry-run must report:

- Train-normal clips: `1,724`
- Validation clips: `1,071`
- Test clips scored: `False`
- Cross-split pair-suspect groups: `0`

Do not run the training cell if these values differ.

## 4. Expected Outputs

Required files under `/kaggle/working/tempglitch_phase6e/seed_42/`:

- `protocol_audit.json`
- `train_normal_manifest.csv`
- `validation_manifest.csv`
- `video_autoencoder.pt`
- `training_metadata.json`
- `validation_scores.csv`
- `phase6e_summary.json`

Use **Save Version** with outputs enabled, then download the output folder. Keep the checkpoint,
generated manifests, scores, and outputs outside Git.

## 5. Validate Downloaded Artifacts

After downloading the Kaggle output:

```powershell
python scripts\ingest_phase6e_kaggle_artifacts.py `
  --artifact-root C:\path\to\downloaded\seed_42 `
  --output-root outputs\tempglitch_phase6e\seed_42\ingested
```

Strict ingestion requires a CUDA device string, exactly `1,071` validation rows, finite numeric
scores, zero cross-split groups, and both `test_materialized=false` and `test_scored=false`.

Optionally generate validation-only clip metrics:

```powershell
python scripts\ingest_phase6e_kaggle_artifacts.py `
  --artifact-root C:\path\to\downloaded\seed_42 `
  --labels data\processed\tempglitch_phase3b\labels.csv `
  --output-root outputs\tempglitch_phase6e\seed_42\ingested
```

## Prohibited Claims Before Artifact Validation

- Do not claim a Kaggle GPU run exists before downloading and validating real artifacts.
- Do not claim neural AUROC/F1 before validation metrics exist.
- Do not claim locked-test performance; Phase 6E does not score test.
- Do not call this Conv3D learned baseline LeWorldModel, JEPA, or state of the art.
