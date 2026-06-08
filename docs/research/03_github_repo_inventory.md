# GitHub Repo Inventory

This inventory separates repos by intended role. Do not add these as hard dependencies until a later task explicitly scopes integration.

| Repo | URL | Role | Current status in this repo | Priority | Integration risk | Next action |
| --- | --- | --- | --- | --- | --- | --- |
| lucas-maes/le-wm | https://github.com/lucas-maes/le-wm | Model backbone | Declared as `external/le-wm` submodule | High | High: model/checkpoint integration, dependency weight, API uncertainty | Audit files after submodule init; do not implement scoring yet |
| BenedictWilkins/world-of-bugs | https://github.com/BenedictWilkins/world-of-bugs | Dataset / benchmark | Declared as `external/world-of-bugs` submodule | High | Medium: Unity/platform assets may need setup | Verify assets and label formats when submodule is initialized |
| BenedictWilkins/world-of-bugs-experiments | https://github.com/BenedictWilkins/world-of-bugs-experiments | Reference experiments | Declared as `external/world-of-bugs-experiments` submodule | Medium | Medium: may not match this repo's CSV pipeline | Review only; avoid coupling |
| GlitchBench / benchmark project | https://glitchbench.github.io/ | Dataset / benchmark | Not integrated; subset downloader script exists | High | Medium: likely image/LMM-oriented, not temporal by default | Use as visual benchmark and report limitations |
| glitchbench/GlitchBench dataset | https://huggingface.co/datasets/glitchbench/GlitchBench | Dataset / benchmark | Script can query lightweight subset; no data committed | High | Medium: downloads are external and should stay out of git | Keep as optional experiment input |
| facebookresearch/jepa-wms | https://github.com/facebookresearch/jepa-wms | Model backbone / reference only | Not integrated | Medium | High: larger stack and checkpoints | Review methodology for future LeWM/JEPA comparisons |
| facebookresearch/vjepa2 | https://github.com/facebookresearch/vjepa2 | Model backbone / future optional integration | Not integrated | Medium | High: weights/checkpoints and video preprocessing | Consider only after baseline reproducibility is stable |
| facebookresearch/jepa-intuitive-physics | https://github.com/facebookresearch/jepa-intuitive-physics | Reference only | Not integrated | Low | Medium: physics domain mismatch | Use for related work if relevant |
| open-mmlab/mmaction2 | https://github.com/open-mmlab/mmaction2 | Baseline framework | Not integrated | Medium | Medium: large dependency surface | Candidate for TimeSformer/VideoMAE-style baselines |
| facebookresearch/TimeSformer | https://github.com/facebookresearch/TimeSformer | Baseline | Not integrated | Low-Medium | Medium: supervised video model, labels required | Reference for transformer baseline planning |
| MCG-NJU/VideoMAE | https://github.com/MCG-NJU/VideoMAE | Baseline / representation | Not integrated | Medium | Medium: checkpoint and preprocessing complexity | Candidate future baseline |
| OpenGVLab/VideoMAEv2 | https://github.com/OpenGVLab/VideoMAEv2 | Baseline / representation | Not integrated | Medium | Medium-High: larger model family | Candidate future baseline if compute allows |
| stevenliuwen/ano_pred_cvpr2018 | https://github.com/stevenliuwen/ano_pred_cvpr2018 | Video anomaly detection baseline | Not integrated | Low-Medium | Medium: older stack, surveillance domain | Use as conceptual future-frame-prediction reference |
| kimphys/VideoAnomalyDetection.pytorch | https://github.com/kimphys/VideoAnomalyDetection.pytorch | ConvLSTM autoencoder baseline | Not integrated | Low-Medium | Medium: domain mismatch and dependency age | Use for baseline comparison design |
| fdjingliu/NSVAD | https://github.com/fdjingliu/NSVAD | Survey / reference only | Not integrated | Low | Low: reference material only | Mine for baseline taxonomy |
| Gymnasium | https://github.com/Farama-Foundation/Gymnasium | Future data generation support | Not integrated | Low | Medium: needs environment choice | Optional for controlled experiments |
| ALE / Arcade Learning Environment | https://github.com/Farama-Foundation/Arcade-Learning-Environment | Future Atari data source | Not integrated | Low | Medium: gameplay capture and labels required | Optional external validation |
| Procgen | https://github.com/openai/procgen | Future data source | Not integrated | Low | Medium: synthetic game domain and label generation | Optional controlled environment |

## Role separation

- Model backbone: LeWM, JEPA-WMs, V-JEPA 2.
- Dataset / benchmark: World of Bugs, GlitchBench, TempGlitch, VideoGlitchBench.
- Baseline: frame prediction, ConvLSTM autoencoder, TimeSformer, VideoMAE, MMAAction2.
- Reference only: surveys, physics JEPA references, game QA papers.
- Future optional integration: Gymnasium, ALE, Procgen, Godot, Unity.
