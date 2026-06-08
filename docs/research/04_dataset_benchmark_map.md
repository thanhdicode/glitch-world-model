# Dataset and Benchmark Map

Public benchmarks should remain the main source of paper-facing evidence. Synthetic or repo-local data can validate mechanics, not novelty or generalization.

| Dataset / Benchmark | Source ID | Data modality | Label type | Temporal labels? | Access status | Planned use | Risk | Verification notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TempGlitch | [S-003](17_source_verification_log.md) | Gameplay videos | Video-level glitchy / glitch-free labels; internal temporal glitch segments described in paper; public file schema `TBD / verify` | Yes, within clips; public annotation export not inspected | verified-online=yes; downloaded-locally=no; converted-locally=no; evaluated-locally=no | Primary temporal benchmark if direct source URL, license, and download path are verified in Phase 2 | Paper says code/data exist at a project website, but the URL and public access path were not recovered from primary sources on 2026-06-08 | Paper verifies 5 temporal glitch categories and 1,500 total videos, but not a repo-ready annotation file format |
| VideoGlitchBench | [S-004](17_source_verification_log.md) | Gameplay videos | Natural-language glitch descriptions plus precise temporal spans | Yes | verified-online=yes; downloaded-locally=no; converted-locally=no; evaluated-locally=no | Full-paper extension benchmark or fallback if public release is verified later | Public code/data release was not verified on 2026-06-08 | Paper reports 5,238 videos from 120 games and a joint semantic + temporal protocol |
| GlitchBench | [S-005](17_source_verification_log.md) | Images plus short text metadata | Image-level descriptions and glitch-type metadata | No | verified-online=yes; downloaded-locally=no; converted-locally=no; evaluated-locally=no | Auxiliary static-image benchmark and qualitative evidence only | Static framing cannot support temporal-detection claims | Paper reports 593 images from 205 games; current HF dataset viewer exposes 607 validation rows under MIT license |
| World of Bugs | [S-006](17_source_verification_log.md) | 2D / 3D game environments, agent observations, downloadable data, standalone builds | Bug scenarios and downloadable train/test data; exact public label schema `TBD / verify` | Potentially yes, but public mapping to this repo's CSV schema is still `TBD / verify` | verified-online=yes; downloaded-locally=no benchmark data; converted-locally=no; evaluated-locally=no | Controlled benchmark or case study after a safe data-conversion audit | Environment setup, Unity dependency, and label conversion overhead | Official docs expose PyPI, GitHub, standalone builds, and Kaggle train/test data, but not a ready-made `source,start_frame,end_frame,label` export |
| Synthetic dynamics datasets in this repo | repo-local | Generated frame folders | Interval labels in `source,start_frame,end_frame,label` CSV | Yes | verified-online=n/a; downloaded-locally=n/a; converted-locally=generated-on-demand; evaluated-locally=Phase 0 sanity checks only | Sanity checks for pipeline mechanics and scorer behavior | Toy distribution; not publishable benchmark evidence by itself | Keep separated from public benchmark results in every report and manuscript draft |

## Interpretation rules

- `verified-online` means the source artifact was confirmed from an official page, paper, repo, or dataset page.
- `downloaded-locally` means raw benchmark files are present under gitignored data paths. No public benchmark in this repo meets that bar yet.
- `converted-locally` means labels or media were transformed into this repo's CSV pipeline. No public benchmark in this repo meets that bar yet.
- `evaluated-locally` means the repo actually produced `scores.csv` and `metrics.json` on that benchmark. No public benchmark in this repo meets that bar yet.

## Evidence guardrails

- Do not mark TempGlitch as downloaded until files exist locally under gitignored `data/`.
- Do not use GlitchBench to justify temporal localization claims.
- Treat World of Bugs as a platform candidate until its downloadable data and labels are inspected against this repo's CSV interfaces.
- Keep synthetic data in the paper as sanity-check-only evidence.
