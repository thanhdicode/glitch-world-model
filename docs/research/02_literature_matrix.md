# Literature Matrix

This matrix is a starting point. Entries marked `TBD / verify` need paper-level verification before citation or numerical claims.

| Work / Paper | Year | Problem | Method | Dataset / Benchmark | Metrics | Relevance to this repo | Limitation / risk |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| LeWorldModel / LeWM | 2026 | Stable JEPA-style latent world modeling from pixels | Next-embedding prediction plus latent regularization | Control and physical plausibility settings reported by authors | Prediction / planning / surprise metrics, TBD / verify | Direct future target for `lewm_latent`; supports latent surprise hypothesis | New work; integration and checkpoint details must be verified |
| World of Bugs | 2022 | Automated bug detection in 3D video games | Unity-based platform with implemented bug types and labels | World of Bugs environments | Bug identification metrics, TBD / verify | Relevant game QA benchmark/source of bug categories and possible assets | Submodules may be uninitialized; environment setup may be heavier than current MVP |
| GlitchBench | 2024 | Can large multimodal models detect game glitches? | Image/LMM benchmark from glitched game scenarios | GlitchBench dataset | LMM task metrics, TBD / verify | Useful public evidence for visual glitch recognition and image baselines | Primarily static/image-oriented; weak for temporal-dynamics claims |
| VideoGlitch / GlitchAgent | 2026 | Open-ended gameplay glitch detection with temporal grounding | Agentic multimodal reasoning, description, temporal localization | VideoGlitchBench | Semantic and temporal grounding metrics, TBD / verify | Strongly aligned with temporal localization and natural-language glitch reports | VLM/agent pipeline differs from lightweight latent world model approach |
| VideoGlitchBench / GliDe | 2026 | Video game glitch detection with temporal spans | Game-aware memory, debate/reflector, event grounding | VideoGlitchBench | Temporal localization and semantic fidelity, TBD / verify | Important future comparison point for temporal video benchmarks | May require large VLMs and benchmark access; not suitable for current lightweight MVP |
| TempGlitch | 2026 | Temporal glitch detection in gameplay videos | Controlled video benchmark for temporal glitch categories | TempGlitch | Binary / category metrics, TBD / verify | Excellent fit for the claim that temporal glitches differ from spatial glitches | Availability and exact protocol must be verified before use |
| Future frame prediction for anomaly detection | 2018 | General video anomaly detection | Predict future frames and score prediction error | Avenue / UCSD / ShanghaiTech style datasets | AUC / EER, TBD / verify | Conceptual ancestor of prediction-error anomaly scoring | Pixel prediction can overemphasize visual detail rather than game dynamics |
| Spatiotemporal / ConvLSTM autoencoder baselines | 2017+ | General video anomaly detection | Reconstruct or predict normal video dynamics | Surveillance anomaly datasets | AUC / frame-level metrics, TBD / verify | Candidate baseline family for `07_baseline_plan.md` | Domain mismatch with gameplay; compute and data requirements |
| JEPA / V-JEPA / V-JEPA 2 | 2024-2026 | Self-supervised visual/video representation and prediction | Predict latent features instead of pixels | Large-scale video/image data and downstream tasks | Linear probe / action / prediction metrics, TBD / verify | Supports using latent prediction instead of pixel reconstruction | Foundation models may require checkpoints and adaptation strategy |
| TimeSformer | 2021 | Video understanding | Space-time transformer attention | Action recognition datasets | Top-1 / Top-5 accuracy, TBD / verify | Useful supervised video-classification baseline if labels are available | Not an anomaly model by default; needs labeled glitch training data |
| VideoMAE / VideoMAE V2 | 2022-2023 | Self-supervised video pretraining | Masked video autoencoding | Video pretraining and action benchmarks | Classification / transfer metrics, TBD / verify | Candidate representation backbone or baseline | Reconstruction/pretraining objective differs from world-model surprise |

## Seed sources to verify

- LeWM GitHub: https://github.com/lucas-maes/le-wm
- LeWM arXiv: https://arxiv.org/abs/2603.19312
- World of Bugs arXiv: https://arxiv.org/abs/2206.11037
- World of Bugs project: https://benedictwilkins.github.io/world-of-bugs/
- GlitchBench paper: https://arxiv.org/abs/2312.05291
- GlitchBench dataset: https://huggingface.co/datasets/glitchbench/GlitchBench
- VideoGlitchBench / GliDe arXiv: https://arxiv.org/abs/2604.07818
- TempGlitch arXiv: https://arxiv.org/abs/2605.21443
- V-JEPA 2 GitHub: https://github.com/facebookresearch/vjepa2
- JEPA world models GitHub: https://github.com/facebookresearch/jepa-wms
- TimeSformer GitHub: https://github.com/facebookresearch/TimeSformer
- VideoMAE arXiv: https://arxiv.org/abs/2203.12602
