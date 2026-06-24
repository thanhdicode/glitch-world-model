# Paper Source Matrix

Date: 2026-06-24
Status: active paper-writing control document

## Manuscript Surface Matrix

| Surface | Evidence authority | Claim boundary |
| --- | --- | --- |
| Abstract | reports 101, 96; C-084/C-088/C-090--C-092 | bounded observations and limitations only |
| Introduction | claim registry; verified bibliography | motivate task; no performance claim |
| Related Work | `paper/references.bib` | context only; no local metric support |
| Problem Formulation | reports 101/96; protocol code | binary episode discrimination, not localization |
| Method | LeWM audit, reports 69/101, scorer interfaces | no architecture novelty or SIGReg benefit |
| Experimental Protocol | report 101; C-090/C-092 | exact roles, support, overlap, false locked flags |
| Datasets | reports 101/96; C-079/C-082 | keep TempGlitch, XGame, and WOB surfaces separate |
| TempGlitch Results | report 101; C-090--C-092 | frozen non-locked same-support observation |
| R5-XGame Results | reports 96/97; C-084/C-088/C-089 | frozen 12/60 split; no cross-game inference |
| Discussion | reports 98/101; C-079/C-082/C-091 | limitations and future work remain visible |
| Reproducibility | report 101; validators; C-092/C-093 | hashes and controls, not new evidence |
| Limitations | claim registry; reports 98/101 | enumerate all blocked claims |
| Conclusion | claim audit 106 | further-investigation language only |

## Literature Groups

| Group | Sources | Allowed use | Forbidden inference |
| --- | --- | --- | --- |
| JEPA/video prediction | `ijepa`, `vjepa`, `lewm` | latent prediction motivation | repository superiority or novelty |
| Latent world models | `worldmodels`, `planet`, `dreamerv3` | modeling lineage | control/planning performance here |
| Video anomaly detection | `sultani2018ucfcrime`, `park2020mnad` | related formulation | direct metric comparability |
| Gameplay glitches | `glitchbench`, `tempglitch` | task and temporal motivation | leaderboard or broad benchmark claim |
| Automated game testing | `politowski2022automatedtesting` | QA context | replacement of human QA |
| OOD/calibration | `hendrycks2017baseline`, `guo2017calibration` | scalar-score and calibration caution | calibrated deployment probability |
| Leakage/reproducibility | `kaufman2011leakage`, `kapoor2023leakage`, `pineau2021reproducibility` | split and reporting discipline | proof that all future work is leakage-free |

## Evidence Rule

No result prose may be supported from memory, terminal output alone, or an unvalidated draft.
TempGlitch claims resolve to report 101; R5-XGame claims resolve to reports 96/97; R5-WOB is
limited by C-079/C-082. The paragraph-level map is report 106.
