# 123 - Kaggle K3 Ablation Runbook

Date: 2026-06-25
Status: next external gate after validated K2 intake

## Scope

K3 is the Phase P4 controlled ablation gate from
`docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`. It is not a benchmark-expansion job. Its purpose
is to test two mechanism questions under controlled pairs:

- SIGReg on vs SIGReg off
- real action conditioning vs zero action

## Guardrails

- Keep locked test closed.
- Use the same train and validation data across each controlled pair.
- Keep the same seed within each controlled pair.
- Change exactly one variable per pair.
- Report positive or negative outcomes honestly.
- Do not claim SIGReg or action-conditioning benefit until the downloaded K3 artifact validates.

## Local Entry Points

- Runner: `scripts/run_r6_sigreg_ablation.py`
- Validator: `scripts/validate_r6_ablations.py`

The current runner already materializes the full `seed42/43/44 x sigreg_on/off x real/zero_action`
matrix and writes:

- `r6_ablation_plan.json`
- `r6_controlled_pairs.json`
- `r6_ablation_receipt.json`

## Dry-Run Command

```bash
python scripts/run_r6_sigreg_ablation.py \
  --train-path <TRAIN_LANCE_OR_MANIFEST> \
  --validation-path <VALIDATION_LANCE_OR_MANIFEST> \
  --output-root outputs/r6_sigreg_ablation \
  --device cpu \
  --dry-run
```

Expected dry-run status:

- `dry_run_ready`

## Scientific K3 Command

```bash
python scripts/run_r6_sigreg_ablation.py \
  --train-path <TRAIN_LANCE_OR_MANIFEST> \
  --validation-path <VALIDATION_LANCE_OR_MANIFEST> \
  --output-root outputs/r6_sigreg_ablation \
  --seeds 42 43 44 \
  --device cuda
```

Current default training controls:

- `target_optimizer_updates=500`
- `evaluation_interval_updates=100`
- `checkpoint_interval_updates=100`
- `image_size=112`
- `history_size=3`
- `embed_dim=192`
- `batch_size=4`
- `learning_rate=5e-5`
- `weight_decay=1e-3`
- `sigreg_weight=0.09`
- `sigreg_projections=128`

## Local Validation Command

```bash
python scripts/validate_r6_ablations.py \
  --output-dir outputs/r6_sigreg_ablation
```

Expected validation surface:

- controlled pairs detected
- identical dataset hashes within each pair
- identical seed within each pair
- only `sigreg_enabled` differs for SIGReg pairs
- only `action_mode` differs for action-conditioning pairs
- `locked_test_materialized=false`
- `locked_test_scored=false`

## Acceptance Criteria

- all 12 controlled variants complete
- all declared controlled pairs validate
- no locked-test access
- artifact is downloaded and intake-validated locally before any claim registry expansion

## Claim Boundary

Allowed after validated K3 intake only:

- bounded split-specific observations about SIGReg on/off
- bounded split-specific observations about real-action vs zero-action conditioning
- honest negative conclusions if no measurable effect is observed

Forbidden until validated K3 intake:

- any SIGReg benefit statement
- any action-conditioning benefit statement
- any causal mechanism claim beyond the validated split
