# LAST_HANDOFF.md

Last completed task: Fix R5-WOB baseline_scores stage — calibration episode count mismatch
Commit: `4f0b755239bcc8f5cd23c1352cd0c1c927573e1b`
Date: 2026-06-20

## What Changed

- Fixed `scripts/run_gate8_baselines_from_lance.py`:
  - Added constant `_WOB_CALIBRATION_EPISODE_COUNT = 12` (WOB expansion protocol has 12 unique
    calibration_normal episodes, not the default 2 used for TempGlitch).
  - Changed `validate_manifest_rows(manifest_rows)` to
    `validate_manifest_rows(manifest_rows, expected_calibration_episode_count=_WOB_CALIBRATION_EPISODE_COUNT)`.

## Root Cause Analysis (from Kaggle log)

Stage 1 (preflight) and Stage 2 (materialize_lance) both passed cleanly.
Stage 3 (baseline_scores) failed with:

```
ValueError: Canonical Gate 7 manifest has an invalid calibration episode count: 12.
```

The `validate_manifest_rows()` function in `lewm_lance_eval.py` has
`expected_calibration_episode_count: int = 2` as its default — correct for the TempGlitch
protocol but wrong for WOB expansion. The WOB expansion eval manifest has:
- 72 total rows
- 12 `calibration_normal` episodes (unique `source_episode_id` values)
- 60 `evaluation_buggy` episodes

The call site in `run_gate8_baselines_from_lance.py` used the bare default and triggered the
mismatch.

## Checks Passed

- Full test suite: 505 pass, 0 new failures.
- Ruff check: clean.
- Context cache validation: passes.
- Research release CI validator: passes.

## Safety Status

- No locked test touched.
- No WOB ablation A7–A11 claim made.
- No fabricated metric or placeholder added.
- Fix is structural (wrong constant), not a protocol or data change.

## Gate Status After Task

- R5-WOB: AWAITING_KAGGLE_RERUN — fix committed, Kaggle retry required on latest `main`.
- All other gates unchanged.

## Open Blockers

- Kaggle notebook must be rerun on the latest `main` commit so the fix is picked up.
- R5 TempGlitch output directory not present locally (needed for R6 A1–A4 execution).
- R5-XGAME and WOB ablations A7–A11 still blocked on validated R5-WOB evidence.

## Next Recommended Task

**Rerun the Kaggle R5-WOB staged notebook on latest `main`.** The fix is a one-line change
at the call site. If Stage 3 passes, continue through Stages 4–7 (LEWM scores, threshold,
eval, pack). On success run `scripts/verify_r5_wob_upload.py` with the output tarball.

```bash
# After downloading the success tarball + .sha256 sidecar:
python scripts/verify_r5_wob_upload.py \
    --tarball r5_wob_identical_episode_outputs.tar.gz \
    --sha256  r5_wob_identical_episode_outputs.tar.gz.sha256
```

## Files Likely Relevant Next

- `scripts/run_gate8_baselines_from_lance.py` (patched)
- `src/glitch_detection/lewm_lance_eval.py` (validate_manifest_rows signature)
- `src/glitch_detection/r5_wob_staged.py` (Stage 3 caller)
- `scripts/verify_r5_wob_upload.py`
- `docs/context/NEXT_ACTION.md`
