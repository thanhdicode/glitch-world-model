# Package Fix Report

## Old Failure

- `output_dir` intake passed, but `r5_xgame_outputs.tar.gz` intake failed.
- Root cause: the package step wrote `stage_package.json` after the tarball snapshot was already
  sealed, so the downloaded bundle extracted without that required stage marker.
- `stage_validate_package.json` only proved `/kaggle/working/r5_xgame` was valid; it did not prove
  the tarball itself re-extracted into a validator-clean directory.

## Fix

- `scripts/run_r5_xgame_staged.py` now defines the extracted-tarball contract explicitly:
  `PACKAGE_OUTPUT_NAMES + PACKAGE_STAGE_MARKER_NAMES`.
- The package step now builds a `stage_package.json` snapshot first, injects that snapshot into the
  tarball, and only then writes the same marker to `output_dir`.
- The current package contract treats `stage_package.json` as a stage marker rather than the
  authoritative source for the repaired tarball SHA, so future snapshots do not need
  self-referential tarball hashes.
- `run_validate_package()` now validates both the live `output_dir` and the tarball/sidecar pair.

## Reconciliation Note

- The downloaded repaired bundle is intake-valid, but its existing `stage_package.json` still
  carries legacy tarball/hash fields from the earlier packaging path.
- Those legacy fields still reference the old tarball SHA
  `05d298c29904142d9e28db97e485db80b8b68eb56b520450594936593970fbd2`.
- The authoritative repaired tarball hash remains the tarball plus `.sha256` sidecar pair:
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`.
- The validator now compares normalized manifest content rather than raw line-ending bytes, so the
  checked-in frozen manifest remains authoritative across LF/CRLF checkouts.

## Rebuilt Tarball

- Repaired bundle path:
  `C:\Users\ADMIN\Downloads\results (1)\r5_xgame\r5_xgame_outputs.tar.gz`
- Old SHA256:
  `05d298c29904142d9e28db97e485db80b8b68eb56b520450594936593970fbd2`
- New SHA256:
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`
- Sidecar recomputed:
  `C:\Users\ADMIN\Downloads\results (1)\r5_xgame\r5_xgame_outputs.tar.gz.sha256`

## Tar Listing

The rebuilt tarball contains the required 21 top-level members:

- Outputs:
  `r5_xgame_manifest.csv`, `r5_xgame_window_manifest.csv`, `r5_xgame_baseline_scores.csv`,
  `r5_xgame_lewm_scores_seed42.csv`, `r5_xgame_lewm_scores_seed43.csv`,
  `r5_xgame_lewm_scores_seed44.csv`, `r5_xgame_episode_scores.csv`,
  `r5_xgame_comparison.csv`, `r5_xgame_metrics.json`, `R5_XGAME_REPORT.md`,
  `r5_xgame_provenance.json`
- Stage markers:
  `stage_preflight.json`, `stage_materialize.json`, `stage_baseline_score.json`,
  `stage_train_lewm.json`, `stage_lewm_score.json`, `stage_aggregate_episode.json`,
  `stage_calibrate_thresholds.json`, `stage_evaluate_binary.json`,
  `stage_bootstrap_ci.json`, `stage_package.json`

## Validator Result

- `python scripts/validate_r5_xgame_output_bundle.py --tarball ... --sha256-file ...`
  returned `status = r5_xgame_tarball_validated`
- Extracted validator status:
  `r5_xgame_output_validated`
- Manifest SHA256:
  `caf14819f347342d13165db6129e4b12f7cf6bf99e78d1b96ba4b9ea02ecb999`
- Metrics SHA256:
  `6ec94af80a40eeff718aefa285be870694eeadeaaefa6624babe3a5ee84f8474`
