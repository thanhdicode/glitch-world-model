# Demo - P6 Qualitative Glitch Surprise Timeline

## What this demo does

This demo produces **qualitative only** latent-surprise timeline plots for gameplay episodes scored
by LeWM during the non-locked TempGlitch pair-disjoint follow-up evaluation. It wraps
`scripts/generate_qualitative_surprise_timelines.py` in a single reproducible entry point and
writes a machine-readable receipt that records the claim boundary for the run.

Outputs:

| Artifact | Path |
| --- | --- |
| Timeline PNGs | `outputs/demo_timelines/*.png` |
| Receipt JSON | `outputs/demo_timelines/demo_receipt.json` |

## Claim Boundary

| Claim | Status |
| --- | --- |
| Qualitative per-episode surprise timeline | Allowed |
| Temporal-localization metric | Not claimed; ground-truth spans are unavailable |
| Locked test materialization or scoring | Not allowed |
| Broad LeWM detection superiority over all baselines | Not claimed |
| Kaggle required to reproduce | Not required |

The receipt JSON always contains `"temporal_metrics_claimed": false` and
`"locked_test_used": false`.

## Required Inputs

The demo reads three CSV files produced by the non-locked TempGlitch pair-disjoint follow-up
evaluation:

- `outputs/tempglitch_followup_pair_disjoint/followup_comparison.csv`
- `outputs/tempglitch_followup_pair_disjoint/followup_episode_scores.csv`
- `outputs/tempglitch_followup_pair_disjoint/followup_manifest.csv`

These files are not committed to Git because `outputs/` is ignored. The surrounding release checks
and provenance rules are documented in
[15_reproducibility_checklist.md](C:/Users/ADMIN/Desktop/glitch-world-model/docs/research/15_reproducibility_checklist.md).

## Commands

Dry-run, no artifact CSVs required:

```bash
python demo/run_glitch_demo.py --dry-run
```

Full run with the default non-locked follow-up artifacts:

```bash
python demo/run_glitch_demo.py
```

Full run with custom paths:

```bash
python demo/run_glitch_demo.py \
    --comparison-csv outputs/tempglitch_followup_pair_disjoint/followup_comparison.csv \
    --episode-scores-csv outputs/tempglitch_followup_pair_disjoint/followup_episode_scores.csv \
    --manifest-csv outputs/tempglitch_followup_pair_disjoint/followup_manifest.csv \
    --output-dir outputs/demo_timelines \
    --max-episodes 6
```

## Receipt Schema

Every run writes `outputs/demo_timelines/demo_receipt.json` with at least:

```json
{
  "temporal_metrics_claimed": false,
  "locked_test_used": false,
  "ground_truth_spans_available": false,
  "kaggle_required": false,
  "claim_boundary": "qualitative only - no temporal-localization metric, no locked test, no broad LeWM superiority claim",
  "demo_phase": "P6"
}
```

## Demo Test Command

```bash
python -m pytest tests/test_p6_demo.py -v
```
