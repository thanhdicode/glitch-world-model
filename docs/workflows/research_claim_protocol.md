# Research Claim Protocol

All paper-facing claims belong in `docs/research/16_claim_registry.md`.

| Status | Meaning |
| --- | --- |
| `verified` | Supported by a checked artifact, document, or primary source. |
| `experiment-pending` | Requires an experiment that has not run. |
| `citation-needed` | Requires an unverified source. |
| `rejected` | Evidence contradicts it; do not state it positively. |
| `future-work` | Planned only. |

Evidence must identify the protocol, split, metric source, and limitations. Negative results stay
visible. Proxies must be named as proxies. Do not claim SOTA, temporal localization, LeWM, JEPA,
SIGReg, or locked-test neural performance without direct evidence.

Run `python scripts/check_claim_registry.py` before a research release.
