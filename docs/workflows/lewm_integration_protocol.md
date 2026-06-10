# LeWM Integration Protocol

Real LeWM integration is a future phase. Do not implement or fine-tune it under this protocol.

Before implementation:

1. Audit upstream license, commit, checkpoint provenance, and supported tasks.
2. Document environment and dependency compatibility.
3. Map gameplay clips to expected preprocessing, shape, normalization, and temporal stride.
4. Define a pluggable scorer contract without changing existing CSV interfaces.
5. Prove checkpoint loading and inference on non-locked validation data.
6. Add tests for shape, determinism, error handling, and no-test access.
7. Record metrics and limitations before changing claim status.

`mini_latent` remains a proxy. External source presence does not prove integration.
