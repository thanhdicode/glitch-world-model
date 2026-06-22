# R5-XGame Kaggle Live Runbook

## UI Setup

1. Open a Kaggle notebook with GPU enabled.
2. Attach `benedictwilkinsai/world-of-bugs-normal`.
3. Attach `benedictwilkinsai/world-of-bugs-test`.
4. Do not attach old R5-WOB seed artifacts, checkpoints, output bundles, locked-test data, or any
   private credential files.

## Command

```bash
cd /kaggle/working/glitch-world-model
bash cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh
```

The script validates the frozen manifest, runs preflight, materializes only the 120 non-locked
manifest rows, trains fresh seed42/43/44 checkpoints from the 36 train-normal rows, scores
calibration plus held-out evaluation rows, computes binary metrics, packages outputs, writes a
SHA256 sidecar, and validates the bundle.

## Expected Outputs

Download these files after success:

- `/kaggle/working/r5_xgame/r5_xgame_outputs.tar.gz`
- `/kaggle/working/r5_xgame/r5_xgame_outputs.tar.gz.sha256`
- `/kaggle/working/r5_xgame_staged.log`

Do not upload raw videos, Lance datasets, checkpoints, cache folders, `.env`, `kaggle.json`, or
credentials back into the repository.

## Failure Triage

- Missing input: attach the two required WOB datasets or set `NORMAL_INPUT_ROOT` and
  `TEST_INPUT_ROOT`; do not edit the frozen manifest.
- Old checkpoint/R5-WOB input refusal: remove the unsafe mounted dataset and rerun from scratch.
- OOM or timeout: return the full Kaggle log and stage marker files; do not reuse partial metrics.
- Validation failure: download the log plus output directory listing; treat the bundle as invalid
  until `scripts/validate_r5_xgame_output_bundle.py` passes locally.

## What To Send Back

Send the tarball, SHA256 sidecar, and Kaggle log. Metrics are not claim-ready until local intake
validates the downloaded bundle.
