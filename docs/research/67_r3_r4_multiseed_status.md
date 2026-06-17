# R3/R4 Multi-Seed Status Audit

Date: 2026-06-17

Evidence class: repository and local-artifact audit

## Summary

This audit reconciles the current repository state, local Kaggle-downloaded folders, and the
human-provided R3/R4 live-run summary. It does not rerun training, open locked test, score locked
test, or use validation-buggy data for fit/select.

The important boundary is artifact persistence. The R4 seed43/44 live logs reportedly validated
training success and created archives, but the actual `.tar.gz` files were not present locally
during this audit. Therefore R4 remains live-log validated but not fully artifact-backed.

## Evidence Search

| Expected file | Local availability | Expected SHA256 | Audit result |
|---|---:|---|---|
| `r3_seed42_artifacts.tar.gz` | not found | `a51fa19517b69cadcd96273e37094fed50bd14440d854ce0dac521b78a580d48` | LOG_VERIFIED_BUT_ARTIFACT_MISSING / NEEDS_ARTIFACT_VERIFICATION |
| `r3_seed43_artifacts.tar.gz` | not found | `ec75a1df25801c61f12d0a4cbead0d024aa6413e3d2ae9341362478b92a0e1ad` | LIVE_LOG_VALIDATED_BUT_ARTIFACT_PERSISTENCE_UNRESOLVED |
| `r3_seed44_artifacts.tar.gz` | not found | `55037ef74d98965c0fe60ae2bc029d92b7364c42c8c89acecbd04537936f36fc` | LIVE_LOG_VALIDATED_BUT_ARTIFACT_PERSISTENCE_UNRESOLVED |
| `r4_seed43_44_artifacts_bundle.tar.gz` | not found | `8e66bfdb27b2b908b151b9404f16a83a8e2c63eaa9a129ac5bef57ac2c103de1` | LIVE_LOG_CREATED_BUT_ARTIFACT_PERSISTENCE_UNRESOLVED |

Local folders under `artifacts/kaggle_kernel_output/` contain repo snapshots from Kaggle output,
not the expected tar archives.

## Seed Table

| Seed | Stage | Target optimizer updates | Updates completed | Early-stopped | Best update | Best validation loss | Checkpoint reload | Leakage / locked-test flags | Status |
|---:|---|---:|---:|---|---:|---:|---|---|---|
| 42 | R3 | 15000 | 3000 | true | 500 | `0.657468929663858` | reported valid in handoff context | validation-buggy fit/select false; locked test not materialized/scored | LOG_VERIFIED_BUT_ARTIFACT_MISSING / NEEDS_ARTIFACT_VERIFICATION |
| 43 | R4 | 15000 | 3000 | true | 500 | `0.615883181833121` | live-log verified | validation-buggy fit/select false; locked test not materialized/scored | LIVE_LOG_VALIDATED_BUT_ARTIFACT_PERSISTENCE_UNRESOLVED |
| 44 | R4 | 15000 | 8000 | true | 5500 | `0.6347979751979919` | live-log verified | validation-buggy fit/select false; locked test not materialized/scored | LIVE_LOG_VALIDATED_BUT_ARTIFACT_PERSISTENCE_UNRESOLVED |

## Failed Persistence Event

Kaggle Version 1 later failed before successful artifact persistence because it reran an old
notebook cell without `setup_runtime.sh` and hit:

```text
ModuleNotFoundError: No module named 'glitch_detection'
```

This is an artifact-persistence / saved-version rerun failure, not evidence that the live seed43
or seed44 training logs were invalid. It also does not create artifact-backed status.

## Phase Status

| Item | Status |
|---|---|
| FIX-0 GPU capability guard | DONE |
| R3 seed42 | LOG_VERIFIED_BUT_ARTIFACT_MISSING / NEEDS_ARTIFACT_VERIFICATION |
| R4 seed43 | LIVE_LOG_VALIDATED_BUT_ARTIFACT_PERSISTENCE_UNRESOLVED |
| R4 seed44 | LIVE_LOG_VALIDATED_BUT_ARTIFACT_PERSISTENCE_UNRESOLVED |
| R4 bundle | LIVE_LOG_CREATED_BUT_ARTIFACT_PERSISTENCE_UNRESOLVED |
| R5 | NOT_STARTED |
| WOB expansion | NOT_STARTED |
| Locked test | UNTOUCHED / NOT_MATERIALIZED / NOT_SCORED |

## Safe Claims

- FIX-0 GPU capability guard exists on `main`.
- R4 seed43/44 were live-log validated, but artifact persistence is unresolved.
- R3/R4 runs used validation-normal for checkpoint selection according to the provided run
  summaries, and validation-buggy was not used for fit/select.
- Locked test remained unmaterialized and unscored.
- R5 not started.
- No detection metrics yet.

## Unsafe Claims

- R4 is fully artifact-backed.
- All seeds completed 15,000 optimizer updates.
- R5 episode-level evaluation has started.
- LeWM detects glitches, outperforms baselines, or is state of the art.
- SIGReg benefit, temporal localization, WOB expansion, or neural locked-test performance.

## Next Action

Recover/persist the R4 archives and bundle before R5. Do not rerun training unless artifact
recovery fails. After recovery, compute SHA256 for each archive and update this record only if the
hashes match the expected values above.
