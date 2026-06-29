# Figure Provenance

Store only small, publication-ready figures with documented provenance. For every figure record:

- source script and command
- input metrics or artifact path
- split and seed
- generation date
- claim-registry IDs supported

Do not commit raw data, model checkpoints, or exploratory output directories here.

## Timeline Figure Status

`fig_timeline_example.pdf` and `fig_timeline_example.png` are publication-ready qualitative-only
figures generated from validated non-locked TempGlitch window-score artifacts. The corresponding
receipt is `fig_timeline_example_receipt.json` and records `temporal_metrics_claimed=false`,
`ground_truth_spans_available=false`, and `locked_test_used=false`.
