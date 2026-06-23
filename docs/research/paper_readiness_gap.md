# Paper Readiness Gap

Date: 2026-06-23

## Ready Now

- Evidence-governed pipeline and claim-control infrastructure.
- Provenance-bound TempGlitch R5 documentation and bounded non-locked findings.
- Validated `R5-WOB` positive-probe bundle with explicit limitations.
- Frozen `R5-XGame` split, runner, Kaggle launcher, validator, and execution docs.
- Paper scaffolding work: method/protocol text, related-work refresh, limitations framing,
  reviewer FAQ, figure/table shells, and submission memo.

## Not Ready Yet

- A valid WOB/XGame binary results table.
- Final abstract or conclusion with empirical headline metrics.
- Cross-source comparison claims.
- Baseline or ablation conclusions derived from `R5-XGame`.
- Any claim of superiority, state of the art, temporal localization, SIGReg benefit,
  action-conditioning benefit, or locked-test readiness.

## Governing Distinction

Engineering readiness is not the same as scientific-evidence readiness.

- `R5-WOB` is engineering-ready and signal-validating, but not binary-benchmark-ready.
- `R5-XGame` is execution-ready in tooling terms, but not claim-ready in scientific terms until
  the downloaded bundle passes intake validation.

## Exit Condition For Paper-Ready Results

Paper-facing main results become eligible only after:

1. the Phase B output tarball, SHA256 sidecar, and log are downloaded;
2. `scripts/validate_r5_xgame_output_bundle.py` passes;
3. claim registry, current-state, and paper claim map are refreshed from the validated bundle;
4. the results are written with the documented non-locked boundary still explicit.
