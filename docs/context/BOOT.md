# BOOT.md - Fast Start Context For Agents

Generated: 2026-06-24T12:05:00+00:00
Commit: `d475724e49acbd024daed3f2b4dfe9c1ba071c33`

## Read Order
1. `RULES.md`
2. `AGENTS.md`
3. `docs/context/BOOT.md`
4. `docs/context/PROJECT_STATE.md`
5. `docs/context/NEXT_ACTION.md`
6. `docs/context/LAST_HANDOFF.md`
7. `docs/context/TASK_ROUTER.md`

Only open `PLAYBOOK.md` for roadmap, paper, claim, gate-status, or ambiguous tasks, or when the
context cache is stale. Use `docs/context/REPO_MAP.md` before broad repo searches.
The current execution roadmap is `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Current Status
- Gates 1-4 passed at engineering/smoke level.
- Gate 5 passed strict Kaggle CUDA/resume artifact validation.
- Gate 6 v8 completed normal-only CUDA training and passed strict checkpoint/reload/encoding
  validation with locked-test flags false.
- Gates 7-9 completed a validation-only, non-locked evidence lane on canonical TempGlitch support.
- A separate non-locked research MVP source is ready with 36 train-normal, 14 validation-normal,
  and 22 validation-buggy episodes across all five categories.
- The exact 500-update research-MVP GPU profile completed as engineering evidence only.
- R4 rerun seed43/44 training artifacts are local SHA256-verified and pass per-seed validators.
- The pair-disjoint TempGlitch follow-up is validator-backed on 2 calibration-normal, 12
  evaluation normal-negative, and 22 evaluation buggy-positive episodes with zero cross-role
  source, pair, and episode overlap.
- K1 learned-baseline Kaggle intake is now validator-backed locally for `video_autoencoder`,
  `cnn_lstm`, and `video_transformer` on the exact currently cited TempGlitch follow-up support,
  with false locked-test materialized/scored flags.
- The strongest K1 learned baseline is the bounded `cnn_lstm` row at AUROC `0.613636`; the best
  recorded LeWM row on the same support remains higher at AUROC `0.715909`, while the intervals
  overlap and the comparison stays non-locked and split-bounded.
- Local `WOB-P0` remains blocked on missing tar files, the Kaggle-native `WOB-P0` pass is
  verified from the downloaded evidence bundle, and WOB-P1 seed42/seed43/seed44 training
  artifact verification is complete.
- `R5-WOB` is validated as a positive-probe bundle, and `R5-XGame` compute is intake-validated
  for both the live output directory and the repaired tarball/sidecar bundle.
- Roadmap V4 is canonical and keeps the Topic-A upgrade lane open while preserving the anti-
  overclaim and locked-test rules.
- Gate 10 is closed.
- Locked test is closed.

## Immediate Next Task
- Execute roadmap V4 Phase P3 local preparation for the GlitchBench benchmark.
- Freeze the K2 public-benchmark packaging, validator, and claim boundary before any Kaggle K2
  launch.
- Keep K1 learned-baseline wording bounded to the validated TempGlitch support and stop before the
  user-operated K2 gate.

## Safety
- Non-locked-test Kaggle actions use standing Kaggle authorization after security, license,
  protocol, and package validation.
- Fingerprints are audit/idempotency records, not approval artifacts.
- Locked-test materialization or scoring requires a separate direct user command.
- No locked-test materialization or scoring.
- No data, output, checkpoint, Lance dataset, cache, `.env`, token, or `kaggle.json` commits.
- No new performance, superiority, SIGReg-benefit, action-benefit, cross-game, temporal-
  localization, SOTA, or neural locked-test claim may appear until a supporting artifact is
  validated.
- No broad WOB/R5-XGame detection-performance, cross-game, action-conditioning, or
  SIGReg-benefit claim outside the exact qualified non-locked bundles.

## Required Checks
```powershell
python scripts/update_context_cache.py --refresh-boot
python scripts/validate_context_cache.py
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
pre-commit run --all-files
```

## Fast Workflow
- Start with the context files and task router.
- Open only the files named by the router plus files discovered with targeted `rg`.
- Update `docs/context/LAST_HANDOFF.md` after each task.
- Regenerate context cache before final verification.
- Treat `PLAYBOOK.md` as the long-form source of truth, not the default first read for every
  routine code edit.
