# LAST_HANDOFF.md

Last completed task: Diagnose and harden K-C/WOB scorer schema after Kaggle Fix #3 failure
Commit: `5be9ede79fde67c04390b68af05c71cc558f097d`
Date: 2026-07-01T00:00:00+07:00

## What Changed

- Diagnosed the Kaggle Fix #3 Version 4 failure as a scorer-schema mismatch: K-C/WOB LeWM score
  CSVs emit `mse_t*` and `l2_t*` fields but not `cosine_gap_t*`, while the aggregation path tried
  to evaluate every scorer in `LEWM_WINDOW_SCORERS`.
- Replaced the previous neutral `0.0` cosine-gap fallback with schema-aware scorer selection:
  unavailable scorers are omitted with explicit `missing_required_score_fields` metadata rather
  than reported as fake constant metrics.
- Added `available_lewm_window_scorers`, `omitted_lewm_window_scorers`, and
  `lewm_window_scorer_schema` helpers in `src/glitch_detection/r5_tempglitch_eval.py`.
- Updated TempGlitch, WOB non-staged, K-C/WOB staged, and R5-XGame staged aggregation paths to
  aggregate only available LeWM window scorers and fail if no usable LeWM scorer exists.
- Added scorer-schema metadata to WOB/K-C metrics, provenance, stage markers, and seed outputs.
- Added regression tests proving missing cosine-gap fields are omitted, present cosine-gap fields
  are still evaluated, and R5-XGame does not synthesize cosine-gap rows from WOB-style score CSVs.

## Checks Passed

- `python -m pytest`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python scripts/check_claim_registry.py`
- `python scripts/validate_research_release.py --ci`
- `python scripts/doctor.py`
- `python scripts/update_context_cache.py --refresh-boot`
- `python scripts/validate_context_cache.py`
- `pre-commit run --all-files`

## Safety Status

- No GPU training, Kaggle launch, window rescoring, locked-test materialization, or locked-test
  scoring was performed.
- No K-C/WOB binary result is claimed yet; the next Kaggle run must use the updated commit and its
  downloaded tarball plus SHA sidecar must pass local intake before any result claim.
- The change improves artifact honesty: K-C/WOB outputs should report only real emitted LeWM
  scorers and explicitly document omitted cosine-gap scorer families.
- Output artifacts, checkpoints, Lance datasets, caches, credentials, and Kaggle files remain
  uncommitted.
- The existing `_kaggle_upload/` directory remains untracked and uncommitted.

## Gate Status After Task

- K-C/WOB binary remains pending until a successful Kaggle run is downloaded and validated.
- Locked test remains closed.
- Current next gate remains evidence-safe paper revision plus K-C intake-preparation.

## Open Blockers

- K-C output cannot be claimed until `kc_wob_binary_outputs.tar.gz` plus `.sha256` are downloaded
  and pass local intake.
- The next Kaggle cell must checkout/use a commit containing the schema-aware scorer fix; rerunning
  commit `77623fb` will reproduce the old `KeyError: 'cosine_gap_t1'`.
- Any paper wording must avoid treating omitted cosine-gap scorer families as evaluated metrics.

## Next Recommended Task

- Commit/push the schema-aware scorer fix.
- Rerun the K-C WOB binary Kaggle job from the new commit.
- If Kaggle succeeds, download `kc_wob_binary_outputs.tar.gz` and `.sha256`, then run local intake
  validation before updating any claim registry or paper text.

## Files Likely Relevant Next

- `src/glitch_detection/r5_tempglitch_eval.py`
- `src/glitch_detection/r5_wob_staged.py`
- `scripts/run_r5_xgame_staged.py`
- `tests/test_r5_tempglitch_eval.py`
- `tests/test_r5_xgame_runner.py`
- `scripts/validate_kc_wob_binary_output.py`
- `kaggle/kc_wob_binary/KAGGLE_K_C_WOB_BINARY.md`
