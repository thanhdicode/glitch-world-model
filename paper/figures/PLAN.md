# Figure Plan

No visual data are invented in the bounded paper package. The planned figures below define
placement, supported evidence, and claim scope before any assets are created.

| Figure | Placement | Purpose | Data or source | Supported claim IDs |
| --- | --- | --- | --- | --- |
| Pipeline diagram | Method / Protocol transition | Show normal-only fit -> frozen window scoring -> episode aggregation -> normal calibration -> bounded evaluation | `paper/sections/04_method.tex`, `paper/sections/05_protocol.tex`, report 101 | C-090, C-092 |
| Split protocol diagram | Experimental Protocol | Show source/pair/episode assignment before windowing, with the two TempGlitch calibration normals and 12/22 evaluation support | report 101, appendix C split protocol | C-090 |
| Evidence gate diagram | Reproducibility / Discussion | Show engineering evidence -> validated non-locked TempGlitch follow-up -> separate R5-XGame evidence -> locked test closed | claim registry, report 101, report 96, context state | C-082, C-084, C-092 |
| Claim-boundary diagram | Discussion / Appendix E | Show which statements stay inside the frozen-split evidence boundary and which are forbidden | claim registry, report 106, appendix E | C-091, C-093 |

Any later plotted score distribution, ROC, or PR figure must record its generating script,
command, exact input hash, split, seed/configuration, generation date, and supported claim IDs.
