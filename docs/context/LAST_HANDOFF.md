# LAST_HANDOFF.md

Last completed task: R5-XGame live runner, Kaggle package, and output validator implementation
Commit: pending task commit
Date: 2026-06-23

## What Changed

- Replaced the preflight-only `scripts/run_r5_xgame_staged.py` with a real staged R5-XGame runner:
  `preflight`, `materialize`, `baseline_score`, `train_lewm`, `lewm_score`,
  `aggregate_episode`, `calibrate_thresholds`, `evaluate_binary`, `bootstrap_ci`, `package`, and
  `validate_package`.
- The runner uses the frozen 120-row non-locked manifest, materializes only the four allowed roles,
  trains fresh seed42/43/44 LeWM artifacts on the 36 `train_normal` rows through the real
  `LeWMTrainConfig` / `train_lewm` API, calibrates thresholds only on the 12
  `calibration_normal` rows, and evaluates only the 12 normal-negative + 60 buggy-positive held-out
  rows.
- Fresh R5-XGame training now uses a 15,000-update research target with validation/checkpoint
  intervals and early stopping; old R5-WOB checkpoint or seed-artifact mounts are refused.
- Added `scripts/validate_r5_xgame_output_bundle.py` support for output-directory and downloaded
  tarball + SHA256 validation, including exact role counts, both evaluation classes, required
  metrics, required stage markers, false locked-test flags, and old-checkpoint-reuse rejection.
- Added Kaggle live operator script `cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh`.
- Updated R5-XGame operator docs, postrun intake template, required Kaggle inputs, implementation
  report, and stale docs that previously said no live scorer existed.
- Registered claim C-081 as tooling readiness only.
- Hardened `capture_resource_usage()` with a Windows-safe `tracemalloc` fallback when neither
  `psutil` nor Unix `resource` is available.

## Safety Status

- No local heavy training, Kaggle execution, materialization, checkpoint loading, or scoring was run.
- No raw data, Lance datasets, checkpoints, output bundles, caches, credentials, or `attached_assets`
  were added.
- Locked test remains closed, unmaterialized, and unscored.
- No R5-XGame performance, cross-game generalization, action-conditioning, superiority, SIGReg,
  temporal-localization, or locked-test claim was added.

## Checks Passed

- `python -m pytest tests/test_r5_xgame_live.py tests/test_r5_xgame_runner.py tests/test_validate_r5_xgame_output_bundle.py tests/test_r5_xgame_protocol.py tests/test_r5_xgame_metrics.py tests/test_lewm_lance_eval.py tests/test_r5_wob_stage.py`
- R5-XGame dry-run preflight with a deliberately missing local input root and a temporary ignored
  output directory; it reported all WOB tar inputs missing and did not materialize data.
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python scripts/validate_research_release.py --ci`
- `python scripts/check_claim_registry.py`
- `python scripts/doctor.py`
- `python scripts/validate_context_cache.py`

## Checks With Known Failure

- Full `python -m pytest` is still red only for the pre-existing Phase 6E docs gap:
  `tests/test_phase6e_kaggle_docs.py` expects
  `kaggle/phase6e_video_autoencoder/phase6e_kaggle_cells.md`, which remains absent.
  Current result after the telemetry fix: 497 passed, 2 failed.

## Gate Status After Task

- R5-XGame: Kaggle operation package is ready for a human operator, but no run has occurred and no
  metric is validated.
- R5-WOB: prior validated intake remains separate from this task.
- R6 and locked test: still closed under their existing prerequisites.

## Open Blockers

- R5-XGame still needs a human-operated Kaggle run with mounted WOB normal/test datasets.
- R5-XGame metrics remain unavailable until the downloaded tarball and SHA256 sidecar pass local
  intake validation.
- Full repo `pytest` still has the unrelated Phase 6E missing-doc failure.

## Next Recommended Task

1. Open Kaggle with GPU enabled.
2. Attach `benedictwilkinsai/world-of-bugs-normal` and `benedictwilkinsai/world-of-bugs-test`.
3. Run:

   ```bash
   cd /kaggle/working/glitch-world-model
   bash cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh
   ```

4. Download `r5_xgame_outputs.tar.gz`, `r5_xgame_outputs.tar.gz.sha256`, and the Kaggle log.
5. Run local intake:

   ```powershell
   python scripts/validate_r5_xgame_output_bundle.py `
     --tarball <download-dir>\r5_xgame_outputs.tar.gz `
     --sha256-file <download-dir>\r5_xgame_outputs.tar.gz.sha256 `
     --frozen-manifest configs\wob_protocol\r5_xgame_split.csv
   ```

## Files Likely Relevant Next

- `scripts/run_r5_xgame_staged.py`
- `scripts/validate_r5_xgame_output_bundle.py`
- `cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh`
- `docs/research/r5_xgame_kaggle_live_runbook.md`
- `docs/research/r5_xgame_postrun_intake_template.md`
- `configs/wob_protocol/r5_xgame_split.csv`
