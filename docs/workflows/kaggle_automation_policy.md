# Kaggle Automation Policy

## Standing Authorization

Codex may perform all non-locked-test Kaggle actions without a per-action approval artifact:
dataset create/version, kernel push/version, GPU execution, polling, artifact download, and
public publication after validation.

Fingerprints are audit identifiers and idempotency keys. They are not permissions.

## Locked-Test Boundary

Locked-test materialization or scoring is not covered by standing authorization and requires a
separate direct user command naming the frozen configuration and claim scope.

## Public Release Gate

Public datasets and kernels require credential scanning, locked-test scanning, an inventory,
recorded license and redistribution permission, explicit owner/slug metadata, and false
locked-test flags.

Generated kernels must not assume auxiliary package files are available beside
`/kaggle/src/script.py`. Dependencies and repository code must be embedded in the configured code
file, resolved from an explicit Kaggle input, or loaded from a documented immutable source.

## Prohibited Actions

Automation is not authorized to delete remote Kaggle resources, publish credentials or private
data, weaken validators, bypass gate order, or retry a runtime failure without a changed
fingerprint.

## Retry And Audit

Transient network failures may retry at most three times. A remote version is pushed once per
kernel fingerprint; established versions are polled rather than resubmitted. Commands, hashes,
visibility, remote versions, outcomes, and downloaded artifact hashes are recorded under ignored
outputs.

## Required Downloaded Artifacts

- run config and environment
- dataset/training metadata
- loss history and collapse diagnostics
- checkpoint and SHA-256
- protocol audit
- resume metadata
- validation scores/metrics when the gate requires them

## Release Check

Run the gate-specific local validator after download. Standing authorization, Kaggle status,
logs, or a checkpoint alone do not prove a gate. The validator must confirm CUDA, required
hashes, finite outputs, and locked-test false flags.

Never include locked-test data in a validation-only package.
