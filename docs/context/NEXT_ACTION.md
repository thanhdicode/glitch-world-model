# NEXT_ACTION.md

Last updated: 2026-06-24T08:15:50+00:00
Commit: `8853fc5de1ad85e0fe874f72a9a0ebcd745d01f3`

## Current Priority
Execute roadmap V4 Phase P1 (Statistical & Support Hardening). The project is upgrading from a
bounded evaluation note into a full empirical method paper for Topic A. Authority roadmap:
`docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (Phase P1, LOCAL, no Kaggle)
1. `src/glitch_detection/statistics.py`: add `delong_auroc_test` and `paired_bootstrap_delta`;
   extend `_metric` for `auprc`, `balanced_accuracy`, `mcc`.
2. `src/glitch_detection/analysis.py` (or new `seed_aggregation.py`): add `aggregate_seed_metrics`
   reporting mean +/- std across seed42/43/44.
3. `src/glitch_detection/tempglitch_followup.py` + `scripts/freeze_tempglitch_protocol.py`:
   raise calibration normals 2 -> 4 and use all 14 validation-normal episodes; keep leakage = 0.
4. `scripts/validate_tempglitch_followup.py`: enforce `calibration_normal_count >= 4`.
5. Tests: `tests/test_statistics.py`, `tests/test_seed_aggregation.py`.
6. Register the paired delta-AUROC claim as `experiment-pending` in the claim registry.

## Success Criteria
- DeLong and paired-bootstrap statistics exist with tests.
- Multi-seed aggregation replaces best-row reporting.
- The frozen follow-up split uses >= 4 calibration normals and full validation-normal support.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After P1
P2 learned baselines (Kaggle K1), P3 GlitchBench benchmark (Kaggle K2), P4 SIGReg/action ablation
(Kaggle K3), P5 temporal localization (Kaggle K4 optional), P6 demo, P7 full paper rewrite.
Codex does every local task autonomously and stops only at Kaggle gates K1-K4.

## Current Known Blocker
None blocks P1 (P1 is fully local). The official Springer kit / TeX toolchain blocker only applies
to the final P7 compile. Locked test remains closed.
