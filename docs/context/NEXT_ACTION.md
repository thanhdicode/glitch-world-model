# NEXT_ACTION.md

Last updated: 2026-06-25T00:00:00+00:00
Commit: `6f4bfe99742a9a376b8a16369eb1658982177221`

## Current Priority
Advance from validated P3/K2 intake to Phase P4 controlled ablations. The downloaded scientific K2
bundle is now locally SHA256-verified and intake-validated, so the next roadmap task is no longer a
K2 rerun. The next external gate is Kaggle K3 on the controlled SIGReg and action-conditioning
matrix defined in `scripts/run_r6_sigreg_ablation.py`.
Authority roadmap: `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (User-Operated Kaggle K3)
1. Confirm the train and validation inputs for the controlled ablation lane.
2. Run the K3 dry-run defined in `docs/research/123_kaggle_k3_ablation_runbook.md`.
3. Launch the scientific K3 job for seed42/43/44 with the full `sigreg_on/off x real/zero_action`
   matrix.
4. Download the K3 output bundle and validate it locally before any SIGReg or action-conditioning
   claim enters the claim registry.

## Success Criteria
- all 12 controlled variants complete
- `validate_r6_ablations.py` accepts the declared controlled pairs
- locked test remains closed
- K3 artifacts validate locally before any mechanistic claim expands

## Phase Sequence After This Task
P4 controlled SIGReg/action ablation artifact run (Kaggle K3), P5 temporal localization or
explicit future-work scoping, P6 demo, P7 full paper rewrite.

## Current Known Blocker
K3 remains user-operated on Kaggle and still needs a downloaded post-run artifact before any
SIGReg or action-conditioning statement is allowed. GlitchBench remains image-level and
synthetic-normal, so K2 does not unlock temporal-localization or broad generalization language.
Locked test remains closed.
