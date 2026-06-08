# Claim Registry

Track every paper-facing claim here before it appears in the manuscript.

| Claim ID | Claim text | Type | Evidence source | Status | Where used in paper | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| C-001 | The current repo provides a reproducible preprocess -> score -> evaluate -> report pipeline. | method | README, source modules, pytest run | verified | Method / Reproducibility | Verified locally in Phase 0. |
| C-002 | `mini_latent` is a lightweight latent-dynamics proxy, not real LeWorldModel. | method | `mini_latent.py`, `lewm_latent.py`, research docs | verified | Method / Limitations | Keep wording precise. |
| C-003 | Synthetic results are sanity checks only and not benchmark evidence. | limitation | research docs and roadmap policy | verified | Experiments / Limitations | Prevents overclaiming. |
| C-004 | Raw datasets and checkpoints are not committed. | reproducibility | `.gitignore`, git status checks | verified | Reproducibility | Recheck before release. |
| C-005 | No state-of-the-art claim should be made until public benchmark results exist. | limitation | risk docs | verified | Abstract / Discussion | Strong guardrail for FISAT draft. |
| C-006 | TempGlitch is the target benchmark for later phases. | experiment | roadmap and TempGlitch plan | experiment-pending | Experiments | Access and format remain `TBD / verify`. |
| C-007 | `frame_diff`, `feature_distance`, and `mini_latent` are the MVP baselines. | method | scorer registry | verified | Method / Experiments | Preserve registry compatibility. |
| C-008 | Latent prediction error may capture temporal dynamics violations better than static frame features. | background | literature review and future experiments | citation-needed | Introduction / Related Work | Needs verified citations and benchmark results. |
| C-009 | The synthetic demo achieves F1 > 0 in the current environment. | experiment | `outputs/synthetic_metrics.json` from Phase 0 | verified | Internal report only | Do not use as benchmark evidence. |
| C-010 | Real LeWM integration is future work. | limitation | guarded `lewm_latent.py` and ADR-003 | verified | Limitations / Future Work | Update only after actual implementation. |

## Status meanings

- `verified`: supported by current repo artifacts or verified source.
- `experiment-pending`: requires an experiment that has not been run.
- `citation-needed`: requires external source verification.
- `rejected`: should not be used.
