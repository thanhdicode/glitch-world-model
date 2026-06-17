# R5 TempGlitch Identical-Episode Results

Date: 2026-06-17

Status: completed, non-locked, validation-only

## Scope

This note records the completed Phase R5 TempGlitch identical-episode evaluation bundle. The
bundle is limited to the non-locked research MVP Lance inventories and does not materialize or
score locked test. Window and transition outputs are diagnostic only; episode/video metrics are the
primary reporting unit.

## Inputs

| Input | Path | SHA256 / fingerprint | Notes |
| --- | --- | --- | --- |
| Train-normal Lance | `outputs/research_mvp/datasets/tempglitch_train_normal_all_local.lance` | `e6c48a35eef32edf43a6c78db37c52adcbbe656f47b2e453e1917365355f3aa1` | Train-normal only for train-dependent fitting |
| Validation-normal Lance | `outputs/research_mvp/datasets/tempglitch_validation_normal_all_local.lance` | `bb89e66c6afa5d3af7728be8efd0bacbf49cfedca6704fd27cc6178f27e556e6` | Source of two calibration-normal episodes plus 12 evaluation-normal episodes |
| Validation-buggy Lance | `outputs/research_mvp/datasets/tempglitch_validation_buggy_all_local.lance` | `02c2417579bb25cd683738106d0603c5ed7a70fb6f3271716f9c23b95bae10f1` | 22 evaluation-buggy episodes |
| Seed42 best weights | `artifacts/downloads/r3_seed42_artifacts_extract/lewm_outputs/r3_seed42/best_weights.pt` | `8bf1d6220673b4a3f2de82f2478bfe1465cc4667cb44564b4bcf9c8b30f6c704` | Local extracted artifact root |
| Seed43 best weights | `artifacts/verified/r4_rerun_2026_06_17/r3_seed43/best_weights.pt` | `c5e6a2165c7e9d2dc6170feace048287f5f55a8b10d3181b640b21e5ae422edf` | Local verified rerun artifact |
| Seed44 best weights | `artifacts/verified/r4_rerun_2026_06_17/r3_seed44/best_weights.pt` | `7bb6bd75645fa6c85e7849647669ad45a77c79f3eecefcdc3fecfc542446b8d8` | Local verified rerun artifact |

## Frozen Manifest

- Manifest path: `outputs/r5_tempglitch_identical_episode/r5_manifest.csv`
- Manifest SHA256: `93327b661bd419944b57fb33112ec79264cb8a7b27708252c8507f3d3410f620`
- Window count: `30,549`
- Calibration-normal episodes: `2`
- Evaluation episodes: `34` (`12` normal, `22` buggy)
- Calibration episode IDs:
  - `Godot_Animation_Platformer_Normal_18`
  - `Godot_Blinking_Normal_106`

## Methods

Required methods executed:

- LeWM latent surprise for seed42, seed43, and seed44 artifact-backed checkpoints.
- `frame_diff`.
- Train-normal-fitted `feature_distance`.

Deferred methods:

- Conv3D autoencoder: not included in this first R5 family because the existing Phase 6E path was
  not yet promoted into this identical-manifest runner.
- Frozen video-representation baseline: still planning-only.

## Threshold And Metric Policy

- Threshold source: per-configuration 95th percentile of the two calibration-normal episode
  scores.
- Primary metrics: AUROC and AUPRC.
- Secondary metrics: F1 at the normal-calibrated threshold and FPR@95TPR.
- Uncertainty: grouped episode-bootstrap confidence intervals for AUROC and F1.

## Output Hashes

| Output | Path | SHA256 |
| --- | --- | --- |
| Manifest | `outputs/r5_tempglitch_identical_episode/r5_manifest.csv` | `93327b661bd419944b57fb33112ec79264cb8a7b27708252c8507f3d3410f620` |
| Manifest hash sidecar | `outputs/r5_tempglitch_identical_episode/r5_manifest.sha256` | `e79bfeb774d4f78f99d1acc9772dcf2594a4039d7b91645466d0d009a6d95b2f` |
| Baseline window scores | `outputs/r5_tempglitch_identical_episode/baseline_scores.csv` | `cf6fb7f2caaac7b9c91cf9d1956fbddb09eed64333335700d088c9a35538b66d` |
| LeWM window scores seed42 | `outputs/r5_tempglitch_identical_episode/lewm_scores_seed42.csv` | `c235f294f600de4bc9781dc01cb043930a1176ba0e57d0f0010e35bc8e65426b` |
| LeWM window scores seed43 | `outputs/r5_tempglitch_identical_episode/lewm_scores_seed43.csv` | `36850092c8745543deb53b1d22de25b7356830243dde1a85e59ecb165cfa2cc2` |
| LeWM window scores seed44 | `outputs/r5_tempglitch_identical_episode/lewm_scores_seed44.csv` | `6dc1f0646380f279125c018b630c7abc3a162ab55a2f062564410919b2061019` |
| Episode scores | `outputs/r5_tempglitch_identical_episode/episode_scores.csv` | `7397805c3812cc7deba7f9493cf6d87707dfeeac460b1d8079a5ed7fa8e2c5ab` |
| Comparison table | `outputs/r5_tempglitch_identical_episode/r5_comparison.csv` | `e4d5c7e797239529a2802e626f1dc953a9bb417899a77ff733b6a3a2c4690fc9` |
| Metrics JSON | `outputs/r5_tempglitch_identical_episode/r5_metrics.json` | `770a6ca70f7f6e228c9a5b26dde3d62623eaac12bdd2eff1f2190228a266affa` |
| Provenance JSON | `outputs/r5_tempglitch_identical_episode/r5_provenance.json` | `e4cbed4b7942f00dfe8f4e0fb24f8f9dc62da0dcb526e5fce3974e8b306e9684` |
| Markdown report | `outputs/r5_tempglitch_identical_episode/R5_REPORT.md` | `7c7263b964d3b5c84a2942314a2f9654a79943975bd989a38c7dc9edb83e94fd` |

## Qualified Metric Summary

Best observed rows within the frozen R5 family:

| Family | Configuration | AUROC | AUPRC | F1 | FPR@95TPR | 95% CI |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| LeWM best AUROC | seed44 `lewm_l2_max` + episode `mean` | `0.696970` | `0.796125` | `0.723404` | `0.75` | AUROC `[0.479152, 0.878319]`; F1 `[0.536585, 0.851984]` |
| LeWM best AUPRC | seed44 `lewm_l2_top2_mean` + episode `mean` | `0.670455` | `0.797118` | `0.711111` | `0.75` | AUROC `[0.450536, 0.857792]`; F1 `[0.526316, 0.844487]` |
| Baseline best AUROC | `feature_distance` + episode `top2_mean` | `0.617424` | `0.746156` | `0.086957` | `0.833333` | AUROC `[0.397633, 0.810653]`; F1 `[0, 0.260870]` |
| Baseline best AUPRC | `feature_distance` + episode `mean` | `0.602273` | `0.777896` | `0.24` | `1` | AUROC `[0.407068, 0.8]`; F1 `[0, 0.444444]` |
| Baseline best F1 | `frame_diff` + episode `mean` | `0.530303` | `0.701055` | `0.785714` | `0.833333` | AUROC `[0.321329, 0.754941]`; F1 `[0.666667, 0.885246]` |

## Interpretation Boundary

Safe conclusions:

- The repository now has a full provenance-bound non-locked R5 TempGlitch identical-episode
  evaluation bundle.
- Exact family-qualified metric comparisons can be cited with the hashes above.
- The best observed AUROC and AUPRC rows in this frozen family came from LeWM seed44 mean-episode
  L2 variants.

Still forbidden:

- Any locked-test claim.
- Any World of Bugs result claim.
- Broad LeWM superiority, state-of-the-art, temporal-localization, or SIGReg-benefit claim.
- Any claim that these results generalize beyond this non-locked TempGlitch family.

## Safety Flags

- `locked_test_materialized = false`
- `locked_test_scored = false`
- `validation_buggy_used_for_fit_select = false`

