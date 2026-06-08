# Full Paper Readiness Gap Analysis

## 1. FISAT full paper requirements

- Venue: EAI FISAT 2026.
- Submission deadline: 2026-07-20.
- Acceptance notification: 2026-09-15.
- Camera-ready deadline: 2026-10-15.
- Full / regular paper length: 12-20 pages excluding appendices, references, and acknowledgements.
- Short paper length: 6-11 pages excluding appendices, references, and acknowledgements.
- Language: English.
- Format: Springer Authors' Kit / LNCS-style proceedings templates.
- Submission system: Confy+.
- Review model: Single-blind.
- Accessibility constraint: descriptive text / alt text is required for figures, tables, illustrations, and images.

## 2. Current repo status

- Phase 0 pipeline exists and is locally verified.
- Phase 1 literature and source verification is now substantially stronger.
- Real LeWM integration is still absent by design.
- No public temporal benchmark has yet been downloaded, converted, or evaluated in this repo.
- The repo currently has only synthetic and toy-dynamics evidence.

## 3. What is enough for a short paper

- A precise problem statement.
- A clean reproducible baseline pipeline.
- Honest synthetic and toy-dynamics sanity checks.
- A narrow claim such as:
  - "we present a reproducible baseline pipeline and motivate latent-surprise scoring for future gameplay glitch detection"
- Careful limitation language that avoids benchmark-performance claims.

## 4. What is required for a full paper

- Verified literature that supports the motivation, benchmark choice, baseline families, and limitations.
- At least one verified public temporal benchmark with documented source URL, access date, and permitted use.
- A verified train / validation / test or cross-video split with no leakage across overlapping clips.
- Actual public-benchmark results for `frame_diff`, `feature_distance`, and `mini_latent`.
- At least one clear failure-analysis section beyond headline metrics.
- Reproducible commands that regenerate every table and figure cited in the paper.

## 5. Minimum experiment package for a full paper

- Benchmark package:
  - TempGlitch if its direct public access path and label format are verified in Phase 2.
  - Otherwise a documented fallback, likely World of Bugs or a clearly limited GlitchBench image-only section.
- Baselines:
  - `frame_diff`
  - `feature_distance`
  - `mini_latent`
- Ablations:
  - clip length / stride sensitivity
  - score thresholding or smoothing choice
  - at least one mini-latent design ablation
- Analysis:
  - per-category or failure-mode breakdown
  - qualitative timeline plots or clip examples
  - explicit false-positive and false-negative discussion

## 6. Must-have tables

- Dataset provenance table:
  - source URL, access date, license / permitted use, split protocol
- Main metrics table:
  - scorer vs benchmark metrics, with exact `metrics.json` provenance
- Ablation table:
  - clip construction and scorer-design changes
- Error-analysis table:
  - failure modes by glitch category or scene type

## 7. Must-have figures

- End-to-end pipeline figure from preprocess -> score -> evaluate -> report.
- Benchmark example figure with normal and glitch intervals.
- Score-timeline plots for representative successes and failures.
- Failure-case montage showing where simple visual baselines and `mini_latent` differ.

## 8. Must-have ablations

- Clip length and stride.
- Score aggregation choice.
- `mini_latent` latent dimension or transition-model setting.
- Threshold-selection protocol, clearly separated from test evaluation.

## 9. Must-have limitations

- `mini_latent` is a proxy, not LeWM.
- Public temporal benchmark access was the main gating factor for the full-paper path.
- Image-only evidence from GlitchBench cannot support temporal localization claims.
- World of Bugs requires additional setup and label conversion effort.
- Cross-game generalization remains unproven until multiple public benchmarks or games are evaluated.

## 10. Go / No-Go criteria before writing full paper

### Go

- A public temporal benchmark is verified, downloaded locally under gitignored paths, and converted into the repo CSV interfaces.
- The repo has benchmark results for all current baselines.
- Split protocol, threshold protocol, and figure / table provenance are documented.
- At least two ablations and one error-analysis section are complete.

### No-Go

- Benchmark access is still paper-only.
- Labels are still not mapped into `source,start_frame,end_frame,label`.
- Results come only from synthetic or toy data.
- The paper would have to rely on static-image evidence to stand in for temporal detection.

## Decision

- Decision class: B. Full-paper path risky, short-paper path safer.
- Why:
  - TempGlitch is the best benchmark on paper, but direct public access was not verified during Phase 1.
  - VideoGlitchBench is rich on paper, but public code/data release was also unverified.
  - GlitchBench is accessible but static-image only.
  - World of Bugs is promising but operationally heavier and not yet mapped into this repo's CSV interfaces.
- Practical implication:
  - Phase 2 should focus first on benchmark access verification and conversion, not on broad model expansion.
