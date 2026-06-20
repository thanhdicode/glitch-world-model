# R5-XGAME: Cross-Dataset Comparison

Status: `SKELETON_ONLY`

## Purpose

Combine validated TempGlitch R5 and WOB R5 evaluation results into a single cross-dataset
comparison table. This phase does not run any model training or scoring — it only aggregates
previously validated metric files.

## Prerequisites

1. R5 TempGlitch identical-episode evaluation must be completed and validated.
2. R5-WOB identical-episode evaluation must be completed, downloaded, and validated.
3. Both metric files must pass their respective validators.

## Usage

```bash
# After both R5 outputs are validated:
python scripts/run_r5_xgame_comparison.py \
    --tempglitch-metrics outputs/r5_tempglitch_identical_episode/r5_metrics.json \
    --wob-metrics outputs/r5_wob_identical_episode/r5_wob_metrics.json \
    --output-dir outputs/r5_xgame_comparison

# Validate the comparison output:
python scripts/validate_r5_xgame_comparison.py \
    --output-dir outputs/r5_xgame_comparison
```

## Claim Safety

- No cross-game generalization claim until both datasets have validated outputs.
- No action-conditioning claim from this comparison alone.
- No superiority or state-of-the-art claim.
- Locked test remains closed.

## Outputs

- `r5_xgame_comparison.csv` — cross-dataset comparison rows
- `r5_xgame_provenance.json` — provenance and locked-test flags
