# 125 - K3 Kaggle Package Instructions

Date: 2026-06-25
Status: package prepared; ready for user-operated Kaggle K3

## Current State

The repository contains a K3 package surface under:

- `kaggle/k3_sigreg_action_ablation/`

It also contains:

- local input preparation: `scripts/prepare_k3_ablation_inputs.py`
- local post-Kaggle intake: `scripts/ingest_k3_ablation_bundle.py`

The latest local input preparation result is:

- `prepared`

The local K3 dry-run result is:

- `dry_run_ready`

The current package archive is:

- `outputs/k3_kaggle_package/lewm_k3_sigreg_action_ablation_package.zip`
- SHA256:
  `9820c50c1b4196bb66c754adde70e89c6e9916599567765d6857a9d5e35574cc`

## What Is Ready

- K3 package wrapper docs and entrypoint
- prepared R5-XGame train and validation Lance inputs
- deterministic K3 input manifest with dataset hashes
- local 12-variant dry-run matrix
- deterministic post-Kaggle intake validator
- explicit no-claim boundary for pre-K3 state

## Prepared Inputs

- train: `outputs/r5_xgame/_r5_xgame_train_normal.lance`
- validation: `outputs/r5_xgame/_r5_xgame_calibration_eval_normal.lance`
- auxiliary buggy-eval provenance: `outputs/r5_xgame/_r5_xgame_eval_buggy.lance`
- train SHA256: `34ef70fd3e7cb288646b8e5e1fb4f8ae60e9308cddcd2401c8d77c717c076efc`
- validation SHA256: `ecb4c9ef1349b8e1896b783a7ae7b3f6761b2d445370ff814e2cfc179ebbfa19`

## Kaggle Upload Steps

1. Upload `outputs/k3_kaggle_package/lewm_k3_sigreg_action_ablation_package.zip` to Kaggle.
2. In the Kaggle notebook, unzip the archive into the working directory so `kaggle/`, `scripts/`,
   `src/`, and `outputs/r5_xgame/` sit under one root.
3. Run the scientific command below with CUDA enabled.

The Kaggle runner resolves relocated prepared inputs by dataset directory name and verifies the
recorded SHA256 hashes before launching the 12 scientific variants.

## Kaggle Scientific Command

The intended Kaggle scientific command is:

```bash
python kaggle/k3_sigreg_action_ablation/run_k3_ablation.py \
  --input-manifest kaggle/k3_sigreg_action_ablation/k3_input_manifest.json \
  --device cuda \
  --output-root /kaggle/working/r6_sigreg_ablation
```

## Expected Kaggle Outputs

- `r6_ablation_plan.json`
- `r6_controlled_pairs.json`
- `r6_ablation_receipt.json`
- per-variant output directories for all 12 variants

## Post-Kaggle Intake

After the user downloads the Kaggle K3 bundle:

```powershell
python scripts/ingest_k3_ablation_bundle.py ^
  --bundle <downloaded_k3_bundle_or_extracted_dir> ^
  --output-root outputs/k3_ablation_intake
```

## Claim Boundary

Even after package preparation succeeds, the repo must still keep these rules:

- K3 is not scientifically validated until the downloaded output bundle passes local intake.
- No SIGReg or action-conditioning claim is allowed yet.
- Locked test remains closed.
