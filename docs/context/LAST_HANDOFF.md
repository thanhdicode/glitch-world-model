# LAST_HANDOFF.md

Last completed task: Phase P2 learned-baseline local preparation
Commit: `940b8d60bb036934ebceeb8f2ca2cc910e65011a`
Date: 2026-06-24T08:42:16+00:00

## What Changed

- Added `src/glitch_detection/cnn_lstm.py` with an optional CNN-LSTM next-frame baseline that
  mirrors the video autoencoder train/score interface.
- Added `src/glitch_detection/video_transformer.py` with an optional VideoMAE-small
  feature-distance baseline and checkpointed train/score flow.
- Registered the new learned baselines in `src/glitch_detection/score_clips.py`.
- Added `scripts/run_kaggle_learned_baselines.py` and
  `scripts/validate_learned_baselines.py` for the shared K1 train/score/validate path.
- Added CPU-mock coverage for the new baselines and the unified runner.

## Checks Passed

- `python -m pytest`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python scripts/validate_research_release.py --ci`
- `python scripts/check_claim_registry.py`
- `python scripts/doctor.py`
- `python scripts/validate_context_cache.py`

## Safety Status

- No Kaggle launch, retraining run, or downloaded evidence claim was performed in this task.
- New paper-facing learned-baseline claims stay blocked until K1 artifacts are validated.
- No locked-test access.
- No data/output/checkpoint/cache/credential commit intended.

## Gate Status After Task

- Gates 1-8 passed; Gate 9 remains a bounded pilot and R5 follow-up evidence remains bounded.
- Gate 10 remains closed.
- Phase P2 local preparation is complete; K1 is the next external gate.
- Locked test remains closed.

## Open Blockers

- K1 still requires a user-operated Kaggle run plus local validator-backed artifact intake.
- Phase P3-P5 evidence is still missing: public benchmark scoring, controlled ablations, and
  temporal-localization scope/results.
- Official-kit compile remains a later P7 packaging blocker.

## Next Recommended Task

- Run Kaggle gate K1 with the frozen follow-up manifest/split and the new learned-baseline
  runner, then validate the downloaded artifact directory locally.

## Files Likely Relevant Next

- `src/glitch_detection/video_autoencoder.py`
- `src/glitch_detection/cnn_lstm.py`
- `src/glitch_detection/video_transformer.py`
- `scripts/run_kaggle_learned_baselines.py`
- `scripts/validate_learned_baselines.py`
- `tests/test_cnn_lstm.py`
- `tests/test_video_transformer.py`
- `tests/test_learned_baselines_runner.py`
