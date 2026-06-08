# Paper Outline

## Title

Latent World Models for Video Game Glitch Detection: A JEPA-based Approach

## Abstract draft

Video game glitches often appear as violations of expected visual and physical dynamics rather than isolated abnormal frames. This paper studies glitch detection as a latent prediction problem: a world model trained or adapted on normal gameplay should assign high prediction error to clips containing abnormal transitions. We present a reproducible Python pipeline for preprocessing gameplay clips, scoring anomalies, evaluating interval labels, and comparing baselines. Current experiments use frame difference, RGB feature distance, and a lightweight PCA latent transition model as baselines and proxies for latent surprise. Future work integrates a LeWorldModel-style JEPA encoder and predictor while preserving the same evaluation interface. The goal is to provide a practical research path for temporal glitch detection in games with careful separation between synthetic sanity checks and public benchmark evidence.

## 1. Introduction

- Motivation: QA for complex games is difficult and rare glitches are costly.
- Static anomaly detection misses temporal failures.
- Latent world models offer a dynamics-aware framing.
- Contributions: pipeline, baseline comparison, dataset strategy, LeWM integration plan.

## 2. Related Work

- Automated bug detection in video games.
- World of Bugs and game QA benchmarks.
- GlitchBench and multimodal glitch detection.
- Temporal gameplay glitch benchmarks such as TempGlitch and VideoGlitchBench.
- Video anomaly detection via prediction/reconstruction.
- JEPA and latent world models.

## 3. Method

- Clip generation and manifest format.
- Baseline scorers.
- Mini latent transition model.
- Future LeWM latent prediction error method.
- Scoring and thresholding.

## 4. Experiments

- Synthetic sanity check.
- Easy and hard dynamics generated datasets.
- GlitchBench subset image-oriented demo.
- Future World of Bugs and temporal benchmark experiments.
- Metrics and file outputs.

## 5. Results

- Report metrics tables.
- Compare baselines.
- Include score plots.
- Separate synthetic from benchmark results.
- Avoid SOTA claims unless benchmark protocol is verified.

## 6. Discussion

- What latent prediction error captures.
- Where visual baselines are enough.
- Failure cases in high-motion normal gameplay.
- Generalization across games.

## 7. Limitations

- Dataset access.
- Temporal labels.
- Compute constraints.
- LeWM integration not yet complete.
- Synthetic data limits.

## 8. Conclusion

- Summarize why dynamics-aware glitch detection is promising.
- State the practical value of the reproducible pipeline.
- Outline next steps toward real LeWM evaluation.

## Fit for FISAT / student research paper

Keep the first version focused: a clear problem framing, honest baselines, reproducible commands, and a modest future-work section are stronger than overclaiming incomplete model integration.
