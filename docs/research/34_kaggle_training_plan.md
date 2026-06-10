# Kaggle Validation-Only Training Plan

## Scope And Current Decision

This plan prepares the next Kaggle GPU experiment without authorizing a live upload, kernel
push, or locked-test run. The first Phase 6E Conv3D run is verified engineering evidence, but
its validation AUROC of `0.403865` does not support improvement. Real LeWorldModel, JEPA, and
SIGReg remain future work.

The next live run, if separately approved, must remain validation-only. Fit data is train-normal
only; validation is used for metrics and configuration decisions; locked test remains
unmaterialized and unscored.

## Local Safety Checks

Run from the repository root:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts\validate_research_release.py --ci
python scripts\check_claim_registry.py
python scripts\run_phase6e_kaggle_automation.py --dry-run
python scripts\prepare_phase6e_kaggle_dataset.py --dry-run
python scripts\run_kaggle_video_autoencoder.py --dry-run
```

Expected protocol facts:

- `1,724` train-normal clips for seed 42.
- `1,071` validation clips.
- zero cross-split pair-suspect groups.
- `test_materialized=false`.
- `test_scored=false`.

## Live Commands Requiring Separate Approval

These commands are documented for reproducibility only. Do not run them without a new,
fingerprint-bound user approval for each live action.

```powershell
python scripts\run_phase6e_kaggle_automation.py --live
python scripts\run_phase6e_kaggle_automation.py --live --approve-step dataset_upload_approval
python scripts\run_phase6e_kaggle_automation.py --live
python scripts\run_phase6e_kaggle_automation.py --live --approve-step kernel_push_approval
python scripts\run_phase6e_kaggle_automation.py --live
```

The private upload package must contain processed clips, `manifest.csv`, and grouped
`split.csv` only. It must not contain credentials, repository secrets, outputs from prior
experiments, checkpoints, or materialized locked-test artifacts.

## Validation Experiment Grid

Start with a small Conv3D grid:

| Field | Values |
| --- | --- |
| image size | `64`, then `96` only if stable |
| clip length | `16` |
| epochs | `10`, `20`, `30` |
| learning rate | `0.001`, `0.0003` |
| batch size | `8` or maximum stable |
| seed | `42`; add `43` and `44` only after runtime is stable |

Every candidate must fit only train-normal clips and score only validation. Record bad results
without filtering them out. If validation AUROC is below `0.5`, inspect label alignment, score
direction, split selection, duplicate groups, frame sampling, and score distributions on
validation only.

## Artifact Handoff And Ingestion

Download required artifacts without committing them, then run:

```powershell
python scripts\ingest_phase6e_kaggle_artifacts.py `
  --artifact-root C:\path\to\downloaded\seed_42 `
  --labels data\processed\tempglitch_phase3b\labels.csv `
  --output-root outputs\tempglitch_phase6e\seed_42\ingested
```

Strict ingestion requires exact validation row counts, finite scores, CUDA metadata, zero
cross-split groups, and both test flags set to false.

## Locked-Test Release Gate

Before any locked-test scoring:

1. Save `docs/research/35_validation_decision.md` with the selected configuration, checkpoint
   and score hashes, limitations, and the exact sentence `Locked test has not been scored yet.`
2. Freeze `selected_protocol_config.json`.
3. Obtain explicit user approval for that exact selected-config SHA-256.
4. Create a gitignored `locked_test_approval.json` containing:

```json
{
  "authorization": "APPROVE LOCKED TEST SCORING",
  "selected_config_sha256": "<exact SHA-256>"
}
```

`scripts/evaluate_tempglitch_locked_test.py` rejects missing, stale, or mismatched approvals.
Test must be scored once with the frozen configuration and threshold only.
