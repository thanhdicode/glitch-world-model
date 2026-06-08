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

- Current readiness score: `6/10`.
- Phase 0 pipeline exists and is locally verified.
- Phase 1 literature and source verification is now substantially stronger.
- TempGlitch public access is now verified through a public Hugging Face dataset artifact under MIT license.
- The repo now has a real TempGlitch smoke pipeline on a tiny public subset.
- Real LeWM integration is still absent by design.
- Public benchmark evidence now includes the two-video smoke subset and a preliminary 30-video split experiment.
- The repo now has a leakage-aware 30-video TempGlitch split experiment across all five public categories.
- Thresholds are calibrated on validation and applied unchanged to test.
- `feature_distance` and `mini_latent` fit on train-normal clips only.
- Current 30-video results are weak and preliminary; test AUROC ranges from approximately `0.522` to `0.589`.
- The verified public TempGlitch artifact currently exposes binary per-video labels and one public `train` split, not a verified official held-out split or finer temporal-span file.

## 3. What is enough for a short paper

- A precise problem statement.
- A clean reproducible baseline pipeline.
- Honest synthetic and toy-dynamics sanity checks.
- A narrow claim such as:
  - "we present a reproducible baseline pipeline and motivate latent-surprise scoring for future gameplay glitch detection"
- Careful limitation language that avoids benchmark-performance claims.

## 4. What is required for a full paper

- Verified literature that supports the motivation, benchmark choice, baseline families, and limitations.
- At least one verified public gameplay-video benchmark with documented source URL, access date, and permitted use.
- A documented split protocol with no leakage across overlapping clips or paired near-duplicates, even if the benchmark does not ship an official held-out split.
- Actual public-benchmark results for `frame_diff`, `feature_distance`, and `mini_latent`.
- At least one clear failure-analysis section beyond headline metrics.
- Reproducible commands that regenerate every table and figure cited in the paper.
- If the paper claims temporal localization rather than binary clip-level detection, a benchmark with verified public span annotations is still required.
- Results must extend beyond a smoke subset to a more meaningful benchmark slice.
- The current 30-video slice must be scaled and analyzed by category / failure mode.

## 5. Minimum experiment package for a full paper

- Benchmark package:
  - TempGlitch for binary clip-level gameplay-glitch detection if the repo defines and documents a leakage-safe local split.
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
- TempGlitch public access is solved, but the public artifact is binary per-video and single-split.
- Image-only evidence from GlitchBench cannot support temporal localization claims.
- World of Bugs requires additional setup and label conversion effort.
- Cross-game generalization remains unproven until multiple public benchmarks or games are evaluated.
- Temporal localization claims remain unproven until a public span-annotated benchmark is executed.

## 10. Go / No-Go criteria before writing full paper

### Go

- A public gameplay-video benchmark is verified, downloaded locally under gitignored paths, and converted into the repo CSV interfaces.
- The repo has benchmark results for all current baselines.
- Split protocol, threshold protocol, and figure / table provenance are documented.
- At least two ablations and one error-analysis section are complete.
- If claiming localization, public span annotations are verified and executed.

### No-Go

- Benchmark access is still paper-only.
- Labels are still not mapped into `source,start_frame,end_frame,label`.
- Results come only from synthetic, toy, or tiny smoke subsets.
- The paper would have to rely on static-image evidence to stand in for temporal detection.

## Decision

- Decision class: B. Full-paper path risky, short-paper path safer.
- Why:
  - TempGlitch now has a verified public artifact and is strong enough for binary clip-level benchmark work.
  - The repo now proves that the TempGlitch smoke path is operational end-to-end.
  - The repo now has a leakage-aware train / validation / test protocol and preliminary results for all three current baselines.
  - The current 30-video results do not support mini-latent superiority and have weak discrimination.
  - TempGlitch's current public artifact does not by itself verify finer temporal spans or an official held-out split.
  - VideoGlitchBench is rich on paper, but public code/data release is still unverified.
  - GlitchBench is accessible but static-image only.
  - World of Bugs is promising but operationally heavier and not yet mapped into this repo's CSV interfaces.
- Practical implication:
  - The next step is Phase 3B: scale the split and add per-category / failure analysis before deciding whether ablations are justified.
