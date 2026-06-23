# 94 - R5-XGame Intake Reconciliation

Date: 2026-06-23

## Scope

This note records the Phase 0 preflight reconciliation required before `R6 Scientific Evidence
Upgrade`. It does not describe a new scientific run, does not retrain LeWM, does not launch
Kaggle, and does not open locked test.

## Current Repository State

- Git commit during reconciliation:
  `6993964547348659cb2f8882f0a84347f765e200`
- Working tree at preflight start:
  clean
- Docs claiming package intake complete:
  - `docs/context/PROJECT_STATE.md`
  - `docs/context/NEXT_ACTION.md`
  - `docs/context/LAST_HANDOFF.md`
  - `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md`
  - `docs/research/93_r5_xgame_validated_bundle_summary.md`
  - `PACKAGE_FIX_REPORT.md`

## Frozen Manifest Contract

Checked against:

- `configs/wob_protocol/r5_xgame_split.csv`
- downloaded bundle manifest:
  `C:\Users\ADMIN\Downloads\results (1)\r5_xgame\r5_xgame_manifest.csv`

Verified counts remain:

- `train_normal=36`
- `calibration_normal=12`
- `evaluation_normal_negative=12`
- `evaluation_buggy_positive=60`

Verified safety flags remain:

- no `split=test` rows
- no `locked_test` role rows
- zero cross-role overlap by `episode_id`
- zero cross-role overlap by `pair_id`
- zero cross-role overlap by `source`
- `validation_buggy_used_for_fit_select=false`
- `locked_test_materialized=false`
- `locked_test_scored=false`

## Original Preflight Divergence

Observed before the validator reconciliation:

| Check | Result before fix | Why |
| --- | --- | --- |
| output dir + checked-in manifest | fail | validator required raw file SHA equality |
| tarball + checked-in manifest | fail | same raw-SHA requirement |
| output dir + artifact-local manifest | pass | raw SHA matched artifact-local copy |
| tarball + artifact-local manifest | pass | raw SHA matched extracted artifact-local copy |

The checked-in and bundled manifests are logically identical as CSV rows, but not byte-identical.

## Manifest Hash Evidence

Raw SHA256 values:

- checked-in manifest:
  `4f4b0ca5fe6e7ea207dd5a8f4ec97a0d00af486a109d2f215e9c83880c89182c`
- bundle manifest:
  `caf14819f347342d13165db6129e4b12f7cf6bf99e78d1b96ba4b9ea02ecb999`

Normalized manifest SHA256 values after CSV parse plus LF-normalized rewrite:

- checked-in manifest:
  `caf14819f347342d13165db6129e4b12f7cf6bf99e78d1b96ba4b9ea02ecb999`
- bundle manifest:
  `caf14819f347342d13165db6129e4b12f7cf6bf99e78d1b96ba4b9ea02ecb999`

Row-level comparison result:

- `rows_equal=true`
- checked-in rows: `120`
- bundle rows: `120`

## Line Ending Evidence

`git ls-files --eol configs/wob_protocol/r5_xgame_split.csv` reports:

- index: `i/lf`
- working tree: `w/crlf`

Byte-level file inspection reports:

- checked-in working-tree manifest:
  CRLF line endings, size `17976`
- bundle manifest:
  LF line endings, size `17855`

Conclusion:

- the original failure was a cross-platform line-ending mismatch, not split-content drift

## Stage Package Evidence

The downloaded live output directory and the tarball both contain `stage_package.json`, which
keeps the tarball extract intake-valid.

However, the downloaded marker still records legacy tarball metadata:

- legacy tarball SHA recorded in `stage_package.json`:
  `05d298c29904142d9e28db97e485db80b8b68eb56b520450594936593970fbd2`
- repaired sidecar SHA:
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`

This stale SHA is a legacy package receipt detail, not the authoritative repaired bundle hash.
The authoritative repaired tarball hash remains the `.sha256` sidecar plus direct tarball hashing.

## Contract Decision

The authoritative intake contract is now:

1. The checked-in frozen manifest content remains authoritative.
2. Manifest validation is based on normalized CSV content equality, not raw line-ending bytes.
3. The repaired tarball SHA is taken from the tarball plus sidecar pair, not from legacy fields in
   `stage_package.json`.
4. `stage_package.json` is required as a package-stage marker, but legacy tarball/hash fields in
   older downloaded bundles are informational only.
5. `stage_validate_package.json` in the current downloaded output should be interpreted as a
   live-output validation receipt only; the tarball-green state is established by the repaired
   local validator run.

## Post-Reconciliation Preflight Result

With the validator updated to compare normalized manifest content:

| Check | Result after fix |
| --- | --- |
| output dir + checked-in manifest | pass |
| tarball + checked-in manifest | pass |
| output dir + artifact-local manifest | pass |
| tarball + artifact-local manifest | pass |

Validated output-dir result now reports:

- `manifest_raw_sha256_match=false`
- `manifest_normalized_sha256_match=true`
- `stage_package_marker.stale_legacy_tarball_sha256=true`

Validated tarball result now reports:

- bundle SHA256 verified as
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`
- extracted output manifest normalized match:
  `true`

## Conclusion

`R5-XGame` intake is now mutually consistent enough to proceed to `R6 Scientific Evidence Upgrade`
without retraining or relaunching Kaggle.

The remaining caveat is documentation-level only:

- the current downloaded `stage_package.json` still contains legacy old-SHA fields

That caveat is now explicitly documented and is no longer treated as the authoritative repaired
bundle hash source.
