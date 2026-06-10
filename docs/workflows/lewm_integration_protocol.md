# LeWM Integration Protocol

Real LeWM integration is the mandatory main-method path. Implementation and fine-tuning may
begin only after the relevant audit and data-contract gates pass.

Before implementation:

1. Audit upstream license, commit, checkpoint provenance, and supported tasks.
2. Document environment and dependency compatibility.
3. Map gameplay clips to expected preprocessing, shape, normalization, and temporal stride.
4. Define a pluggable scorer contract without changing existing CSV interfaces.
5. Prove checkpoint loading and inference on non-locked validation data.
6. Add tests for shape, determinism, error handling, and no-test access.
7. Record metrics and limitations before changing claim status.

`mini_latent` remains a proxy. External source presence does not prove integration.

The official upstream training path is action-conditioned. Video-only zero-action or
action-free adaptations must be named explicitly and must not be described as the unchanged
action-conditioned LeWM method.

Implementation order and acceptance gates are defined in
`docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v2.md`.
