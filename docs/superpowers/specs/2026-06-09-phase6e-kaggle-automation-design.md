# Phase 6E Kaggle Automation Design

## Understanding Summary

- Build a resumable state-machine orchestrator for the Phase 6E Conv3D video autoencoder learned
  baseline.
- The orchestrator covers preflight, OAuth request, security scans, dataset preparation/upload,
  kernel generation/push/poll, artifact download/validation, and ingestion.
- Dataset upload and GPU kernel push require explicit one-time approval records bound to the
  current fingerprint.
- This implementation phase runs tests and dry-run only. It must not upload a dataset or push a
  Kaggle kernel.
- Locked test remains untouched and no Kaggle GPU result or neural metric may be claimed.

## Decisions

- Architecture: one Python state-machine orchestrator with focused reusable components.
- Resume policy: idempotent; completed steps are verified and skipped.
- Retry policy: at most three attempts for transient API/network failures only.
- GPU policy: one push per kernel fingerprint; running/success fingerprints are never pushed
  again.
- Approval policy: request/approved JSON records, one-time use, fingerprint-bound, consumed when
  a live action starts.
- State/log/package paths: all generated material remains below
  `outputs/kaggle_phase6e_automation/`.
- Dataset policy: private only, license `other`, recursive mode `zip` or `tar`.

## State Machine

```text
preflight
  -> auth_check_or_request_login
  -> repo_and_security_scan
  -> dataset_dry_run
  -> dataset_prepare
  -> dataset_validate_package
  -> dataset_fingerprint
  -> dataset_upload_approval
  -> dataset_create_or_version
  -> kernel_package_generate
  -> kernel_validate_package
  -> kernel_push_approval
  -> kernel_push_once
  -> kernel_poll
  -> artifact_download
  -> artifact_validate
  -> artifact_ingest
  -> complete
```

Dry-run stops before live actions and records what would happen. Approval creation does not run
the approved action; a later live invocation consumes the approval immediately before the side
effect starts.

## Components

- `AutomationConfig`: slugs, paths, expected partition counts, retries, timeout, accelerator,
  recursive mode, and live/dry-run mode.
- `AutomationState`: current/completed/failed steps, blocked reason, sanitized last error,
  approval requirement, attempts, dataset/kernel fingerprints, kernel status, and artifact paths.
- `StateStore`: atomic write through a temporary file and preserves `state.prev.json`.
- `ApprovalStore`: writes request/approved records, validates fingerprints, records
  `one_time_use=true`, and marks `consumed_at`.
- `FingerprintBuilder`: includes git SHA, branch, manifest hash, split hash, package inventory
  hash, kernel script hash, config hash, and expected partition counts.
- `SecurityGuard`: scans tracked repo files, dataset/kernel packages, command strings, and
  redacted logs.
- `CommandRunner`: redacts before writing logs and retries transient failures only.
- `DatasetManager`, `KernelManager`, and `ArtifactManager`: validate and execute their bounded
  responsibilities.
- `Phase6EKaggleOrchestrator`: validates state transitions and coordinates components.

## Security Rules

Forbidden paths/names include `.kaggle/`, `kaggle.json`, `access_token`, `.env`, `.env.*`,
`*.pem`, `*.key`, `id_rsa`, `id_ed25519`, `*.p12`, and `*.pfx`. Kernel packages additionally
forbid `*.pt`, `*.pth`, and `*.ckpt`. Dataset/kernel packages reject `data/raw/` and unrelated
`outputs/` content. Token-like environment values and credential patterns are redacted before
stdout/stderr is written.

No raw command output is persisted. Security, authentication, validation, protocol, metadata,
artifact-schema, GPU quota, and accelerator-unavailable failures are non-retryable.

## Retry And Blocking

Retry only: HTTP `429`, `500`, `502`, `503`, `504`, timeout, connection reset, and temporary
DNS/network errors. Use exponential backoff with a maximum of three attempts per step.

GPU quota exhaustion or accelerator unavailability sets a precise `blocked_reason` and stops
without retry. Polling stops after six hours.

## Package And Artifact Validation

Dataset validation requires private metadata, license `other`, recursive mode `zip` or `tar`,
manifest/split presence, and allowed package content.

Kernel validation requires private metadata, the expected dataset source, allowed Python script,
no credentials/checkpoints/raw data, and a stable kernel fingerprint.

Artifact validation runs before ingestion and requires:

- `video_autoencoder.pt`
- `training_metadata.json` with CUDA device
- `validation_scores.csv` with exactly `1,071` finite score rows
- `phase6e_summary.json`
- `protocol_audit.json` with `test_scored=false`

It writes `artifact_validation_report.md` and `artifact_validation_summary.json`.

## Testing And Acceptance

- Unit-test state backup/atomic behavior, approvals, fingerprint invalidation, security scans,
  redaction, retry classification, GPU blocking, artifact validation, and transition resume.
- Use fake command runners for all side-effect tests.
- Run orchestrator dry-run only against local Phase 6E inputs.
- Run full pytest and ruff checks.
- Verify no generated data, output, checkpoint, or credentials are staged.

