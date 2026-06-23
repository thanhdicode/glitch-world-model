# 100 - TempGlitch Evidence Upgrade Checklist

Date: 2026-06-24

## Scope

This checklist governs the next bounded non-locked TempGlitch follow-up defined in
`docs/research/99_tempglitch_followup_protocol.md`.

It is a pre-execution checklist only. It does not authorize Kaggle, retraining, locked-test
access, or new benchmark downloads.

## Pre-Run Checks

- Confirm `git status --short` is clean or that unrelated changes are intentionally isolated.
- Confirm the authoritative `R5` TempGlitch artifacts are present:
  - `outputs/research_mvp/datasets/tempglitch_train_normal_all_local.lance`
  - `outputs/research_mvp/datasets/tempglitch_validation_normal_all_local.lance`
  - `outputs/research_mvp/datasets/tempglitch_validation_buggy_all_local.lance`
  - `outputs/r5_tempglitch_identical_episode/r5_manifest.csv`
  - `outputs/r5_tempglitch_identical_episode/baseline_scores.csv`
  - `outputs/r5_tempglitch_identical_episode/lewm_scores_seed42.csv`
  - `outputs/r5_tempglitch_identical_episode/lewm_scores_seed43.csv`
  - `outputs/r5_tempglitch_identical_episode/lewm_scores_seed44.csv`
  - `outputs/r5_tempglitch_identical_episode/r5_metrics.json`
  - `outputs/r5_tempglitch_identical_episode/r5_provenance.json`
- Confirm `validation_buggy_used_for_fit_select=false`.
- Confirm `locked_test_materialized=false`.
- Confirm `locked_test_scored=false`.
- Confirm the follow-up calibration freeze remains pair-disjoint:
  - `Godot_Blinking_Normal_106`
  - `Godot_Frozen_Animation_Platformer_Normal_107`
- Confirm the follow-up evaluation support remains non-empty and two-class:
  - `12` normal-negative evaluation episodes
  - `22` buggy-positive evaluation episodes

## Required Input Files

| File | Required | Purpose |
| --- | --- | --- |
| `outputs/research_mvp/datasets/tempglitch_train_normal_all_local.lance` | yes | Train-only fit inventory for train-dependent methods. |
| `outputs/research_mvp/datasets/tempglitch_validation_normal_all_local.lance` | yes | Source of calibration-normal and evaluation-normal follow-up rows. |
| `outputs/research_mvp/datasets/tempglitch_validation_buggy_all_local.lance` | yes | Source of evaluation buggy-positive follow-up rows. |
| `outputs/r5_tempglitch_identical_episode/r5_manifest.csv` | yes | Authoritative starting manifest and window universe. |
| `outputs/r5_tempglitch_identical_episode/baseline_scores.csv` | yes | Raw baseline score input. |
| `outputs/r5_tempglitch_identical_episode/lewm_scores_seed42.csv` | yes | Raw LeWM score input. |
| `outputs/r5_tempglitch_identical_episode/lewm_scores_seed43.csv` | yes | Raw LeWM score input. |
| `outputs/r5_tempglitch_identical_episode/lewm_scores_seed44.csv` | yes | Raw LeWM score input. |
| `outputs/r5_tempglitch_identical_episode/r5_metrics.json` | yes | Existing verified receipt and score hashes. |
| `outputs/r5_tempglitch_identical_episode/r5_provenance.json` | yes | Existing seed-artifact and environment provenance. |
| `outputs/r5_tempglitch_identical_episode/R5_REPORT.md` | recommended | Human-readable cross-check of the current bounded family. |
| `outputs/tempglitch_phase6d/` | optional background only | Historical grouped-split context; not the main evidence source. |

## Required Output Files

- `outputs/tempglitch_followup_pair_disjoint/followup_manifest.csv`
- `outputs/tempglitch_followup_pair_disjoint/followup_manifest.sha256`
- `outputs/tempglitch_followup_pair_disjoint/followup_episode_scores.csv`
- `outputs/tempglitch_followup_pair_disjoint/followup_comparison.csv`
- `outputs/tempglitch_followup_pair_disjoint/followup_metrics.json`
- `outputs/tempglitch_followup_pair_disjoint/followup_provenance.json`
- `outputs/tempglitch_followup_pair_disjoint/FOLLOWUP_REPORT.md`
- `outputs/tempglitch_followup_pair_disjoint/followup_command.txt`
- `outputs/tempglitch_followup_pair_disjoint/followup_validator_receipt.json`

## Validation Commands

Existing cheap checks to run before or alongside implementation:

```powershell
git status --short
python -m pytest tests/test_r5_tempglitch_eval.py
python -m pytest tests/test_experiment_protocol.py tests/test_repeated_eval.py
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
python scripts/validate_context_cache.py
pre-commit run --all-files
```

Required implementation follow-up:

- add a cheap dedicated validator or receipt generator for the new output directory
- recommended command shape:

```powershell
python scripts/validate_tempglitch_followup.py --output-dir outputs/tempglitch_followup_pair_disjoint
```

Status of that command today:

- `TBD / must be added with the follow-up implementation`

## Failure Conditions

- Any required input file is missing.
- Any raw score file no longer matches the hash recorded in `r5_metrics.json` or
  `r5_provenance.json`.
- Any compared row fails manifest alignment.
- Any compared row uses different calibration episodes or different evaluation support counts.
- Any role overlap appears by `source`, `source_episode_id`, or `pair_id`.
- The evaluation slice becomes one-class.
- Any required metric field is absent.
- Any path or flag indicates locked-test access.
- Any method would require fitting on buggy data or using evaluation data for threshold selection.

## Claim-Safety Checks

- Keep the wording bounded to the frozen follow-up split.
- State that the follow-up is non-locked.
- State that the follow-up is built from existing validated `R5` artifacts only.
- Do not mention SOTA, broad superiority, SIGReg benefit, temporal localization, cross-game
  generalization, or locked-test performance.
- Do not reuse Phase 6D locked-test-style outputs as if they were the new authoritative result.

## Paper-Readiness Impact

Positive impact if completed:

- adds a cleaner public-benchmark follow-up than the current positive-heavy `R5-XGame` lane
- upgrades TempGlitch reporting with full support counts and richer metric coverage
- documents pair-disjoint calibration and a validator-backed provenance receipt

What still remains blocked even after a successful follow-up:

- locked-test claims
- temporal-localization claims
- broad generalization claims
- SOTA or superiority claims outside the frozen follow-up split

## Stop Conditions

Stop and hand off instead of running the follow-up if:

- TempGlitch artifacts are missing or inconsistent.
- Existing manifests cannot be verified from the authoritative `R5` receipts.
- The pair-disjoint calibration freeze cannot be reproduced.
- No clean train/calibration/evaluation split can be maintained.
- Metrics would become one-class or leakage-prone.
- Any required step would need locked-test access.
- Any proposed claim would depend on unverified data.
