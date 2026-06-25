# Expected K3 Outputs

The Kaggle run must emit these top-level files under the chosen output root:

- `r6_ablation_plan.json`
- `r6_controlled_pairs.json`
- `r6_ablation_receipt.json`

The scientific receipt must describe all 12 variants:

- `seed42_sigreg_on_real_action`
- `seed42_sigreg_on_zero_action`
- `seed42_sigreg_off_real_action`
- `seed42_sigreg_off_zero_action`
- `seed43_sigreg_on_real_action`
- `seed43_sigreg_on_zero_action`
- `seed43_sigreg_off_real_action`
- `seed43_sigreg_off_zero_action`
- `seed44_sigreg_on_real_action`
- `seed44_sigreg_on_zero_action`
- `seed44_sigreg_off_real_action`
- `seed44_sigreg_off_zero_action`

Each variant output directory is expected to contain the normal `train_lewm` artifacts produced by
the repository training path.
