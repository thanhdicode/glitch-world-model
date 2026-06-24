# 117 - Kaggle K1 Learned Baselines Runbook

Date: 2026-06-24
Status: completed run intake reference

## Scope

This runbook captures the offline post-run intake steps for the completed Kaggle K1 learned
baseline job.

It does not relaunch Kaggle and it does not open locked test.

## Bundle Summary

Observed Kaggle success markers:

- `K1_SUCCESS`
- elapsed minutes: `17.8`
- train-normal clips: `2167`
- validation clips: `1898`
- `locked_test_materialized=false`
- `locked_test_scored=false`
- validated baselines:
  - `video_autoencoder`
  - `cnn_lstm`
  - `video_transformer`

Tarball SHA256 recorded by Kaggle:

- `3a1da8f8ef0e8ca8e78de317548664280e79d09e7ce95bd56d50e1c62133b74d`

## Exact Intake Steps

1. Verify the tarball hash against the sidecar.

```powershell
$expected = (Get-Content C:\Users\ADMIN\Downloads\learned_baselines_k1.tar.gz.sha256).Split("  ")[0]
$actual = (Get-FileHash C:\Users\ADMIN\Downloads\learned_baselines_k1.tar.gz -Algorithm SHA256).Hash.ToLower()
$expected
$actual
```

2. Extract the tarball under the ignored output root.

```powershell
New-Item -ItemType Directory -Force outputs\learned_baselines_k1 | Out-Null
tar -xzf C:\Users\ADMIN\Downloads\learned_baselines_k1.tar.gz -C outputs\learned_baselines_k1
```

3. Run the strict local validator.

```powershell
python scripts/validate_learned_baselines.py --output-root outputs/learned_baselines_k1/learned_baselines_k1
```

4. Project the learned clip scores onto the current validated TempGlitch follow-up support.

```powershell
python scripts/ingest_k1_learned_baselines.py
```

## Expected Success Criteria

- local validator status: `validated`
- train-normal clip count: `2167`
- validation clip count: `1898`
- all checkpoint, metadata, and validation-score sidecars match
- analysis summary written under `outputs/learned_baselines_k1/analysis/`

## Current Validated Receipt

Local validator receipt SHA256:

- `ab5187a9636c347c9b7a97d5c1b5b9ef2eea34cd27c978b7a92166e2edbb9a64`

Analysis summary SHA256:

- `969c4c210d73d3971fb15fbf8f3d84584b729209a8b79865521ce0ae758fdbeb`

## Failure Modes

- SHA mismatch:
  stop and do not ingest claims
- missing extracted file or sidecar:
  stop and re-check the downloaded bundle
- local validator path error:
  use the current validator version, which remaps Kaggle input paths to the local K1 package
- support mismatch against the TempGlitch follow-up:
  stop and inspect `followup_metrics.json` versus the learned-baseline episode mapping

## Next Decision After A Clean Intake

Once the K1 bundle validates and the learned-baseline comparison is written locally:

- update claim registry and paper tables with only the bounded supported claims
- move to Phase P3 local GlitchBench preparation
- stop before the user-operated Kaggle K2 gate
