# Source Verification Log

Access date: 2026-06-08  
Verifier: Codex

## Summary

- Verified sources: 14
- Paper-only sources: TempGlitch, VideoGlitchBench / GliDe, Future Frame Prediction for Anomaly Detection, Spatiotemporal Autoencoder, ConvLSTM
- Code-available sources: LeWorldModel, GlitchBench, World of Bugs, I-JEPA, V-JEPA, V-JEPA 2, VideoMAE, VideoMAE V2, TimeSformer
- Data-available sources: LeWorldModel task datasets/checkpoints via Hugging Face, GlitchBench on Hugging Face, World of Bugs training/test data via Kaggle, World of Bugs standalone builds via GitHub
- Pending / unverified sources: direct TempGlitch project URL and download path; public VideoGlitchBench code/data release; repo-ready public label exports for TempGlitch and World of Bugs
- Claims downgraded:
  - TempGlitch is not yet safe to describe as "download-ready" in this repo.
  - VideoGlitchBench is not yet safe to describe as an immediately runnable fallback.
  - LeWM is not yet safe to describe as integrated into this repo.
  - GlitchBench is not safe evidence for temporal localization claims.

## Full-paper readiness implications

- Strongest sources for the Introduction:
  - LeWM for latent prediction and surprise evaluation.
  - TempGlitch for the temporal-vs-spatial glitch distinction.
  - GlitchBench and World of Bugs for public game-QA context.
- Strongest sources for Related Work:
  - TempGlitch, VideoGlitchBench / GliDe, GlitchBench, World of Bugs.
  - I-JEPA, V-JEPA, V-JEPA 2, VideoMAE, TimeSformer, future-frame prediction, and spatiotemporal autoencoder baselines.
- Primary benchmark recommendation:
  - TempGlitch is the best thematic match, but only after Phase 2 verifies direct public access, license, and annotation format.
- Fallback benchmark recommendation:
  - GlitchBench is the safest currently visible public artifact, but only for static-image evidence.
  - World of Bugs is the best controlled game-environment fallback if setup and label conversion are later verified.
- Baselines justified by verified sources:
  - Prediction-error baselines: future-frame prediction.
  - Classical temporal anomaly baselines: spatiotemporal autoencoder family.
  - Future representation backbones: VideoMAE, TimeSformer, JEPA-family variants.
- Claims that must remain tentative:
  - Any claim that a public temporal benchmark is already runnable in this repo.
  - Any claim that LeWM is already implemented here.
  - Any superiority claim for latent surprise over simpler visual baselines before benchmark results exist.

## Source table

| ID | Source | URL | Type | Status | Verified facts | Relevance | Risk / notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S-001 | EAI FISAT 2026 official page | https://daihoc.fpt.edu.vn/hcm/fisat/ | conference page | official page verified | dates, page limits, language, format, review model, alt-text requirement, tracks, submission system | Venue targeting and paper planning | Official page is live and current |
| S-002 | LeWorldModel | https://arxiv.org/abs/2603.19312 ; https://github.com/lucas-maes/le-wm | paper + code + data links | paper-verified; code-available; data-available | end-to-end JEPA from pixels, code repo, HF checkpoints/data, surprise evaluation | Future `lewm_latent` target | Not a gameplay-glitch benchmark |
| S-003 | TempGlitch | https://arxiv.org/abs/2605.21443 | paper | paper-verified; paper-only; pending-web-verification | 5 temporal glitch types, 1,500 total videos, paired clean clips, binary metrics | Best thematic benchmark target | Project website URL not recovered from primary sources |
| S-004 | VideoGlitchBench / GliDe | https://arxiv.org/abs/2604.07818 | paper | paper-verified; paper-only; pending-web-verification | 5,238 videos, 120 games, descriptions plus temporal spans, joint semantic + temporal protocol | Rich full-paper benchmark candidate | Public code/data release not verified |
| S-005 | GlitchBench | https://arxiv.org/abs/2312.05291 ; https://glitchbench.github.io/ ; https://huggingface.co/datasets/glitchbench/GlitchBench | paper + project page + dataset page | paper-verified; data-available; dataset-format-verified | image-level benchmark, paper size 593 images / 205 games, current HF viewer 607 rows, MIT license | Static-image benchmark and metadata source | Paper/HF row-count mismatch; not temporal |
| S-006 | World of Bugs | https://arxiv.org/abs/2206.11037 ; https://benedictwilkins.github.io/world-of-bugs/ ; https://github.com/BenedictWilkins/world-of-bugs | paper + project page + code | paper-verified; code-available; data-available | open ABD platform, docs, PyPI, standalone builds, Kaggle train/test data | Controlled benchmark or case study candidate | Label schema still not mapped to this repo |
| S-007 | I-JEPA | https://arxiv.org/abs/2301.08243 ; https://github.com/facebookresearch/ijepa | paper + code | paper-verified; code-available | image JEPA predicts latent targets without pixel reconstruction | Background for latent prediction | Image-only source |
| S-008 | V-JEPA | https://github.com/facebookresearch/jepa | code + cited paper | paper-verified; code-available | self-supervised latent video prediction without pixel reconstruction | Video-side JEPA background | Not a gameplay benchmark |
| S-009 | V-JEPA 2 / V-JEPA 2.1 | https://arxiv.org/abs/2506.09985 ; https://arxiv.org/abs/2603.14482 ; https://github.com/facebookresearch/vjepa2 | paper + code | paper-verified; code-available | understanding, prediction, planning, dense video features, model weights required | Strong modern JEPA context | Heavy checkpoints / compute |
| S-010 | VideoMAE / VideoMAE V2 | https://arxiv.org/abs/2203.12602 ; https://arxiv.org/abs/2303.16727 ; https://github.com/MCG-NJU/VideoMAE ; https://github.com/OpenGVLab/VideoMAEv2 | paper + code | paper-verified; code-available | reconstruction-based self-supervised video pretraining families with official repos | Future backbone / baseline context | Objective mismatch vs latent surprise |
| S-011 | TimeSformer | https://github.com/facebookresearch/TimeSformer | paper + code | paper-verified; code-available | supervised video transformer baseline; repo archived on 2025-01-01 | Future supervised baseline | Archived repo; not an anomaly detector |
| S-012 | Future Frame Prediction for Anomaly Detection | https://arxiv.org/abs/1712.09867 | paper | paper-verified; paper-only | future-frame prediction used directly for anomaly scoring | Canonical prediction-error baseline | Surveillance-domain mismatch |
| S-013 | Spatiotemporal Autoencoder | https://arxiv.org/abs/1701.01546 | paper | paper-verified; paper-only | spatial + temporal anomaly model for videos | Classical autoencoder baseline family | Surveillance-domain mismatch |
| S-014 | ConvLSTM | https://arxiv.org/abs/1506.04214 | paper | paper-verified; paper-only | canonical spatiotemporal recurrent modeling block | Method background if future baselines use ConvLSTM blocks | Not itself a glitch/anomaly paper |

## Detailed notes

### S-001 - FISAT 2026

source_id: S-001  
title: EAI FISAT 2026 official conference page  
authors: TBD / verify  
year: 2026  
venue/status: Official conference page  
URL: https://daihoc.fpt.edu.vn/hcm/fisat/  
access_date: 2026-06-08  
artifact_type: conference page  
availability_status:
- paper-verified

key_verified_facts:
- Conference name: EAI FISAT 2026, the European Alliance for Innovation - FPT International Conference on Intelligent Systems and Advanced Technologies.
- Conference dates: November 25-27, 2026, in Ho Chi Minh City, Vietnam.
- Paper submission deadline: July 20, 2026.
- Acceptance notification: September 15, 2026.
- Camera-ready deadline: October 15, 2026.
- Full / regular papers: 12-20 pages, excluding appendices, references, and acknowledgements.
- Short papers: 6-11 pages, excluding appendices, references, and acknowledgements.
- Required language: English.
- Format: Springer Authors' Kit / LNCS-style proceedings templates via the conference page.
- Submission system: Confy+.
- Review model: Single-blind review.
- Accessibility: figures, illustrations, tables, and images should include descriptive text / alt text.
- Relevant tracks: Track 1 AI & Data Science, especially Machine Learning and Foundation Models, Computer Vision, and Reinforcement Learning and Optimization.
- Publication / indexing: EAI / Springer Innovations in Communication and Computing, indexed in Scopus (Q4 / Scimago on the official page).

relevance_to_project:
- Sets the paper-length target and review constraints.
- Confirms the project fits the AI & Data Science track.

how_used_in_full_paper:
- Venue planning.
- Paper-scope decision between short and full / regular submission.

limitations_or_risks:
- The official page does not yet expose presenter guidelines or registration fees.

claims_supported:
- FISAT 2026 is a realistic venue target.
- The full-paper page budget is compatible with a larger experimental package.

claims_not_supported:
- Any claim about registration fees or final presentation logistics.

### S-002 - LeWorldModel

source_id: S-002  
title: LeWorldModel: Stable End-to-End Joint-Embedding Predictive Architecture from Pixels  
authors: Lucas Maes; Quentin Le Lidec; Damien Scieur; Yann LeCun; Randall Balestriero  
year: 2026  
venue/status: arXiv preprint v3; official code repo available  
URL: https://arxiv.org/abs/2603.19312 ; https://github.com/lucas-maes/le-wm  
access_date: 2026-06-08  
artifact_type: paper / code / data links  
availability_status:
- paper-verified
- code-available
- data-available

key_verified_facts:
- LeWM is presented as the first JEPA that trains stably end-to-end from raw pixels using only a prediction loss plus Gaussian latent regularization.
- The paper reports a compact model of about 15M parameters.
- The paper explicitly reports surprise evaluation for physically implausible events.
- The official GitHub repo is public.
- The official repo links to Hugging Face datasets and pretrained checkpoints.
- The official repo documents how checkpoints are loaded and converted for evaluation.

relevance_to_project:
- Direct long-term target for `lewm_latent`.
- Strongest source for the latent-surprise framing already adopted in the repo docs.

how_used_in_full_paper:
- Introduction and method framing.
- Future-work justification for replacing `mini_latent`.

limitations_or_risks:
- Official experiments are control / robotics oriented, not gameplay-glitch oriented.
- The pipeline assumes action-conditioned trajectories and checkpoint-specific setup that this repo does not yet implement.

claims_supported:
- LeWM code and checkpoints exist.
- LeWM makes latent surprise a defensible research direction.

claims_not_supported:
- LeWM is already integrated into this repo.
- LeWM is already validated for gameplay glitch detection.

### S-003 - TempGlitch

source_id: S-003  
title: TempGlitch: Evaluating Vision-Language Models for Temporal Glitch Detection in Gameplay Videos  
authors: Yakun Yu; Ashley Wiens; Adrian Barahona-Rios; Benedict Wilkins; Saman Zadtootaghaj; Nabajeet Barman; Cor-Paul Bezemer  
year: 2026  
venue/status: arXiv preprint v1  
URL: https://arxiv.org/abs/2605.21443  
access_date: 2026-06-08  
artifact_type: paper  
availability_status:
- paper-verified
- paper-only
- pending-web-verification

key_verified_facts:
- The paper explicitly separates spatial glitches from temporal glitches.
- TempGlitch contains five temporal glitch categories: blinking, shooting glitch, velocity glitch, frozen animation, and stuck in place.
- The paper describes 750 glitchy videos and 750 glitch-free videos, with 150 glitchy videos per category and matched clean clips.
- The dataset is built with the open-source Godot engine and two base environments, plus a character variation.
- Each glitchy clip contains both normal and anomalous temporal segments inside the same video.
- Evaluation is binary classification at the video level with accuracy, F1, precision, and recall.
- The paper says code and data are available at the project website.

relevance_to_project:
- Best thematic match for a temporal gameplay glitch benchmark.
- Strongest paper-level support for treating temporal glitches as distinct from static visual anomalies.

how_used_in_full_paper:
- Benchmark selection rationale.
- Related work and limitations discussion.

limitations_or_risks:
- The public project website URL was not recoverable from primary sources during this Phase 1 pass.
- Public annotation-file format, license, and download procedure remain `TBD / verify`.
- The official evaluation setup is video-level binary classification, not a ready-made CSV export for this repo.

claims_supported:
- TempGlitch is a real temporal gameplay glitch benchmark on paper.
- TempGlitch is the strongest benchmark target for Phase 2.

claims_not_supported:
- TempGlitch is already downloadable in this repo.
- TempGlitch labels are already verified to map directly into `source,start_frame,end_frame,label`.

### S-004 - VideoGlitchBench / GliDe

source_id: S-004  
title: Open-Ended Video Game Glitch Detection with Agentic Reasoning and Temporal Grounding  
authors: Muyang Zheng; Tong Zhou; Geyang Wu; Zihao Lin; Haibo Wang; Lifu Huang  
year: 2026  
venue/status: arXiv preprint v2; under review per paper comments  
URL: https://arxiv.org/abs/2604.07818  
access_date: 2026-06-08  
artifact_type: paper  
availability_status:
- paper-verified
- paper-only
- pending-web-verification

key_verified_facts:
- The paper introduces VideoGlitchBench as an open-ended gameplay glitch detection benchmark with temporal localization.
- The paper reports 5,238 gameplay videos from 120 games.
- Samples include detailed glitch descriptions and precise temporal spans.
- The benchmark is constructed from GamePhysics videos with a semi-automated pipeline plus human review and manual temporal annotation.
- The paper proposes GliDe, an agentic framework with contextual memory, debate / reflection, and event grounding.
- The paper states that the evaluation jointly measures semantic fidelity and temporal accuracy.

relevance_to_project:
- Strongest full-paper-scale temporal benchmark on paper.
- Valuable fallback if TempGlitch access remains blocked.

how_used_in_full_paper:
- Related work.
- Stretch benchmark for a later full / regular submission.

limitations_or_risks:
- No primary-source public code or dataset release URL was verified on 2026-06-08.
- The task is richer than this repo's current binary interval pipeline and may need an adapter layer.

claims_supported:
- VideoGlitchBench is a temporally grounded gameplay benchmark on paper.
- It is a serious future comparison target.

claims_not_supported:
- VideoGlitchBench is already runnable from public artifacts.
- Its evaluation protocol already maps cleanly into this repo's current metric files.

### S-005 - GlitchBench

source_id: S-005  
title: GlitchBench: Can Large Multimodal Models Detect Video Game Glitches?  
authors: Mohammad Reza Taesiri; Tianjun Feng; Anh Nguyen; Cor-Paul Bezemer  
year: 2024  
venue/status: arXiv preprint v2; CVPR 2024 noted in paper comments  
URL: https://arxiv.org/abs/2312.05291 ; https://glitchbench.github.io/ ; https://huggingface.co/datasets/glitchbench/GlitchBench  
access_date: 2026-06-08  
artifact_type: paper / project page / dataset page  
availability_status:
- paper-verified
- data-available
- dataset-format-verified

key_verified_facts:
- The paper frames GlitchBench as a single-frame benchmark for LMM glitch detection.
- The paper reports 593 images from 205 games.
- Each paper sample has a video clip, representative frame, short description, and Reddit-thread reference.
- The project page advertises code and data.
- The current Hugging Face dataset page is public, licensed MIT, and exposes a validation split with 607 rows.
- The Hugging Face viewer shows image-level fields including `image`, `id`, `reddit`, `glitch-type`, `game`, `source`, and `description`.

relevance_to_project:
- Safest currently visible public benchmark artifact in this topic area.
- Useful for image-level auxiliary evidence and metadata structure.

how_used_in_full_paper:
- Related work.
- Static-image auxiliary benchmark or qualitative section.

limitations_or_risks:
- The benchmark is image-level, not a temporal video benchmark.
- The paper count (593) and current HF viewer count (607) differ; the reason was not verified.

claims_supported:
- GlitchBench is useful public evidence for game-glitch recognition.
- GlitchBench should be treated as static-image evidence.

claims_not_supported:
- GlitchBench can support temporal localization claims.
- The current HF row-count difference has been explained.

### S-006 - World of Bugs

source_id: S-006  
title: World of Bugs: A Platform for Automated Bug Detection in 3D Video Games  
authors: Benedict Wilkins; Kostas Stathis  
year: 2022  
venue/status: arXiv preprint; accepted at COG2022 per arXiv comments  
URL: https://arxiv.org/abs/2206.11037 ; https://benedictwilkins.github.io/world-of-bugs/ ; https://github.com/BenedictWilkins/world-of-bugs  
access_date: 2026-06-08  
artifact_type: paper / project page / code / docs  
availability_status:
- paper-verified
- code-available
- data-available

key_verified_facts:
- The paper defines World of Bugs as an open platform for Automated Bug Detection research in video games.
- The paper highlights a growing collection of common video game bugs for training and evaluation.
- The official docs expose PyPI installation, source installation, standalone builds, and Unity-editor setup.
- The official GitHub repo is public and links to Kaggle training and test data.
- The official quick-start recommends Unity 2020.3.29f1 for editor-based workflows.

relevance_to_project:
- Best verified controlled-environment alternative to purely static benchmarks.
- Bridges game QA and anomaly-style learning more directly than surveillance datasets.

how_used_in_full_paper:
- Related work and possible controlled-case-study benchmark.
- Risk discussion around public benchmark availability.

limitations_or_risks:
- Public label schema was not yet inspected against this repo's CSV interfaces.
- Setup cost is substantially higher than the current MVP pipeline.

claims_supported:
- World of Bugs is a platform / environment, not just a paper idea.
- Data and builds exist outside this repo.

claims_not_supported:
- World of Bugs is already converted into this repo's manifest / labels format.
- WOB benchmark results can already be reported from this repo.

### S-007 - I-JEPA

source_id: S-007  
title: Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture  
authors: Mahmoud Assran; Quentin Duval; Ishan Misra; Piotr Bojanowski; Pascal Vincent; Michael Rabbat; Yann LeCun; Nicolas Ballas  
year: 2023  
venue/status: arXiv preprint; official code repo archived on 2024-08-01  
URL: https://arxiv.org/abs/2301.08243 ; https://github.com/facebookresearch/ijepa  
access_date: 2026-06-08  
artifact_type: paper / code  
availability_status:
- paper-verified
- code-available

key_verified_facts:
- I-JEPA predicts latent representations of masked image regions from context.
- The official repo explicitly contrasts it with pixel-filling objectives.
- The official code repo is public and archived.

relevance_to_project:
- Background support for latent prediction over reconstruction.

how_used_in_full_paper:
- Method background in the JEPA family section.

limitations_or_risks:
- Image-only source.

claims_supported:
- Latent prediction can be framed without pixel reconstruction.

claims_not_supported:
- I-JEPA itself solves gameplay glitch detection.

### S-008 - V-JEPA

source_id: S-008  
title: V-JEPA: Video Joint-Embedding Predictive Architecture  
authors: Adrien Bardes; Quentin Garrido; Jean Ponce; Xinlei Chen; Michael Rabbat; Yann LeCun; Mahmoud Assran; Nicolas Ballas  
year: 2024  
venue/status: official code repo with cited paper `Revisiting Feature Prediction for Learning Visual Representations from Video`  
URL: https://github.com/facebookresearch/jepa  
access_date: 2026-06-08  
artifact_type: code / cited paper  
availability_status:
- paper-verified
- code-available

key_verified_facts:
- The official repo describes V-JEPA as self-supervised learning of video representations from latent feature prediction.
- The official repo states it does not rely on pretrained image encoders, text, negative examples, human annotations, or pixel-level reconstruction.
- The repo provides pretrained checkpoints and evaluation code.

relevance_to_project:
- Strongest official source for video JEPA background before V-JEPA 2.

how_used_in_full_paper:
- Related work on latent predictive video learning.

limitations_or_risks:
- Representation-learning source, not a gameplay-glitch benchmark.

claims_supported:
- Video JEPA methods can learn from latent prediction instead of pixel reconstruction.

claims_not_supported:
- V-JEPA already validates gameplay anomaly detection.

### S-009 - V-JEPA 2 / V-JEPA 2.1

source_id: S-009  
title: V-JEPA 2 and V-JEPA 2.1 official papers and code  
authors: Mahmoud Assran and collaborators; Lorenzo Mur-Labadia and collaborators  
year: 2025-2026  
venue/status: arXiv preprints plus official Meta FAIR repo  
URL: https://arxiv.org/abs/2506.09985 ; https://arxiv.org/abs/2603.14482 ; https://github.com/facebookresearch/vjepa2  
access_date: 2026-06-08  
artifact_type: paper / code  
availability_status:
- paper-verified
- code-available

key_verified_facts:
- V-JEPA 2 is described as enabling understanding, prediction, and planning.
- The official repo includes V-JEPA 2, V-JEPA 2-AC, and V-JEPA 2.1.
- V-JEPA 2-AC is described as a latent action-conditioned world model for robot manipulation after post-training.
- V-JEPA 2.1 emphasizes dense predictive loss, deep self-supervision, and temporally consistent dense features.

relevance_to_project:
- Stronger modern world-model context than classic reconstruction baselines.
- Helps justify future latent backbones without claiming direct glitch performance.

how_used_in_full_paper:
- Background and future-work section.

limitations_or_risks:
- Requires significant checkpoints / compute.
- Still not direct benchmark evidence for gameplay glitches.

claims_supported:
- JEPA-family video models now explicitly cover prediction and planning.

claims_not_supported:
- V-JEPA 2 already proves gameplay glitch localization performance.

### S-010 - VideoMAE / VideoMAE V2

source_id: S-010  
title: VideoMAE family official papers and repos  
authors: VideoMAE: Zhan Tong; Yibing Song; Jue Wang; Limin Wang. VideoMAE V2: Limin Wang and collaborators  
year: 2022-2023  
venue/status: arXiv preprints  
URL: https://arxiv.org/abs/2203.12602 ; https://arxiv.org/abs/2303.16727 ; https://github.com/MCG-NJU/VideoMAE ; https://github.com/OpenGVLab/VideoMAEv2  
access_date: 2026-06-08  
artifact_type: paper / code  
availability_status:
- paper-verified
- code-available

key_verified_facts:
- VideoMAE uses masked video autoencoding with high-ratio tube masking.
- VideoMAE V2 scales the approach with dual masking.
- Both are positioned as self-supervised video pretraining methods for downstream transfer.
- Both papers point to official code repositories.

relevance_to_project:
- Reasonable future backbone or baseline family if the project wants a mainstream video SSL comparison.

how_used_in_full_paper:
- Related work and future baseline discussion.

limitations_or_risks:
- Reconstruction-based objectives do not directly match the repo's latent-surprise hypothesis.

claims_supported:
- VideoMAE is a strong video SSL family worth citing.

claims_not_supported:
- VideoMAE already supports anomaly scoring by latent prediction error.

### S-011 - TimeSformer

source_id: S-011  
title: Is Space-Time Attention All You Need for Video Understanding? / official TimeSformer repo  
authors: Gedas Bertasius; Heng Wang; Lorenzo Torresani  
year: 2021  
venue/status: ICML 2021 paper; official repo archived on 2025-01-01  
URL: https://github.com/facebookresearch/TimeSformer  
access_date: 2026-06-08  
artifact_type: paper / code  
availability_status:
- paper-verified
- code-available

key_verified_facts:
- Official repo positions TimeSformer as a supervised video classification framework.
- The repo provides pretrained models for Kinetics, Something-Something, and HowTo100M variants.
- The repo is archived and read-only as of 2025-01-01.

relevance_to_project:
- Candidate future supervised baseline if benchmark splits support supervised training.

how_used_in_full_paper:
- Related work and baseline planning.

limitations_or_risks:
- Archived maintenance state.
- Not an anomaly detector by default.

claims_supported:
- TimeSformer is a legitimate supervised video baseline family.

claims_not_supported:
- TimeSformer is already aligned with one-class anomaly scoring.

### S-012 - Future Frame Prediction for Anomaly Detection

source_id: S-012  
title: Future Frame Prediction for Anomaly Detection -- A New Baseline  
authors: Wen Liu; Weixin Luo; Dongze Lian; Shenghua Gao  
year: 2017  
venue/status: arXiv preprint  
URL: https://arxiv.org/abs/1712.09867  
access_date: 2026-06-08  
artifact_type: paper  
availability_status:
- paper-verified
- paper-only

key_verified_facts:
- The paper explicitly proposes anomaly detection through future-frame prediction error rather than reconstruction error.
- The abstract highlights both spatial and temporal constraints in the prediction objective.

relevance_to_project:
- Canonical prediction-error baseline family to cite against latent prediction.

how_used_in_full_paper:
- Baseline motivation in related work.

limitations_or_risks:
- Surveillance anomaly source, not gameplay-specific.

claims_supported:
- Prediction error is a canonical anomaly-detection framing.

claims_not_supported:
- This source directly validates gameplay glitch detection.

### S-013 - Spatiotemporal Autoencoder

source_id: S-013  
title: Abnormal Event Detection in Videos using Spatiotemporal Autoencoder  
authors: Yong Shean Chong; Yong Haur Tay  
year: 2017  
venue/status: arXiv preprint  
URL: https://arxiv.org/abs/1701.01546  
access_date: 2026-06-08  
artifact_type: paper  
availability_status:
- paper-verified
- paper-only

key_verified_facts:
- The paper presents a spatial representation module plus a temporal evolution module for video anomaly detection.
- The abstract reports evaluation on Avenue, Subway, and UCSD.

relevance_to_project:
- Classical autoencoder-style temporal anomaly baseline family.

how_used_in_full_paper:
- Related work for non-JEPA anomaly baselines.

limitations_or_risks:
- Surveillance domain mismatch.

claims_supported:
- Spatiotemporal autoencoders are canonical anomaly baselines.

claims_not_supported:
- This source directly supports gameplay-specific conclusions.

### S-014 - ConvLSTM

source_id: S-014  
title: Convolutional LSTM Network: A Machine Learning Approach for Precipitation Nowcasting  
authors: Xingjian Shi; Zhourong Chen; Hao Wang; Dit-Yan Yeung; Wai-kin Wong; Wang-chun Woo  
year: 2015  
venue/status: arXiv preprint  
URL: https://arxiv.org/abs/1506.04214  
access_date: 2026-06-08  
artifact_type: paper  
availability_status:
- paper-verified
- paper-only

key_verified_facts:
- ConvLSTM extends FC-LSTM with convolutional transitions for spatiotemporal sequences.
- The paper is a sequence-forecasting method source, not an anomaly paper.

relevance_to_project:
- Canonical temporal-modeling citation if future baselines reuse ConvLSTM blocks.

how_used_in_full_paper:
- Method background only.

limitations_or_risks:
- No direct gameplay or anomaly evidence.

claims_supported:
- ConvLSTM is a legitimate spatiotemporal modeling component.

claims_not_supported:
- ConvLSTM alone justifies gameplay glitch detection claims.
