# 120 - Kaggle K2 GlitchBench Runbook

Date: 2026-06-25
Status: local K2 runner repaired; rerun Kaggle dry-run directly from `/kaggle/input` before the
first scientific full K2 launch

## Scope

K2 is a bounded image-level GlitchBench subset benchmark. The current public path supplies static
bug images only, so this repo materializes repeated-frame clips and explicit synthetic normal
companions. K2 cannot support temporal-localization, cross-game generalization, broad superiority,
or SOTA claims.

## Required Kaggle Datasets

- `lewm-k2-glitchbench-inputs`
- `lewm-k2-lewm-seed-artifacts` for the scientific full K2 path

## Local Package Receipts

- Input zip:
  `outputs/k2_glitchbench_kaggle_dataset/lewm-k2-glitchbench-inputs.zip`
- Input zip SHA256:
  `d2c6be8f83d99cb6a04578532f0f80d620c168342ff3e630b4e6b5389c62b038`
- LeWM artifact zip:
  `outputs/k2_lewm_seed_artifacts/lewm-k2-lewm-seed-artifacts.zip`
- LeWM artifact zip SHA256:
  `bf227ef26ac8316ccbc7456425e6218d2ac2172576fa874c35041b4913d04e69`

## Required LeWM Artifact Layout

The scientific K2 path now requires a normalized seed-artifact root with this exact minimum
layout:

- `/kaggle/input/lewm-k2-lewm-seed-artifacts/seed42/best_weights.pt`
- `/kaggle/input/lewm-k2-lewm-seed-artifacts/seed42/config.json`
- `/kaggle/input/lewm-k2-lewm-seed-artifacts/seed43/best_weights.pt`
- `/kaggle/input/lewm-k2-lewm-seed-artifacts/seed43/config.json`
- `/kaggle/input/lewm-k2-lewm-seed-artifacts/seed44/best_weights.pt`
- `/kaggle/input/lewm-k2-lewm-seed-artifacts/seed44/config.json`

Optional but supported:

- `checkpoint.sha256`
- `training_metadata.json`
- existing `.sha256` sidecars for copied metadata/config/weights

The repo now provides `scripts/build_k2_lewm_seed_artifact_dataset.py` to normalize local seed
roots into this Kaggle-ready layout.

## Kaggle Failure Note (2026-06-25)

An initial full K2 Kaggle attempt failed after the direct dry-run passed because
`scripts/run_kaggle_glitchbench_benchmark.py` incorrectly passed `device=...` into learned-baseline
config constructors. The repaired runner now constructs:

- `VideoAutoencoderConfig()`
- `CNNLSTMConfig()`
- `VideoTransformerConfig()`

without a `device` keyword and passes `device` only to `train_model(...)` and
`score_records_with_checkpoint(...)`.

## Direct `/kaggle/input` Dry-Run Command

Run this first. It now works directly on read-only Kaggle mounts because the bundle validator writes
temporary protocol files outside `package_root`.

```bash
python scripts/run_kaggle_glitchbench_benchmark.py \
  --manifest /kaggle/input/lewm-k2-glitchbench-inputs/combined_manifest.csv \
  --split /kaggle/input/lewm-k2-glitchbench-inputs/grouped_split.csv \
  --clips-root /kaggle/input/lewm-k2-glitchbench-inputs/clips_root \
  --output-root /kaggle/working/glitchbench_k2 \
  --device cpu \
  --dry-run
```

Expected dry-run status:

- `dry_run_ready`

## Scientific Full K2 Command

This is the intended evidence-producing K2 path. It is fail-closed when the LeWM seed artifact
dataset is missing.

## Install Isolated LeWM Runtime

Before the scientific full K2 command, install the isolated LeWM runtime rather than relying on
`pip install -e .` alone. The repo now provides a Kaggle launcher that copies the proven XGame
pattern:

- installs `stable-worldmodel==0.1.1`
- installs `hydra-core==1.3.3`
- installs `stable-pretraining==0.1.7` without `--no-deps`
- installs `transformers==4.57.6`
- verifies imports before starting K2 scoring

Preferred launcher:

```bash
bash cloud/k2_glitchbench/run_kaggle_k2_full.sh
```

The launcher script is:

- `cloud/k2_glitchbench/run_kaggle_k2_full.sh`

```bash
python scripts/run_kaggle_glitchbench_benchmark.py \
  --manifest /kaggle/input/lewm-k2-glitchbench-inputs/combined_manifest.csv \
  --split /kaggle/input/lewm-k2-glitchbench-inputs/grouped_split.csv \
  --clips-root /kaggle/input/lewm-k2-glitchbench-inputs/clips_root \
  --output-root /kaggle/working/glitchbench_k2 \
  --device cuda \
  --lewm-seed-artifact-root /kaggle/input/lewm-k2-lewm-seed-artifacts
```

Expected scientific success status:

- `k2_complete_lewm_and_baselines`

LeWM lane details:

- seeds: `42`, `43`, `44`
- aggregations: `mean`, `max`
- threshold source: `train_normal_p95`
- action mode: `zero_action`
- threshold fitting must not use validation labels

## Optional Baseline-Only Smoke Test

This path is engineering-only and cannot support LeWM-vs-baseline claims.

```bash
python scripts/run_kaggle_glitchbench_benchmark.py \
  --manifest /kaggle/input/lewm-k2-glitchbench-inputs/combined_manifest.csv \
  --split /kaggle/input/lewm-k2-glitchbench-inputs/grouped_split.csv \
  --clips-root /kaggle/input/lewm-k2-glitchbench-inputs/clips_root \
  --output-root /kaggle/working/glitchbench_k2 \
  --device cuda \
  --baseline-only
```

Expected smoke-test success status:

- `baseline_only_complete_no_lewm`

## Expected Outputs

Always expected:

- `bundle_validation.json`
- `glitchbench_benchmark_summary.json`
- `glitchbench_benchmark_metrics.csv`
- `train_normal_manifest.csv`
- `validation_manifest.csv`
- `frame_diff_train_scores.csv`
- `frame_diff_validation_scores.csv`
- `feature_distance_train_scores.csv`
- `feature_distance_validation_scores.csv`
- learned-baseline checkpoint, metadata, and score CSV outputs

Scientific full K2 only:

- `lewm_artifact_validation.json`
- `lewm/seed42/lewm_seed42_mean_train_scores.csv`
- `lewm/seed42/lewm_seed42_mean_validation_scores.csv`
- `lewm/seed42/lewm_seed42_max_train_scores.csv`
- `lewm/seed42/lewm_seed42_max_validation_scores.csv`
- matching `*_metadata.json` files for every LeWM score CSV
- the same file family for `seed43` and `seed44`

## Packaging And Download After K2

Download the full `glitchbench_k2` working directory before registering any claim.

Optional Kaggle tarball command:

```bash
tar -czf /kaggle/working/glitchbench_k2_outputs.tar.gz -C /kaggle/working glitchbench_k2
sha256sum /kaggle/working/glitchbench_k2_outputs.tar.gz > /kaggle/working/glitchbench_k2_outputs.tar.gz.sha256
```

Retain at minimum:

- `glitchbench_benchmark_summary.json`
- `glitchbench_benchmark_metrics.csv`
- `bundle_validation.json`
- `lewm_artifact_validation.json` when the scientific path is used
- every per-method score CSV
- notebook log
- optional tarball and `.sha256` sidecar

## Failure Triage

- Read-only package validation failure:
  rerun the direct `/kaggle/input` dry-run first; the current runner should no longer write inside
  the mounted package
- Missing LeWM artifacts:
  attach `lewm-k2-lewm-seed-artifacts` or build it locally with
  `scripts/build_k2_lewm_seed_artifact_dataset.py`
- Full K2 without LeWM artifact root:
  expected fail-closed behavior unless `--baseline-only` is explicitly passed
- Baseline-only completion:
  treat as smoke-test infrastructure evidence only, not benchmark evidence

## Claim Boundary

- Allowed after local intake validation of the downloaded K2 artifact only:
  bounded image-level GlitchBench metrics on the exact frozen K2 split
- Forbidden even after K2:
  temporal localization, natural-normal evidence, cross-game generalization, SOTA, broad
  superiority, SIGReg benefit, action-conditioning benefit, and any locked-test claim
