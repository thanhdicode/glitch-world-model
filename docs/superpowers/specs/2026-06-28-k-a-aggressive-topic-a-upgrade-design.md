# K-A Aggressive Topic A Upgrade Design

Date: 2026-06-28

## Objective

Upgrade the project from a cautious Topic A method-paper scaffold into the strongest
validation-only LeWM-Glitch paper package that can be defended for FISAT:

- keep the paper centered on "Latent World Models for Video Game Glitch Detection: A
  JEPA-based Approach";
- make R5-XGame and TempGlitch the two primary evidence families;
- run K-B while preparing K-A immediately;
- widen TempGlitch support enough for narrower confidence intervals;
- preserve all locked-test, leakage, credential, and artifact boundaries.

Aggressive means spending compute and engineering effort. It does not mean weakening
claim discipline.

## Current Evidence

The repository has already pivoted materially toward Topic A:

- `paper/main.tex` has the Topic A title and LeWM-Glitch abstract.
- `scripts/run_r5_xgame_staged.py` and `src/glitch_detection/r5_xgame_live.py` provide
  the R5-XGame staged protocol.
- `src/glitch_detection/r5_tempglitch_eval.py` provides TempGlitch R5 scoring,
  episode aggregation, calibration-normal thresholding, bootstrap CIs, and locked-test
  path rejection.
- `scripts/build_tempglitch_expanded_normal_inputs.py` provides a K-A expanded input
  builder.
- significance and table-generation utilities exist for paper integration.

The remaining gap is not the story. The gap is making K-A truly expanded-support and
making the paper wording match only validated evidence.

## Known Issues To Fix Before K-A Run

### K-A support target mismatch

`scripts/build_tempglitch_expanded_normal_inputs.py` currently defaults to
`--limit-per-group 8` and documents it as targeting at least 30 normal evaluation
episodes. With the current `freeze_tempglitch_split` defaults
(`validation_ratio=0.2`, `test_ratio=0.2`), this does not hold.

Observed split behavior with five categories:

- `limit_per_group=8`: about 10 validation-normal episodes.
- `limit_per_group=10`: about 10 validation-normal episodes.
- `limit_per_group=12`: about 10 validation-normal episodes.
- `limit_per_group=30`: about 30 validation-normal episodes.
- `limit_per_group=35`: about 35 validation-normal episodes, leaving at least 30
  normal-negative evaluation episodes after four calibration normals.

The builder must target validation/evaluation support directly, not just downloaded
normal count.

### Follow-up validator is not fully exposed

`validate_tempglitch_followup_output` supports `expected_support`, but
`scripts/run_tempglitch_followup_pair_disjoint.py` does not expose it. The follow-up
path also has frozen calibration episode IDs and expected counts wired around the
historical support.

K-A expanded support needs parameterized support and calibration handling while keeping
the historical default unchanged.

### Paper wording hazards

`paper/sections/08_results.tex` still contains TODO comments referring to
"R5-XGame locked-test". Locked test remains closed. Any final paper text must say
"non-locked" or "validation-only" and must not imply final benchmark, broad
generalization, SOTA, SIGReg benefit, or action-conditioning benefit.

The "first JEPA" wording should be softened unless a focused literature audit supports
the priority claim.

## Chosen Strategy: B Aggressive

Implement K-A readiness immediately while K-B is still running.

### Track 1: K-A code/runbook repair

1. Add explicit K-A target support controls to the builder:
   - target validation-normal count, default 34;
   - target validation-buggy count, default 34 or matched available support;
   - fail-closed if the materialized support is below target unless an override is
     explicitly provided;
   - write actual train, calibration, evaluation-normal, and evaluation-buggy counts
     to the summary JSON.

2. Keep the existing historical R5/TempGlitch defaults intact:
   - no behavior drift for the old frozen follow-up;
   - expanded mode is opt-in through the K-A builder/runbook path.

3. Parameterize the follow-up path:
   - expose expected support through CLI;
   - support expanded calibration IDs or calibration count derived from the manifest;
   - preserve locked-test rejection and role-overlap validation;
   - add tests for both historical support and expanded support.

4. Update K-A runbook:
   - replace `--limit-per-group 8/10/12` guidance with target-support guidance;
   - state expected runtime and support acceptance conditions;
   - prefer Path A using existing TempGlitch seed42/43/44 checkpoints when local
     provenance matches;
   - keep Path B retrain as backup.

### Track 2: K-B intake while K-A is prepared

1. When notebook output arrives:
   - validate R5-XGame bundle;
   - compute/verify CI and DeLong/significance tables;
   - compare best LeWM row against frame_diff and feature_distance baselines;
   - record exact seed, scorer, aggregation, AUROC, AUPRC, F1, FPR@95TPR, CI, and p.

2. Paper wording rule:
   - if p < 0.05 and CI supports it, use split-bounded significant wording;
   - otherwise use "best recorded row is higher, but significance remains pending or
     not confirmed."

### Track 3: Paper upgrade after K-A/K-B results

1. Make TempGlitch and R5-XGame co-primary:
   - TempGlitch: multi-category same-source support, stronger external relevance;
   - R5-XGame: strongest binary AUROC result, positive-heavy caveat visible.

2. Refresh tables:
   - dataset inventory;
   - main results;
   - significance;
   - limitations and claim boundary;
   - reviewer-risk table.

3. Harden claims:
   - no locked-test result;
   - no SOTA;
   - no broad cross-game generalization;
   - no deployment-readiness claim;
   - no temporal-localization claim;
   - no unsupported "first" claim unless literature audit is documented.

4. Regenerate paper and run claim audit.

## Acceptance Criteria

K-A readiness is complete when:

- expanded inputs report enough validation-normal support to leave at least 30
  normal-negative evaluation episodes after calibration, or explicitly document the
  maximum public support reached;
- follow-up output validator checks the expanded support tuple;
- role overlap is zero;
- locked-test flags remain false;
- support, hashes, and command provenance are written.

K-B intake is complete when:

- the bundle validates locally;
- the significance output is reproducible;
- paper tables use only validated bundle outputs;
- no remote notebook logs are treated as final evidence without local validation.

Paper upgrade is complete when:

- all TODO-KA/TODO-KB placeholders are resolved or downgraded safely;
- claim registry and context cache are synchronized;
- required commands pass or failures are reported honestly;
- the final text frames LeWM-Glitch as a method contribution backed by two bounded
  evidence families.

## Verification Plan

Focused checks after K-A edits:

```powershell
python -m pytest tests/test_build_tempglitch_expanded_normal_inputs.py
python -m pytest tests/test_tempglitch_followup.py
python -m pytest tests/test_compute_significance_table.py
python -m ruff check scripts/build_tempglitch_expanded_normal_inputs.py scripts/run_tempglitch_followup_pair_disjoint.py src/glitch_detection/tempglitch_followup.py
python -m ruff format --check scripts/build_tempglitch_expanded_normal_inputs.py scripts/run_tempglitch_followup_pair_disjoint.py src/glitch_detection/tempglitch_followup.py
```

Full checks before final paper handoff:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
python scripts/validate_context_cache.py
```

## Decision

Proceed with Strategy B after user approval of this design:

1. repair K-A expanded support controls now;
2. prepare K-A Kaggle run path while K-B continues;
3. ingest K-B results as soon as available;
4. run K-A;
5. upgrade paper only from validated outputs.
