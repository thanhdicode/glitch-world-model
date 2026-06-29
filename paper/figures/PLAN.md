# Figure Plan

No visual data are invented in the submission package. The planned figures below define placement,
supported evidence, and claim scope before any assets are created or uploaded to the official
LLNCS kit.

| Figure | Placement | Purpose | Data or source | Supported claim IDs |
| --- | --- | --- | --- | --- |
| Pipeline diagram | Method / Protocol transition | Show normal-only fit -> frozen window scoring -> episode aggregation -> normal calibration -> evaluation | `paper/sections/04_method.tex`, `paper/sections/05_protocol.tex`, report 101 | C-090, C-092 |
| Split protocol diagram | Experimental Protocol | Show source/pair/episode assignment before windowing, with the two TempGlitch calibration normals and 12/22 evaluation support | report 101, appendix C split protocol | C-090 |
| Qualitative timeline panel | Results / Discussion | Show one representative buggy window-score trajectory for the best TempGlitch LeWM row, explicitly as a qualitative-only diagnostic figure | `paper/figures/fig_timeline_example_receipt.json`; generated from pair-disjoint follow-up selection files plus validated R5 raw LeWM window scores with `temporal_metrics_claimed=false` | C-098, C-115 |
| Evidence matrix diagram | Reproducibility / Discussion | Show TempGlitch, K1, K2, K3, qualitative timelines, and separate R5-XGame evidence with claim boundaries | claim registry, reports 101/118/122/126/128 | C-095, C-097, C-098, C-113, C-114 |
| Claim-boundary diagram | Discussion / Appendix E | Show which statements stay inside the frozen-split evidence boundary and which are forbidden | claim registry, report 106, appendix E | C-091, C-093 |

Any later plotted score distribution, ROC, or PR figure must record its generating script,
command, exact input hash, split, seed/configuration, generation date, and supported claim IDs.
