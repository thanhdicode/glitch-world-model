# NEXT_ACTION.md

Last updated: 2026-06-25T04:06:16+00:00
Commit: `7875c492883562001c1eaeeb55efe31a2d79b507`

## Current Priority
Stop at roadmap V4 Kaggle gate K3. The local K3 packaging path is prepared, but the exact
R5-XGame raw/source archives required to materialize the non-locked train and validation Lance
inputs are missing on this machine. Authority roadmap:
`docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (Phase P4, Kaggle K3, user-operated after local inputs exist)
1. Place the required non-locked R5-XGame raw/source episode archives under one supported input
   root so `scripts/prepare_k3_ablation_inputs.py` can materialize:
   `outputs/r5_xgame/_r5_xgame_train_normal.lance` and
   `outputs/r5_xgame/_r5_xgame_calibration_eval_normal.lance`.
2. Re-run `python scripts/prepare_k3_ablation_inputs.py` and confirm
   `outputs/k3_ablation_inputs/k3_input_manifest.json` reports `status=ready`.
3. Upload the local K3 package skeleton to Kaggle, run the ablation matrix there, then download
   the bundle and validate it locally with `scripts/ingest_k3_ablation_bundle.py`.
4. Register no SIGReg or action-conditioning claim unless the downloaded K3 bundle intake-validates.

## Success Criteria
- The required R5-XGame train and validation Lance directories exist locally and are hash-recorded
  in `outputs/k3_ablation_inputs/k3_input_manifest.json`.
- The local K3 package path is complete and the Kaggle-facing runner still enforces false
  locked-test flags plus exact dataset-hash matching.
- The eventual downloaded Kaggle bundle contains all 12 variants and passes
  `scripts/ingest_k3_ablation_bundle.py`.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After K3
P5 temporal localization (Kaggle K4 optional), P6 demo, P7 full paper rewrite. Earlier phases
K1-K2 are already artifact-backed on this branch.

## Current Known Blocker
K3 is blocked locally by missing raw/source R5-XGame inputs. The exact missing paths are recorded in
`outputs/k3_ablation_inputs/k3_input_manifest.json` and
`outputs/k3_ablation_inputs/K3_INPUTS_REPORT.md`. Locked test remains closed.
