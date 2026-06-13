# Expected R3 Seed 42 Artifacts

The artifact root is `$LEWM_OUTPUT_ROOT`.

Required before full training:

- `cloud_runtime_preflight.json`
- `preflight_passed.json`

Required after full training:

- `training_metadata.json`
- `loss_history.json`
- `validation_history.json`
- `collapse_diagnostics.json`
- `checkpoint_weights.pt`
- `weights.pt`
- `best_weights.pt`
- `best_checkpoint_metadata.json`
- `cloud_runtime_preflight.json`
- `preflight_passed.json`
- `r3_seed42_run.log`

Validation command:

```bash
python scripts/validate_lewm_r3_seed_artifacts.py \
  --artifact-root "$LEWM_OUTPUT_ROOT" \
  --expected-seed 42 \
  --expected-target-updates 15000
```
