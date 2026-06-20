# Paper Source Matrix

Date: 2026-06-18

Status: active paper-writing control document

## Purpose

This matrix records which repository and literature sources are allowed to support each manuscript
surface. A source may motivate context without supporting this repository's empirical claims.

## Manuscript Surface Matrix

| Section or appendix | Primary sources | Notes |
| --- | --- | --- |
| Introduction | `docs/research/16_claim_registry.md`, `docs/research/69_r5_tempglitch_identical_episode_results.md`, `paper/references.bib` | Keep motivation bounded; do not claim final performance. |
| Related Work | `paper/references.bib` | Literature supports context categories only; none support this repository's R5 metrics. |
| Problem Formulation | `docs/research/69_r5_tempglitch_identical_episode_results.md`, `PLAYBOOK.md` | Episode-level framing only. |
| Method Summary | `paper/references.bib`, `PLAYBOOK.md` | No architecture novelty or method-superiority claim. |
| Evaluation Protocol | `docs/research/69_r5_tempglitch_identical_episode_results.md`, `docs/research/16_claim_registry.md` | Protect split hygiene and threshold wording. |
| Datasets and Data Scope | `PLAYBOOK.md`, `docs/research/69_r5_tempglitch_identical_episode_results.md` | WOB stays status-only. |
| Bounded Experiments | `docs/research/69_r5_tempglitch_identical_episode_results.md` | R5 family only; ablations remain TODO. |
| Bounded Results | `docs/research/69_r5_tempglitch_identical_episode_results.md` | Use exact qualified wording. |
| Limitations | `docs/research/16_claim_registry.md`, `PLAYBOOK.md`, `docs/research/69_r5_tempglitch_identical_episode_results.md` | Keep negatives visible. |
| Conclusion | claim map, source matrix, R5 results note | Keep TODO and avoid final abstract-style success claims. |
| Claim Registry appendix | `docs/research/16_claim_registry.md`, `docs/research/69_r5_tempglitch_identical_episode_results.md`, `PLAYBOOK.md` | Mirrors allowed, pending, and forbidden surfaces. |
| Artifact Provenance appendix | `docs/research/69_r5_tempglitch_identical_episode_results.md` | Hash-addressable evidence only. |
| Dataset Split Protocol appendix | `docs/research/69_r5_tempglitch_identical_episode_results.md`, `PLAYBOOK.md` | Preserve the fit/select boundary. |
| Reproducibility Checklist appendix | `docs/research/69_r5_tempglitch_identical_episode_results.md`, `docs/research/16_claim_registry.md`, `pineau2021reproducibility` | Focus on auditability. |
| Forbidden Claims appendix | `docs/research/16_claim_registry.md`, `PLAYBOOK.md` | Keep explicit. |
| Submission Checklist appendix | `paper/main.tex`, `paper/references.bib`, this source matrix | For manual release review. |

## Bibliography Claim Support Matrix

| Source | Group | Supports | Does not support | Allowed claim | Forbidden overclaim | Target section |
| --- | --- | --- | --- | --- | --- | --- |
| `ijepa` | JEPA / I-JEPA | Background on joint-embedding predictive architectures for images. | Any result by this repository or any V-JEPA/LeWM performance claim. | JEPA is relevant representation-learning context. | This paper improves I-JEPA. | Related Work, Method |
| `vjepa` | JEPA / V-JEPA | Background on video feature prediction and self-supervised video representation learning. | Gameplay-glitch metrics or TempGlitch performance. | V-JEPA motivates video prediction context. | This paper beats V-JEPA. | Related Work, Method |
| `worldmodels` | latent world models | Historical context for compact learned world models. | Gameplay glitch detection, R5, or evaluation claims. | Latent world models are relevant background. | This paper demonstrates planning/control. | Related Work, Method |
| `planet` | latent world models | Learned latent dynamics from pixels. | Current repository training/evaluation performance. | Latent dynamics are a relevant modeling lineage. | This paper matches PlaNet-style control claims. | Related Work, Method |
| `dreamerv3` | latent world models | Modern world-model context across domains. | Generalization claims for this project. | World models have been studied across domains. | This paper masters diverse domains. | Related Work, Method |
| `lewm` | latent world models / LeWM | External LeWM architecture and checkpoint-context reference. | Any repository-specific R5 metric without local artifact evidence. | LeWM is the latent-surprise family used for artifact-backed scoring. | The local pipeline proves LeWM is broadly superior. | Related Work, Method |
| `sultani2018ucfcrime` | video anomaly detection | Weakly supervised real-world video anomaly-detection background. | Direct comparability to gameplay glitches. | Video anomaly detection is a related but distinct field. | This paper beats surveillance anomaly detectors. | Related Work |
| `park2020mnad` | video anomaly detection | Normality-modeling background for video anomaly detection. | TempGlitch or R5 metric support. | Normality modeling is a related evaluation context. | This paper improves memory-guided anomaly detection. | Related Work |
| `glitchbench` | game glitch detection | Gameplay glitch benchmark motivation. | Local R5 metric or leaderboard claims. | Game glitches are a documented multimodal benchmark problem. | This paper wins GlitchBench. | Introduction, Related Work |
| `tempglitch` | game glitch detection | Temporal gameplay-glitch benchmark framing. | Locked-test or broad TempGlitch leaderboard claims. | TempGlitch motivates temporal glitch evaluation. | This paper solves TempGlitch broadly. | Introduction, Related Work |
| `politowski2022automatedtesting` | automated game testing | Automated game testing remains difficult and oracle/workflow-sensitive. | Production QA readiness. | Automated game testing is a challenging applied context. | This paper replaces human QA. | Related Work, Limitations |
| `hendrycks2017baseline` | OOD detection | Score-based OOD/error-detection background. | LeWM surprise as calibrated probability. | OOD detection motivates scalar-score caution. | This paper is an OOD benchmark winner. | Related Work |
| `guo2017calibration` | calibration | Calibration caution and distinction between raw scores and calibrated confidence. | Any claim that R5 thresholds are neural probability calibration. | The paper should distinguish threshold choice from probability calibration. | The current detector is calibrated for deployment. | Protocol, Limitations |
| `kaufman2011leakage` | leakage-aware evaluation | General leakage formulation and avoidance motivation. | Proof that every future experiment is leakage-free. | Leakage avoidance motivates split discipline. | This repo has eliminated all leakage risk. | Introduction, Protocol |
| `kapoor2023leakage` | leakage-aware evaluation | ML leakage/reproducibility risk framing. | Any empirical result. | Leakage risk justifies conservative claim boundaries. | External paper validates local metrics. | Introduction, Protocol, Limitations |
| `pineau2021reproducibility` | reproducibility / artifact provenance | Checklist-style reproducibility motivation. | Full third-party reproducibility of private artifacts. | Reproducibility reporting is central to the paper scaffold. | The paper is fully reproducible without data/checkpoints. | Related Work, Appendix D |

## Current Constraint

Do not support R5 prose from memory, terminal output alone, or unattested draft notes. R5 claims
must resolve to `docs/research/69_r5_tempglitch_identical_episode_results.md` or a later verified
artifact document.
