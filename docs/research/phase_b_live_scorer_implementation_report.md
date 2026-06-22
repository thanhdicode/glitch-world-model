# Phase B Live Scorer Implementation Report

Status before commit: implementation prepared in the working tree on `main` after
`e09f596 Wire fresh R5-XGame seed training wrapper`.

## Summary

- Real staged R5-XGame orchestration is implemented in `scripts/run_r5_xgame_staged.py`.
- Fresh seed42/43/44 training is wired through `train_fresh_seed`, which calls the real
  `LeWMTrainConfig` / `train_lewm` API with a 15,000-update research target and validation-only
  early stopping.
- Old R5-WOB checkpoint or seed-artifact mounts are rejected during preflight.
- Kaggle input resolution uses the WOB normal/test roots and the frozen 120-row manifest.
- Local dry-run is expected to report missing inputs unless the machine has Kaggle-style WOB tar
  coverage mounted.

## Required Kaggle Roots

- `benedictwilkinsai/world-of-bugs-normal`, root containing `NORMAL-TRAIN/`.
- `benedictwilkinsai/world-of-bugs-test`, root containing `TEST/`.

## Kaggle Command

```bash
cd /kaggle/working/glitch-world-model
bash cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh
```

## Download After Run

- `/kaggle/working/r5_xgame/r5_xgame_outputs.tar.gz`
- `/kaggle/working/r5_xgame/r5_xgame_outputs.tar.gz.sha256`
- `/kaggle/working/r5_xgame_staged.log`

## Claim Boundary

Allowed now: code/package readiness for a non-locked R5-XGame Kaggle operation.

Still forbidden: WOB/XGame performance claims, superiority, state of the art, cross-game
generalization, action-conditioning benefit, SIGReg benefit, temporal localization, and any locked
test claim.
