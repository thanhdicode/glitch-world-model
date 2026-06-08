# Claim Registry

Track every paper-facing claim here before it appears in the manuscript.

| Claim ID | Claim text | Type | Evidence source | Status | Where used in paper | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| C-001 | The current repo provides a reproducible preprocess -> score -> evaluate -> report pipeline. | method | README, source modules, tests, Phase 0 verification docs | verified | Method / Reproducibility | Repo-local claim only. |
| C-002 | `mini_latent` is a lightweight latent-dynamics proxy, not a real LeWorldModel integration. | method | `src/glitch_detection/mini_latent.py`, `src/glitch_detection/lewm_latent.py`, [S-002](17_source_verification_log.md) | verified | Method / Limitations | Keep wording strict. |
| C-003 | Synthetic and generated datasets in this repo are sanity checks only, not benchmark evidence. | limitation | research docs, scripts, AGENTS.md | verified | Experiments / Limitations | Prevents overclaiming from toy data. |
| C-004 | Raw datasets, generated outputs, checkpoints, `.test-tmp`, and cache folders must stay uncommitted. | reproducibility | `.gitignore`, AGENTS.md, repo workflow docs | verified | Reproducibility | Recheck before any commit. |
| C-005 | No state-of-the-art claim should be made until the repo has comparable public-benchmark evidence under a verified protocol. | limitation | [S-003](17_source_verification_log.md), [S-004](17_source_verification_log.md), workflow docs | verified | Abstract / Discussion | Applies even if synthetic results look strong. |
| C-006 | EAI FISAT 2026 requires English submission in Springer format through Confy+, with full papers at 12-20 pages and short papers at 6-11 pages, under single-blind review. | background | [S-001](17_source_verification_log.md) | verified | Venue / Reproducibility | Also note the alt-text accessibility requirement. |
| C-007 | The MVP scorer set in this repo is `frame_diff`, `feature_distance`, `mini_latent`, plus a guarded `lewm_latent` placeholder. | method | scorer registry and source code | verified | Method / Experiments | Preserve registry compatibility. |
| C-008 | LeWorldModel has official code, datasets, and pretrained checkpoints, but this repo has not integrated those artifacts into `lewm_latent` yet. | method | [S-002](17_source_verification_log.md), current source tree | verified | Method / Future Work | Do not imply runtime integration. |
| C-009 | TempGlitch is the best thematic benchmark target for temporal gameplay glitch detection, but its direct public download path is still unverified in this repo as of 2026-06-08. | benchmark | [S-003](17_source_verification_log.md) | verified | Benchmark selection / Limitations | Safe benchmark-target wording. |
| C-010 | VideoGlitchBench provides temporally grounded glitch descriptions on paper, but public code/data access remained unverified on 2026-06-08. | benchmark | [S-004](17_source_verification_log.md) | verified | Related Work / Limitations | Good fallback candidate, not yet an executable one. |
| C-011 | GlitchBench is an image-level benchmark and should not be used to claim temporal glitch localization performance. | benchmark | [S-005](17_source_verification_log.md) | verified | Related Work / Limitations | Paper and HF artifact both support static-image usage. |
| C-012 | World of Bugs is a platform/environment for automated bug detection research, not a drop-in benchmark already aligned with this repo's CSV interfaces. | benchmark | [S-006](17_source_verification_log.md) | verified | Related Work / Future Work | Requires later conversion and setup work. |
| C-013 | JEPA-family and world-model sources support latent prediction and video representation learning as background, but they do not by themselves prove gameplay glitch detection performance. | background | [S-007](17_source_verification_log.md), [S-008](17_source_verification_log.md), [S-009](17_source_verification_log.md) | verified | Introduction / Related Work | Keeps novelty claims safe. |
| C-014 | Latent prediction error will outperform simpler visual baselines on gameplay glitches. | experiment | no benchmark result yet | experiment-pending | Experiments / Discussion | This remains a hypothesis, not a verified claim. |
| C-015 | This repo does not introduce a new public dataset, benchmark, or public LeWM checkpoint release. | limitation | current repo contents plus [S-002](17_source_verification_log.md) through [S-006](17_source_verification_log.md) | verified | Contributions / Limitations | Explicit anti-overclaim guardrail. |
| C-016 | Any paper-facing public-benchmark result must cite the exact source URL, access date, split protocol, and produced `metrics.json`. | reproducibility | reproducibility checklist and Phase 1 verification log | verified | Reproducibility | Treat as a release gate, not a nice-to-have. |

## Status meanings

- `verified`: supported by current repo artifacts or a verified external source.
- `experiment-pending`: requires an experiment that has not been run in this repo.
- `citation-needed`: requires a source that is not yet verified.
- `rejected`: should not be used.
