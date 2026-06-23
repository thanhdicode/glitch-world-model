# 98 - R6 Limitations And Next Benchmark Memo

Date: 2026-06-23

## Limitation Table

| Limitation | Status | Why it matters |
| --- | --- | --- |
| Non-locked validation only | active | no locked-test claim is available |
| Positive-heavy split | active | the evaluation set is `60` buggy-positive versus `12` normal-negative |
| Only `12` normal-negative evaluation episodes | active | false-positive estimates remain fragile |
| No locked-test claim | required | locked test remains closed |
| No cross-game generalization claim | required | the split is source/pair/episode-disjoint, not a demonstrated cross-game benchmark |
| No SOTA claim | required | current evidence is narrow and benchmark-bounded |
| No SIGReg-benefit claim | required | no controlled SIGReg ablation exists in this bundle |
| No temporal-localization claim | required | the current evidence is binary episode-level, not temporal localization |
| `R5-WOB` remains positive-probe only | active | it has zero `evaluation_normal_negative` episodes and is not a valid binary benchmark |
| Repo category field is single-valued | active | validated per-category comparison is limited to `world_of_bugs` support counts only |

## Current Bounded Claim Surface

Allowed:

- `R5-XGame provides bounded non-locked binary validation evidence on a frozen 12-normal-negative / 60-buggy-positive split.`
- `The best recorded configuration reaches AUROC approximately 0.91 on the frozen R5-XGame split.`
- `These results support further investigation of latent surprise as a gameplay glitch signal.`

Forbidden:

- `LeWM detects gameplay glitches generally.`
- `LeWM beats baselines.` without the phrase `within the frozen non-locked R5-XGame split`
- `LeWM is state of the art.`
- `The method generalizes across games.`
- `SIGReg improves glitch detection.`
- `The model performs temporal localization.`
- `Locked-test performance is known.`
- `R5-WOB is a valid binary benchmark.`

## Benchmark-Lane Decision Memo

Compared next lanes:

| Lane | Evidence quality | Access risk | Reviewer value | Compute cost | Decision note |
| --- | --- | --- | --- | --- | --- |
| TempGlitch follow-up | highest existing continuity | low | strong because the repo already has the deepest validated evidence chain there | low to medium | best next step |
| VideoGlitchBench access verification | no local executable artifact yet | high | potentially high if access is solved | low for verification, unknown for full execution | useful parallel planning lane, not the next main gate |
| WOB/XGame expansion | current split already useful but still positive-heavy and non-locked | medium | moderate, but still bounded by limited negatives and WOB positive-probe status | medium to high | not the next main lane |

## Recommended Next Lane

Recommended next benchmark lane:

- `TempGlitch follow-up`

Reasoning:

1. It has the strongest validated evidence lineage already present in the repo.
2. It does not depend on reopening the still-bounded WOB/XGame lane for its scientific value.
3. It is lower-risk than VideoGlitchBench access work and lower-cost than further WOB expansion.
4. It gives the clearest reviewer-facing path to strengthen the paper without overclaiming from the
   current positive-heavy `R5-XGame` split.

## Single Next Action After R6

Freeze a bounded TempGlitch follow-up protocol that upgrades evidence quality without touching
locked test and without broadening claims beyond validated non-locked evidence.
