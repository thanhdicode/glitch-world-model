# 116 - K1 Learned Baselines Intake Protocol

Date: 2026-06-24
Status: validated local intake protocol

## Purpose

This note records the local protocol used to ingest the completed Kaggle K1 learned-baseline run,
validate the downloaded bundle, and map the learned clip scores onto the current bounded
TempGlitch follow-up comparison surface.

The protocol is validation-only and non-locked:

- no locked-test materialization
- no locked-test scoring
- no new Kaggle execution
- no new LeWM training

## Downloaded Inputs

- `learned_baselines_k1.tar.gz`
- `learned_baselines_k1.tar.gz.sha256`
- `k1_learned_baselines.log`

Repository-local intake paths:

- tarball: `C:\Users\ADMIN\Downloads\learned_baselines_k1.tar.gz`
- sidecar: `C:\Users\ADMIN\Downloads\learned_baselines_k1.tar.gz.sha256`
- extract root: `outputs/learned_baselines_k1/learned_baselines_k1/`

Verified tarball SHA256:

- expected: `3a1da8f8ef0e8ca8e78de317548664280e79d09e7ce95bd56d50e1c62133b74d`
- actual: `3a1da8f8ef0e8ca8e78de317548664280e79d09e7ce95bd56d50e1c62133b74d`

## Local Validation Commands

```powershell
python scripts/validate_learned_baselines.py --output-root outputs/learned_baselines_k1/learned_baselines_k1
python scripts/ingest_k1_learned_baselines.py
```

The validator now supports downloaded Kaggle bundles on a local checkout by remapping the stored
`/kaggle/input/...` paths to the existing local K1 package under
`outputs/k1_tempglitch_kaggle_dataset/lewm-k1-tempglitch-inputs/`.

## Validation Contract

The K1 bundle must satisfy all of the following:

- tarball SHA256 matches the `.sha256` sidecar
- extracted layout contains all three checkpoints, score CSVs, metadata JSON files, and SHA256
  sidecars
- `protocol_audit.json` and `learned_baselines_summary.json` match exactly
- `fit_split=train-normal` for all three learned baselines
- persisted manifests align with the grouped train/validation partition
- validation score CSVs align with the persisted validation manifest in row order and provenance
- `test_materialized=false`
- `test_scored=false`
- `locked_test_materialized=false`
- `locked_test_scored=false`
- cross-split leakage count remains `0`

## Canonical Comparison Surface

K1 comparison is anchored to the existing validated TempGlitch follow-up artifacts in
`outputs/tempglitch_followup_pair_disjoint/`.

The canonical support is taken from the already validated follow-up receipt rather than from a new
 follow-up rerun:

- calibration-normal episodes:
  - `Godot_Blinking_Normal_106`
  - `Godot_Frozen_Animation_Platformer_Normal_107`
- evaluation normal-negative episodes: `12`
- evaluation buggy-positive episodes: `22`
- evaluation total: `34`

This keeps the learned-baseline comparison on the same currently cited bounded support surface as
the existing LeWM and simple-baseline follow-up report.

## Episode Aggregation And Metrics

Each learned baseline is aggregated to the episode level with the fixed aggregation surface:

- `mean`
- `max`
- `top2_mean`

Metrics per configuration:

- AUROC
- AUPRC
- F1
- precision
- recall
- balanced accuracy
- FPR@95TPR
- grouped bootstrap confidence intervals where currently supported by repository tooling

Threshold rule:

- threshold = 95th percentile of the canonical calibration-normal episode scores

Paired comparison rule:

- compare learned baseline episode scores against the best current LeWM row on the exact same
  evaluation episodes
- report paired bootstrap deltas for AUROC and AUPRC
- report DeLong AUROC tests as bounded split-level statistics only

## Output Analysis Artifacts

`scripts/ingest_k1_learned_baselines.py` writes:

- `outputs/learned_baselines_k1/analysis/k1_followup_episode_scores.csv`
- `outputs/learned_baselines_k1/analysis/k1_followup_comparison.csv`
- `outputs/learned_baselines_k1/analysis/k1_followup_summary.json`
- `outputs/learned_baselines_k1/analysis/K1_FOLLOWUP_REPORT.md`

Current analysis hashes:

- episode scores CSV: `f610f648d425df699c41e3707d7067486e18c186a799bfabd2f4bd265af87fe7`
- comparison CSV: `4702efa7f243cab1252314cd73926e1376c53e6dfbe50369caffd0cefbb3b748`
- summary JSON: `969c4c210d73d3971fb15fbf8f3d84584b729209a8b79865521ce0ae758fdbeb`
- report markdown: `14de2db17eab27526a9ceaca6615cacb570da2d74d93e8492d97961934abb7be`

## Claim Boundary

Allowed:

- K1 completed successfully and the downloaded learned-baseline bundle validates locally.
- All three learned baselines are now scored on the exact currently cited TempGlitch follow-up
  support.
- Learned-baseline comparisons are bounded to this non-locked validation split.

Forbidden:

- state of the art
- broad superiority
- cross-game generalization
- temporal localization
- SIGReg benefit
- action-conditioning benefit
- any locked-test result
