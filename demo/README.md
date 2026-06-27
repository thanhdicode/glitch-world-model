# P6 Qualitative Glitch Surprise Timeline Demo

This demo produces **qualitative** LeWM surprise timeline plots for gameplay episodes that already have non-locked follow-up artifacts. It wraps `scripts/generate_qualitative_surprise_timelines.py` behind one reproducible entry point and writes a machine-readable safety receipt.

The demo is for reproducibility and presentation support only. It does not introduce new benchmark numbers.

## Claim boundary

| Claim surface | Status |
|---|---|
| Qualitative per-episode surprise timeline | Allowed |
| Temporal localization metrics such as IoU, onset/offset F1, span recall, or span precision | Not claimed |
| Locked test materialization or scoring | Not used |
| Broad LeWM superiority over all baselines | Not claimed |
| Kaggle requirement | Not required |

Every run writes `demo_receipt.json` with:

```json
{
  "temporal_metrics_claimed": false,
  "locked_test_used": false,
  "ground_truth_spans_available": false,
  "kaggle_required": false
}
```

## Required inputs for a full run

By default, the full demo reads the ignored non-locked TempGlitch follow-up artifacts:

```text
outputs/tempglitch_followup_pair_disjoint/followup_comparison.csv
outputs/tempglitch_followup_pair_disjoint/followup_episode_scores.csv
outputs/tempglitch_followup_pair_disjoint/followup_manifest.csv
```

These files are intentionally not committed to Git because `outputs/` is an artifact directory.

## Dry run

The dry run requires no artifacts. It writes the same safety receipt and reports whether the expected inputs are available.

```bash
python demo/run_glitch_demo.py --dry-run
```

Expected behavior:

```text
P6 Qualitative Glitch Demo Lane
  temporal_metrics_claimed : False
  locked_test_used         : False
  kaggle_required          : False
[dry-run] Receipt written: outputs/demo_timelines/demo_receipt.json
[dry-run] Done.
```

## Full run

Use this when the non-locked follow-up artifacts exist locally:

```bash
python demo/run_glitch_demo.py
```

Outputs:

| Artifact | Path |
|---|---|
| Timeline PNG plots | `outputs/demo_timelines/*.png` |
| Demo receipt | `outputs/demo_timelines/demo_receipt.json` |
| Inner qualitative receipt | `outputs/demo_timelines/qualitative_timeline_receipt.json` |

## Custom artifact paths

```bash
python demo/run_glitch_demo.py \
    --comparison-csv outputs/tempglitch_followup_pair_disjoint/followup_comparison.csv \
    --episode-scores-csv outputs/tempglitch_followup_pair_disjoint/followup_episode_scores.csv \
    --manifest-csv outputs/tempglitch_followup_pair_disjoint/followup_manifest.csv \
    --output-dir outputs/demo_timelines \
    --max-episodes 4
```

## Demo-only verification

```bash
python -m pytest tests/test_p6_demo.py -v
```

## Safety checklist

Before using any generated figure in slides or a paper draft, verify:

- `demo_receipt.json` has `"temporal_metrics_claimed": false`.
- `demo_receipt.json` has `"locked_test_used": false`.
- `demo_receipt.json` has `"kaggle_required": false`.
- The figure caption says qualitative timeline only.
- No temporal-localization metric is reported from this demo.
- No new performance, SIGReg-benefit, action-benefit, or cross-game claim is introduced.
