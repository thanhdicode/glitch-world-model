# Risks and Limitations

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| Dataset access risk | New gameplay glitch benchmarks may have limited access, licenses, or large files. | Treat dataset acquisition as a separate task; document source, license, and version. |
| Temporal label availability | Clip-level metrics are weaker than event-level temporal localization. | Prefer benchmarks with temporal spans; clearly state when labels are interval-derived. |
| GlitchBench ground-truth limitation | GlitchBench is valuable but may emphasize static visual recognition rather than temporal dynamics. | Use it for image-level evidence only; do not overclaim temporal performance from it. |
| Overfitting to synthetic data | Toy datasets can make simple baselines look stronger than they are. | Label synthetic results as sanity checks and validate on public benchmarks. |
| LeWM integration complexity | Real LeWM scoring may require checkpoints, GPU support, and model-specific preprocessing. | Keep `mini_latent` as proxy until docs, baselines, and reproducibility are stable. |
| Compute limitations | Video models can be expensive to train or run. | Start with frozen encoders, small clips, lightweight baselines, and subset experiments. |
| False positives in high-motion normal gameplay | Motion-heavy scenes can look anomalous under simple difference scores. | Compare against feature and latent baselines; include normal high-motion cases. |
| Domain shift across games | A model adapted on one game may not generalize to another. | Report per-game splits and avoid broad claims until cross-game evaluation exists. |
| Ambiguous glitches | Some unusual game events are valid mechanics. | Use benchmark annotations and, where possible, natural-language descriptions. |
| No SOTA claim yet | Current repo has MVP baselines, not verified benchmark results. | Phrase contributions as pipeline, hypothesis, and preliminary experiments until benchmark evidence exists. |
