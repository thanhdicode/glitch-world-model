# Dataset and Benchmark Map

Public benchmarks should remain the main source of paper-facing evidence. Synthetic or repo-local data can validate mechanics, not novelty or generalization.

| Dataset / Benchmark | Source ID | Data modality | Label type | Temporal labels? | Access status | Planned use | Risk | Verification notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TempGlitch | [S-003](17_source_verification_log.md) | Gameplay videos | Public HF artifact exposes binary per-video labels plus category folders; local conversion maps buggy videos to full-video positive intervals | Temporal behavior is the task focus, but the public artifact currently exposes binary per-video labels only | verified-online=yes; public-download=yes; license=MIT; downloaded-locally=yes; converted-locally=yes; evaluated-locally=yes (two-video smoke test and leakage-aware 30-video split slice) | Primary public benchmark path; next scale the slice and add per-category / failure analysis | Public artifact has one `train` split, an empty README, and no verified finer temporal-span annotations; current 30-video split is repo-defined and preliminary | On 2026-06-08 this repo evaluated all five categories with `3` buggy and `3` normal videos per category, split by source into `10/10/10` train/validation/test videos. See [21_phase3_phase4_baseline_results.md](21_phase3_phase4_baseline_results.md). |
| VideoGlitchBench | [S-004](17_source_verification_log.md) | Gameplay videos | Natural-language glitch descriptions plus precise temporal spans on paper | Yes, on paper | verified-online=paper-only; public-download=unverified; downloaded-locally=no; converted-locally=no; evaluated-locally=no | Future full-paper extension benchmark if a public artifact is verified later | No official public repo or dataset artifact was confirmed from primary-source checks on 2026-06-08 | Paper reports 5,238 videos from 120 games and a joint semantic + temporal protocol, but this repo cannot execute it today |
| GlitchBench | [S-005](17_source_verification_log.md) | Images plus short text metadata | Image-level descriptions and glitch-type metadata | No | verified-online=yes; downloaded-locally=no; converted-locally=no; evaluated-locally=no | Auxiliary static-image benchmark and qualitative evidence only | Static framing cannot support temporal-detection claims | Paper reports 593 images from 205 games; current HF dataset viewer exposes 607 validation rows under MIT license |
| World of Bugs | [S-006](17_source_verification_log.md) | 2D / 3D game environments, agent observations, downloadable data, standalone builds | Bug scenarios and downloadable train/test data; exact public label schema for this repo is still `TBD / verify` | Potentially yes, but not verified as a drop-in temporal benchmark | verified-online=yes; public-download=yes; downloaded-locally=no benchmark data; converted-locally=no; evaluated-locally=no | Controlled benchmark or case study after a safe data-conversion audit | Environment setup, Unity dependency, Kaggle data handling, and label conversion overhead | Official site and GitHub repo expose standalone builds and Kaggle train/test data links. Operationally heavier than TempGlitch for the current fast-track. |
| Synthetic dynamics datasets in this repo | repo-local | Generated frame folders | Interval labels in `source,start_frame,end_frame,label` CSV | Yes | verified-online=n/a; downloaded-locally=n/a; converted-locally=generated-on-demand; evaluated-locally=Phase 0 sanity checks only | Sanity checks for pipeline mechanics and scorer behavior | Toy distribution; not publishable benchmark evidence by itself | Keep separated from public benchmark results in every report and manuscript draft |

## Interpretation rules

- `verified-online` means the source artifact was confirmed from an official page, paper, repo, or dataset page.
- `public-download` means a real public artifact path was verified, not just claimed in a paper.
- `downloaded-locally` means raw benchmark files are present under gitignored data paths as part of a reproducible local workflow.
- `converted-locally` means labels or media were transformed into this repo's CSV pipeline.
- `evaluated-locally` means the repo actually produced `scores.csv` and `metrics.json` on that benchmark.

## Evidence guardrails

- Do not turn TempGlitch's binary per-video public artifact into temporal-localization claims.
- Do not mark TempGlitch as downloaded until a reproducible subset workflow exists under gitignored `data/`.
- Do not use GlitchBench to justify temporal localization claims.
- Treat World of Bugs as a platform candidate until its downloadable data and labels are inspected against this repo's CSV interfaces.
- Keep synthetic data in the paper as sanity-check-only evidence.
