# NEXT_ACTION.md

Last updated: 2026-06-11T06:32:55+00:00
Commit: `54fa49f37b99dca85fcd9329c8924ede05776c21`

## Current Priority
Complete or unblock Gate 5 Kaggle CUDA smoke/resume artifact.

## Success Criteria
- `environment.json`
- `resume_metadata.json`
- `protocol_audit.json`
- `run_config.json` or `run_config.resolved.json` according to validator
- `dataset_metadata.json`
- `training_metadata.json`
- `loss_history.json`
- `collapse_diagnostics.json`
- `checkpoint.sha256`
- strict validator pass

## If Approval Missing
Prepare request/fingerprint, update docs/cache, commit and push, and report
`BLOCKED_ON_APPROVAL`.

## If Approval Valid
Execute exactly the approved kernel push/smoke, download artifacts, validate, update
playbook/cache, commit and push.

## Current Known Blocker
The 2026-06-11 TempGlitch path has five failed submissions: v1 returned HTTP 409, v2 failed on a
runtime-file path, v3 failed installing `box2d-py`, v4 failed because `/kaggle/input` is
read-only, and v5 assumed a fixed mount path that did not contain the Lance directories. V6 now
discovers the named Lance directories recursively and copies them to `/tmp/lewm_input`. Obtain a
fresh exact approval for fingerprint
`358e2d77c60c3986be2e84f3c6044200ebfcc2a5fe8f68b0800273fc8c7b6910`; do not infer approval from
this cache.
