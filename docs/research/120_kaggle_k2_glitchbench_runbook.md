# 120 - Kaggle K2 GlitchBench Runbook

Date: 2026-06-24
Status: local package and validator ready; Kaggle run not yet executed

## Dataset Name

Required Kaggle Dataset name:

- `lewm-k2-glitchbench-inputs`

Additional attached dataset may be required for LeWM seed artifacts if the K2 job will score LeWM.

## Required Kaggle Input Paths

- `/kaggle/input/lewm-k2-glitchbench-inputs/combined_manifest.csv`
- `/kaggle/input/lewm-k2-glitchbench-inputs/grouped_split.csv`
- `/kaggle/input/lewm-k2-glitchbench-inputs/clips_root`

## Local Package Receipt

- Built zip: `outputs/k2_glitchbench_kaggle_dataset/lewm-k2-glitchbench-inputs.zip`
- SHA256: `d2c6be8f83d99cb6a04578532f0f80d620c168342ff3e630b4e6b5389c62b038`
- Local validator: passed

## Exact K2 Command

Use this notebook cell or shell command:

```bash
python scripts/run_kaggle_glitchbench_benchmark.py \
  --manifest /kaggle/input/lewm-k2-glitchbench-inputs/combined_manifest.csv \
  --split /kaggle/input/lewm-k2-glitchbench-inputs/grouped_split.csv \
  --clips-root /kaggle/input/lewm-k2-glitchbench-inputs/clips_root \
  --output-root /kaggle/working/glitchbench_k2 \
  --device cuda \
  --lewm-seed-artifact-root /kaggle/input/<lewm-seed-artifact-dataset>
```

Dry-run sanity check:

```bash
python scripts/run_kaggle_glitchbench_benchmark.py \
  --manifest /kaggle/input/lewm-k2-glitchbench-inputs/combined_manifest.csv \
  --split /kaggle/input/lewm-k2-glitchbench-inputs/grouped_split.csv \
  --clips-root /kaggle/input/lewm-k2-glitchbench-inputs/clips_root \
  --output-root /kaggle/working/glitchbench_k2 \
  --device cpu \
  --dry-run
```

## Expected Outputs

- `glitchbench_benchmark_summary.json`
- `train_normal_manifest.csv`
- `validation_manifest.csv`
- simple-baseline train/validation score CSVs
- learned-baseline train/validation score CSVs
- LeWM benchmark outputs only if compatible seed artifacts are attached

## Acceptance Criteria

- input package validator passes
- train split contains only synthetic-normal rows
- validation split contains both normal and buggy rows
- locked-test flags remain false
- metric JSON or CSV outputs are produced for every executed method
- any missing LeWM artifact root fails early with an actionable error, not a silent skip

## Failure Triage

- Missing package files:
  rerun `scripts/build_k2_glitchbench_kaggle_dataset.py`
- Bundle validator failure:
  rerun `scripts/validate_glitchbench_bundle.py` locally before Kaggle
- Missing LeWM artifacts:
  attach a Kaggle dataset containing compatible seed42/43/44 artifacts or plan a separate LeWM
  training step for K2
- Runtime import failure for optional learned baselines:
  check Kaggle environment dependencies before rerunning

## Download After K2

Download the full `glitchbench_k2` working directory, especially:

- `glitchbench_benchmark_summary.json`
- all per-method score CSVs
- any LeWM score outputs
- notebook log

## Claim Boundary

- K2 is still a bounded image-level benchmark.
- Synthetic normals remain explicit.
- No temporal-localization claim is allowed.
- No cross-game generalization claim is allowed.
- No broad superiority or SOTA claim is allowed.
- Locked test remains closed.
