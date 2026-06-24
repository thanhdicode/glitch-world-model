# NEXT_ACTION.md

Last updated: 2026-06-24T08:42:16+00:00
Commit: `940b8d60bb036934ebceeb8f2ca2cc910e65011a`

## Current Priority
Stop at roadmap V4 Kaggle gate K1. Phase P2 local preparation is complete; the next action is a
user-operated Kaggle run of the three learned video baselines on the frozen follow-up support.
Authority roadmap: `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (Phase P2, Kaggle K1, user-operated)
1. Materialize the frozen follow-up inputs inside Kaggle: combined manifest, grouped split, and
   clip root containing the train-normal and validation episodes only.
2. Run `scripts/run_kaggle_learned_baselines.py` to train/fit and score
   `video_autoencoder`, `cnn_lstm`, and `video_transformer` on the same support.
3. Download the artifact directory and run `scripts/validate_learned_baselines.py`.
4. Register only artifact-backed learned-baseline claims after the validator passes.

## Success Criteria
- The Kaggle output contains all three checkpoints, per-baseline metadata/scores, and SHA256
  sidecars.
- Validation still uses the same frozen follow-up support with zero cross-split leakage and false
  locked-test flags.
- The downloaded artifact directory passes `scripts/validate_learned_baselines.py`.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After K1
P3 GlitchBench benchmark (Kaggle K2), P4 SIGReg/action ablation (Kaggle K3), P5 temporal
localization (Kaggle K4 optional), P6 demo, P7 full paper rewrite.
Codex does every local task autonomously and stops only at Kaggle gates K1-K4.

## Current Known Blocker
K1 requires an external Kaggle notebook run and its downloaded artifacts. The official Springer kit
/ TeX toolchain blocker still only applies later at P7. Locked test remains closed.
