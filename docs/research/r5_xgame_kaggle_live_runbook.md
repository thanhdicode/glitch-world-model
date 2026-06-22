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

The script is self-contained: before running any stage it installs the isolated LeWM runtime
(`stable-worldmodel==0.1.1`, `lancedb==0.30.0`, `pylance==4.0.0`, `lance-namespace`, `loguru`,
`hydra-core` with `--no-deps`, then `stable-pretraining==0.1.7` + `transformers==4.57.6` with full
dependencies, then the repo as an editable install). It then verifies the runtime imports cleanly
(`stable_worldmodel.data`, the `stable_pretraining` Hydra target, `lightning`, and the R5-XGame
runner modules) and exits immediately with a clear message if anything is missing — so a missing
dependency surfaces in seconds rather than after the materialize stage. A plain `pip install -e .`
is **not** sufficient; without this runtime the materialize stage fails with
`ModuleNotFoundError: No module named 'stable_worldmodel'`.

After the runtime is verified, the script validates the frozen manifest, runs preflight,
materializes only the 120 non-locked manifest rows, trains fresh seed42/43/44 checkpoints from the
36 train-normal rows, scores calibration plus held-out evaluation rows, computes binary metrics,
packages outputs, writes a SHA256 sidecar, and validates the bundle.

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
