# Paper Readiness Gap

Date: 2026-06-23

## Ready Now

- Evidence-governed pipeline and claim-control infrastructure.
- Provenance-bound TempGlitch R5 documentation and bounded non-locked findings.
- Validated `R5-WOB` positive-probe bundle with explicit limitations.
- Validated `R5-XGame` output-dir and tarball intake with a bounded non-locked binary result
  summary.
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

Engineering readiness is not the same as broad paper-readiness.

- `R5-WOB` is engineering-ready and signal-validating, but not binary-benchmark-ready.
- `R5-XGame` now has claim-ready intake receipts and a bounded non-locked validation summary, but
  it remains a frozen 12-negative / 60-positive split rather than proof of broad generalization.

## Exit Condition For Broader Paper-Ready Results

Broader paper-facing main results become eligible only after:

1. the validated `R5-XGame` bundle is the cited source, not remote status or partial logs;
2. claim registry, current-state, and paper claim map remain synchronized to that validated
   bundle;
3. any cross-source or final-table claim adds separately validated matching evidence;
4. the documented non-locked boundary and evaluation-set limitations remain explicit.
