# 125 - K3 Kaggle Package Instructions

Date: 2026-06-25
Status: package skeleton prepared; scientific run blocked until local K3 inputs exist

## Current State

The repository now contains a K3 package surface under:

- `kaggle/k3_sigreg_action_ablation/`

It also contains:

- local input preparation: `scripts/prepare_k3_ablation_inputs.py`
- local post-Kaggle intake: `scripts/ingest_k3_ablation_bundle.py`

However, the latest local input preparation result is still:

- `missing_required_inputs`

So the package is not yet scientifically runnable on Kaggle.

## What Is Ready

- K3 package wrapper docs and entrypoint
- deterministic K3 input contract
- deterministic post-Kaggle intake validator
- explicit no-claim boundary for pre-K3 state

## What Is Missing

Before the user can run Kaggle K3, the local workspace still needs the raw/source R5-XGame
archives required by the frozen manifest:

- `NORMAL-TRAIN/.../*.tar` coverage for train, calibration, and normal-negative rows
- `TEST/.../*.tar` coverage for the 60 buggy-positive rows

The exact missing-file list is written into:

- `outputs/k3_ablation_inputs/k3_input_manifest.json`

## Shortest Deterministic Path To Ready

1. Place the missing R5-XGame raw archives under a clean root that does not contain old
   `R5-WOB` checkpoint/output directories.
2. Rerun:

```powershell
python scripts/prepare_k3_ablation_inputs.py
```

3. Confirm the result switches to:

- status `prepared`
- real paths exist for:
  - `outputs/r5_xgame/_r5_xgame_train_normal.lance`
  - `outputs/r5_xgame/_r5_xgame_calibration_eval_normal.lance`

4. Run the local K3 dry-run:

```powershell
python scripts/run_r6_sigreg_ablation.py ^
  --train-path outputs/r5_xgame/_r5_xgame_train_normal.lance ^
  --validation-path outputs/r5_xgame/_r5_xgame_calibration_eval_normal.lance ^
  --output-root outputs/r6_sigreg_ablation_dryrun ^
  --device cpu ^
  --dry-run
```

5. Package and upload the refreshed K3 surface to Kaggle.

## Kaggle Scientific Command

Once step 3 succeeds, the intended Kaggle scientific command is:

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
