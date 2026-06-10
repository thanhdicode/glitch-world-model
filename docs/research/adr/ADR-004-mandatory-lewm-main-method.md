# ADR-004: Mandatory Real LeWM Main Method

## Status

Accepted

## Decision

Real LeWorldModel integration is the mandatory main-method path. `mini_latent` remains a sanity
check and emergency fallback only. The paper must not use a LeWM-based title or contribution
claim until checkpoint loading, training or fine-tuning, latent inference, surprise scoring, and
glitch evaluation are all verified by artifacts.

## Technical Interpretation

The official LeWM training path is action-conditioned. A video-only adaptation may use a
documented zero-action or action-free adapter, but the paper must call it an
`action-agnostic LeWM adaptation`, not the unchanged action-conditioned LeWM method.

The preferred progression is:

1. Verify an official pretrained checkpoint can be reconstructed and loaded.
2. Verify official-environment inference with matching actions.
3. Train an action-agnostic LeWM adaptation on normal gameplay video.
4. If feasible, generate or collect action-logged gameplay and train the original
   action-conditioned formulation.

## Consequences

- Kaggle GPU is the primary training backend after local CPU smoke tests.
- Real LeWM work is blocked until the data/API audit and converter tests pass.
- Checkpoints, datasets, credentials, and generated outputs remain gitignored.
- Locked test remains closed until a validation decision and explicit approval exist.
- If real LeWM gates fail before the paper deadline, the paper must be reframed without a
  LeWM-based title or claim.
