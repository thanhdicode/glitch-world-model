# WOB Seed43 Post-Run Playbook

Date: 2026-06-19

Status: `WAITING_FOR_WOB_SEED43_ARTIFACT`

## 1. Current Roadmap Status

Completed stages:

- `R0` through `R5` TempGlitch core are complete under the current bounded claim regime.
- `WOB-P0` Kaggle-native audit passed and remains the verified WOB entry checkpoint.
- `WOB-P1` seed42 training artifact is SHA256-verified and validator-passed.
- The non-locked WOB evaluation-readiness gate is frozen as metadata only.
- Robust WOB seed43/44 Kaggle runners and the generalized seed artifact validator are prepared.

Currently waiting:

- The human is running WOB seed43 Kaggle training on commit
  `7119a3f3ceb82a485202f81448cb6ba4c0f5041e`.
- No local action should assume seed43 succeeded until the downloaded artifact bundle and sidecar
  are verified.

Tasks that remain closed:

- WOB evaluation (`R5-WOB`)
- Cross-game comparison (`R5-XGAME`)
- `R6` ablations and failure analysis
- Locked-test materialization or scoring
- Any empirical WOB paper claim beyond artifact-readiness/training-artifact scope

## 2. Seed43 Artifact Intake Checklist

Required files:

- `wob_seed43_artifacts.tar.gz`
- `wob_seed43_artifacts.tar.gz.sha256`

Optional file:

- `wob_seed43_failure_debug.tar.gz` only if Kaggle reports failure or the robust runner emits it

Local SHA256 verification command:

```powershell
Get-FileHash .\wob_seed43_artifacts.tar.gz -Algorithm SHA256
Get-Content .\wob_seed43_artifacts.tar.gz.sha256
```

Validator command:

```powershell
python scripts/validate_wob_seed_artifacts.py --artifact-tarball .\wob_seed43_artifacts.tar.gz --sha256-sidecar .\wob_seed43_artifacts.tar.gz.sha256 --expected-seed 43
```

PASS criteria:

- The locally computed SHA256 exactly matches the `.sha256` sidecar.
- The validator exits successfully and reports `wob_seed43_validated`.
- The artifact preserves the frozen protocol: `action_dim=4`, real-action path, train-normal-only
  fitting, validation-normal checkpoint selection, validation-buggy excluded from fit/selection,
  and locked-test flags all `false`.

FAIL criteria:

- Hash mismatch between tarball and sidecar
- Missing required file(s)
- Validator failure
- Any protocol flag drift, seed mismatch, checkpoint-selection mismatch, or locked-test leakage

## 3. Success Path

If seed43 validates:

1. Record the artifact filename and SHA256 in the working notes.
2. Keep WOB evaluation closed; seed43 validation is still training-artifact evidence only.
3. Prepare and run the seed44 Kaggle cell next, using the already-prepared seed44 robust runner.

The exact next action after a validated seed43 artifact is:

- run the seed44 Kaggle cell, then repeat the same intake and validator procedure for seed44

## 4. Failure Path

If seed43 fails, inspect in this order:

1. Kaggle notebook console summary and final emitted paths
2. Presence or absence of `wob_seed43_artifacts.tar.gz`
3. Presence of `wob_seed43_failure_debug.tar.gz`
4. SHA256 sidecar consistency
5. Local validator output

Failure classification:

- Kaggle environment failure:
  notebook/runtime failure, package/runtime mismatch, storage/runtime interruption, CUDA/device
  issue, or missing mounted inputs before a valid artifact is produced
- Artifact integrity issue:
  missing tarball, missing sidecar, unreadable tarball, hash mismatch, or incomplete upload
- Validator failure:
  tarball opens but violates expected seed/protocol/checkpoint/flag constraints
- Training failure:
  training ran but exited without a validator-passed final artifact; inspect logs and any emitted
  failure-debug package for the recorded failure stage

What the human must upload after a failure:

- Kaggle console/log excerpt showing the final failure point
- `wob_seed43_failure_debug.tar.gz` if it exists
- `wob_seed43_artifacts.tar.gz` and `.sha256` only if Kaggle emitted them

## 5. Seed44 Readiness Note

- The seed44 robust runner is already prepared in-repo.
- Do not run seed44 until the seed43 artifact is downloaded and verified locally.

## 6. Claim Safety

Keep these claim boundaries closed:

- no WOB performance claim
- no cross-game claim
- no action-conditioning benefit claim
- no locked-test claim

Seed43 validation, if it passes, supports only a narrow training-artifact/protocol-compliance
statement and does not open WOB evaluation or paper-facing empirical conclusions.

## 7. Paper Note

Paper writing may continue in parallel with placeholders only.

Do not add new empirical WOB claims to the paper until `R5-WOB` evaluation artifacts exist and
the resulting claim scope is registered and validated.
