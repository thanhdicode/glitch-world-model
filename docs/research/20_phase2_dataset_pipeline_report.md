# Phase 2 Dataset Pipeline Report

## 1. Objective

Phase 2 proves that this repo can ingest a real public gameplay-video benchmark and preserve the existing pipeline contracts:

- `manifest.csv`
- labels CSV with `source,start_frame,end_frame,label`
- `scores.csv`
- `metrics.json`

The selected benchmark was TempGlitch because Phase 1B verified a real public video artifact with a permissive license.

## 2. Selected public source

- Dataset: <https://huggingface.co/datasets/asgaardlab/TempGlitch>
- Verified access date: `2026-06-08`
- License on the public dataset page: `MIT`
- Public artifact scope used in this phase:
  - category: `Blinking`
  - local smoke subset: `1` `Buggy` video and `1` `Normal` video
  - dataset revision captured in metadata: `1d46a63c31ebfe3b675b51a2231d547da372eff9`

## 3. Code added

- `src/glitch_detection/tempglitch.py`
  - public TempGlitch URL parsing
  - tiny subset download helper
  - manifest merge helper
  - labels conversion helper
- `scripts/download_tempglitch.py`
- `scripts/convert_tempglitch_labels.py`
- `scripts/run_tempglitch_smoke_test.py`
- `tests/test_tempglitch.py`

## 4. Operational notes

- TempGlitch is video-only, so local decoding required the optional video dependency `opencv-python`.
- That dependency was not present initially in this environment and was installed locally before the smoke run.
- No raw data, generated outputs, or checkpoints were committed.

## 5. Smoke command actually run

```powershell
python scripts\run_tempglitch_smoke_test.py --categories Blinking --limit-per-group 1 --clip-length 16 --stride 16 --size 128 --scorer frame_diff --scorer feature_distance --scorer mini_latent
```

## 6. Produced local artifacts

- Raw subset root: `data/raw/tempglitch_smoke/`
- Raw metadata: `data/raw/tempglitch_smoke/metadata.csv`
- Source note: `data/raw/tempglitch_smoke/README_SOURCE.txt`
- Converted labels: `data/raw/tempglitch_smoke_labels.csv`
- Processed manifest: `data/processed/tempglitch_smoke/manifest.csv`
- Metrics:
  - `outputs/tempglitch_smoke_frame_diff_metrics.json`
  - `outputs/tempglitch_smoke_feature_distance_metrics.json`
  - `outputs/tempglitch_smoke_mini_latent_metrics.json`
- Reports:
  - `outputs/tempglitch_smoke_frame_diff_report.md`
  - `outputs/tempglitch_smoke_feature_distance_report.md`
  - `outputs/tempglitch_smoke_mini_latent_report.md`
  - `outputs/tempglitch_smoke_comparison.md`

All of the above output paths are gitignored.

## 7. What the pipeline converted

The public TempGlitch artifact exposes binary per-video labels, not verified finer temporal spans. To preserve the repo interfaces without inventing unsupported annotations, the smoke pipeline used this rule:

- buggy video -> one positive interval covering the full frame range represented in the merged manifest
- normal video -> no explicit positive interval row

For the executed smoke subset:

- sources:
  - `Godot_Blinking_1`
  - `Godot_Blinking_Normal_1`
- merged manifest clips: `61`
- positive clips after overlap mapping: `38`
- source coverage:
  - `Godot_Blinking_1`: `38` clips, frames `0-607`
  - `Godot_Blinking_Normal_1`: `23` clips, frames `0-367`

## 8. Actual smoke metrics

| Scorer | Precision | Recall | F1 | Accuracy | AUROC |
| --- | ---: | ---: | ---: | ---: | ---: |
| `frame_diff` | `0.622951` | `1.0` | `0.767677` | `0.622951` | `0.526316` |
| `feature_distance` | `0.765957` | `0.947368` | `0.847059` | `0.786885` | `0.789474` |
| `mini_latent` | `0.703704` | `1.0` | `0.826087` | `0.737705` | `0.597254` |

Observed ranking on this smoke subset:

- best F1 / AUROC: `feature_distance`
- second: `mini_latent`
- third: `frame_diff`

## 9. What Phase 2 proves

- Public TempGlitch access is real and scriptable from this repo.
- The repo can convert public TempGlitch videos into the existing `manifest.csv` and labels CSV interfaces.
- The scorer registry works unchanged on this converted benchmark subset.
- The repo can emit real `scores.csv`, `metrics.json`, and Markdown experiment reports on a public benchmark subset.

## 10. What Phase 2 does not prove

- These numbers are not a paper-ready benchmark result.
- The subset is tiny: one category, one buggy video, one normal video.
- There is no held-out split yet.
- Thresholds are selected on the same evaluated subset.
- The current public TempGlitch artifact still does not verify finer temporal-span annotations.
- No timeline plot was produced in this phase because the merged multi-source scores would make the current single-axis plot misleading.

## 11. Immediate next step

The next benchmark step should be a larger TempGlitch slice with a documented repo-defined split protocol, followed by failure analysis and at least one ablation. That is the minimum path from smoke-test feasibility to paper-usable evidence.

Phase 3/4 subsequently completed a leakage-aware 30-video split experiment. See [21_phase3_phase4_baseline_results.md](21_phase3_phase4_baseline_results.md).
