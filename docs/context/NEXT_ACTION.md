# NEXT_ACTION.md

Last updated: 2026-06-25T04:06:16+00:00
Commit: `7875c492883562001c1eaeeb55efe31a2d79b507`

## Current Priority
Stop at roadmap V4 Kaggle gate K3. The local K3 train/validation inputs are prepared, the dry-run
matrix passed, and the refreshed package is ready for a user-operated Kaggle run. Authority
roadmap: `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (Phase P4, Kaggle K3, user-operated)
1. Upload `outputs/k3_kaggle_package/lewm_k3_sigreg_action_ablation_package.zip` to Kaggle and
   unzip it into the working directory.
2. Run `kaggle/k3_sigreg_action_ablation/run_k3_ablation.py` with `--device cuda`.
3. Download the K3 output bundle and validate it locally with
   `scripts/ingest_k3_ablation_bundle.py`.
4. Register no SIGReg or action-conditioning claim unless the downloaded K3 bundle intake-validates.

## Success Criteria
- The user-operated Kaggle run completes all 12 variants.
- The Kaggle-facing runner enforces false locked-test flags plus exact dataset-hash matching.
- The eventual downloaded Kaggle bundle contains all 12 variants and passes
  `scripts/ingest_k3_ablation_bundle.py`.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After K3
P5 temporal localization (Kaggle K4 optional), P6 demo, P7 full paper rewrite. Earlier phases
K1-K2 are already artifact-backed on this branch.

## Current Known Blocker
No local input blocker remains for K3. The remaining blocker is the external user-operated Kaggle
scientific run and local intake validation of the downloaded bundle. Locked test remains closed.
