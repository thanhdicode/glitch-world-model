# R3/R4 Multi-Seed Status Audit

Date: 2026-06-17

Evidence class: repository, local-artifact, and validator audit

## Summary

This record supersedes the earlier R4 live-log-only status for the 2026-06-17 rerun of seeds 43
and 44. The downloaded local archives are now present under ignored paths, their `.sha256` sidecar
files match the computed SHA256 values, and both extracted seed roots pass
`scripts/validate_lewm_r3_seed_artifacts.py`.

This confirms that the R4 rerun seed43/44 training artifacts are artifact-backed. It does not
create any R5 detection metric, AUROC, AUPRC, superiority, temporal-localization, SIGReg-benefit,
WOB, or locked-test claim.

## Local Archive Verification

Local archive destination:

- `artifacts/downloads/r4_rerun_2026_06_17/`

Local extraction destination:

- `artifacts/verified/r4_rerun_2026_06_17/`

| Artifact | Local availability | SHA256 | Local verification | Notes |
|---|---:|---|---|---|
| `r3_seed43_artifacts.tar.gz` | yes | `3ec2fa25b2b2b952bcd1087aeb755c2b0c413fa95b9ec9a71a320f5df9dd33f7` | matched `.sha256` and `Get-FileHash` | Extracted and validator-passed. |
| `r3_seed44_artifacts.tar.gz` | yes | `ffd6d917f134f3cce37cd0a1e666b10ab1122678d9c3f483936f9b1ad69efa83` | matched `.sha256` and `Get-FileHash` | Extracted and validator-passed. |
| `r4_seed43_44_artifacts_bundle.tar.gz` | yes | `4d4575679a91ab54ae58005bae6a483bdf63e06750336400f3448873ee0afd01` | matched `.sha256` and `Get-FileHash` | Bundle integrity verified. |

## Validator Commands

```powershell
python scripts/validate_lewm_r3_seed_artifacts.py `
  --artifact-root artifacts/verified/r4_rerun_2026_06_17/r3_seed43 `
  --expected-seed 43 `
  --expected-target-updates 15000

python scripts/validate_lewm_r3_seed_artifacts.py `
  --artifact-root artifacts/verified/r4_rerun_2026_06_17/r3_seed44 `
  --expected-seed 44 `
  --expected-target-updates 15000
```

Both commands passed locally with:

- `locked_test_materialized: false`
- `locked_test_scored: false`

## Seed Table

| Seed | Stage | Target optimizer updates | Updates completed | Early-stopped | Reason | Best update | Best validation loss | Checkpoint reload | Leakage / locked-test flags | Status |
|---:|---|---:|---:|---|---|---:|---:|---|---|---|
| 42 | R3 | 15000 | 3000 | true | previously documented | 500 | `0.657468929663858` | separately documented | validation-buggy fit/select false; locked test not materialized/scored | LOCAL_EXTRACT_PRESENT / ARCHIVE_PROVENANCE_SEPARATE |
| 43 | R4 rerun | 15000 | 3000 | true | `early_stopping_patience` | 500 | `0.615883181833121` | validator passed | validation-buggy fit/select false; locked test not materialized/scored | ARTIFACT_BACKED_RERUN |
| 44 | R4 rerun | 15000 | 8000 | true | `early_stopping_patience` | 5500 | `0.6347979751979919` | validator passed | validation-buggy fit/select false; locked test not materialized/scored | ARTIFACT_BACKED_RERUN |

## Phase Status

| Item | Status |
|---|---|
| FIX-0 GPU capability guard | DONE |
| R3 seed42 | LOCAL_EXTRACT_PRESENT / ARCHIVE_PROVENANCE_SEPARATE |
| R4 seed43 | ARTIFACT_BACKED_RERUN |
| R4 seed44 | ARTIFACT_BACKED_RERUN |
| R4 bundle | ARTIFACT_BACKED_RERUN |
| R5 | NOT_STARTED |
| WOB expansion | NOT_STARTED |
| Locked test | UNTOUCHED / NOT_MATERIALIZED / NOT_SCORED |

## Safe Claims

- The exact 500-update GPU profile completed as engineering evidence only.
- R4 rerun seed43/44 training artifacts are artifact-backed after local SHA256 verification and
  per-seed validator checks.
- R4 rerun seed43 stopped early at update 3000 and seed44 stopped early at update 8000 under the
  frozen non-locked protocol.
- Validation-buggy data was not used for fit or selection in the validated rerun artifacts.
- Locked test remained unmaterialized and unscored.
- R5 has not started.

## Unsafe Claims

- R5 identical-episode evaluation has started.
- LeWM detects glitches, outperforms baselines, or is state of the art.
- SIGReg benefit, temporal localization, WOB expansion, or neural locked-test performance.
- R4 rerun training artifacts imply AUROC, AUPRC, or paper-grade detection performance.

## Next Action

Prepare the R5 identical-episode evaluation on the non-locked research MVP. Do not execute R5 or
touch locked test without an explicit command.
