# 105 - Kaggle Gate Decision Memo

Date: 2026-06-24
Decision: first paper draft remains local; new empirical strengthening requires a separate compute decision

## No Kaggle Needed

- evidence registration and hash preservation;
- paper tables, limitations, and claim registry;
- LNICST outline and first bounded draft;
- failure analysis from existing outputs;
- figures and temporal smoothing derived from existing scores, provided no new score generation or
  claim expansion occurs;
- reproducibility and reviewer-risk audits.

## Kaggle Or Equivalent New Compute Needed

- LeWM retraining or new model seeds beyond existing artifacts;
- autoencoder or other learned-baseline training on exact support;
- CNN/3D-CNN baseline experiments;
- controlled SIGReg on/off or action-conditioning ablations;
- full VideoGlitchBench execution;
- new WOB/XGame scoring;
- comparable GPU inference-FPS measurement if no suitable local GPU is available.

## Gate Decision

The next task is local: build the first paper draft from the bounded TempGlitch and R5-XGame
evidence package. No Kaggle launch is required for that task.

Stop and ask the user only when deciding whether to launch a new compute phase for stronger
baseline/ablation evidence.

Locked-test access remains a separate gate and is not authorized by a future Kaggle decision.
