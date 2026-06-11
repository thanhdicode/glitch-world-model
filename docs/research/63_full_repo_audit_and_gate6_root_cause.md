# Full Repository Audit And Gate 6 Root Cause

Status date: 2026-06-11
Audited commit: `7d33d911b4fb59f6239416254f162e152b0470ef`

## Current Gate State

- Gates 1-5 passed. Gate 5 is backed by strict Kaggle CUDA train/resume artifact validation.
- Gate 6 is partial. Its deterministic 20 train-normal, 10 validation-normal, and one non-locked
  validation-buggy probe datasets passed source/pair leakage and upstream-loader checks.
- Gate 7 has scorer, manifest, evaluation, and plotting infrastructure only. It has not run.
- Gates 8-9 have not run. Gate 10 and locked test remain closed.

## Pipeline Map

| Area | Primary tracked paths | Role |
|---|---|---|
| Dataset audit | `src/glitch_detection/gate6_data.py`, `scripts/audit_gate6_tempglitch_source.py` | Deterministic normal-only selection, hashes, and leakage checks |
| Lance conversion | `src/glitch_detection/lewm_data.py`, `scripts/build_tempglitch_lewm_lance.py` | TempGlitch video-to-Lance conversion and loader inspection |
| Gate 6 package | `src/glitch_detection/lewm_gate6.py`, `scripts/prepare_lewm_gate6_package.py` | Source/data archives, kernel script, metadata, and package fingerprint |
| Approval safety | `src/glitch_detection/kaggle_automation.py`, `scripts/request_lewm_kaggle_approvals.py` | Fingerprint-bound one-time approvals and credential scans |
| Gate 6 validation | `src/glitch_detection/lewm_gate6.py`, `scripts/validate_lewm_gate6_artifacts.py` | Strict CUDA, loss, checkpoint, encoding, and locked-test checks |
| Gate 7 scoring | `src/glitch_detection/lewm_surprise.py`, `scripts/run_lewm_scoring.py` | Frozen-checkpoint latent-surprise scoring |
| Gate 7 protocol | `scripts/build_tempglitch_validation_manifest.py`, `scripts/run_gate7_lewm_evaluation.py` | Non-locked validation manifest and metrics |
| Governance | `RULES.md`, `PLAYBOOK.md`, `docs/research/16_claim_registry.md` | Gate status, evidence policy, and claim limits |

## Gate 6 Failure Sequence

1. Early Gate 6 package iterations established the dataset/upload path but were not accepted as
   training evidence.
2. The v3 kernel was accepted by Kaggle and reached `ERROR` before epoch 1 because the generated
   script could not import the bundled `glitch_detection` package.
3. The v5 package moved the source archive beside the entry script and extracts it before import.
   Its fingerprint was
   `ae0aae43793adb94f8498f8d07c292426e69a0657ba545dbecbfda8682e03504`.
4. The exact v5 approval was created, validated, consumed, and submitted once. Kaggle CLI 2.2.1
   under Python 3.14.4 returned `Expecting value: line 1 column 1 (char 0)`.
5. Read-only list and status checks found no remote v5 kernel. No same-fingerprint retry occurred.

## Proven

- The Gate 6 dataset slug exists remotely and reports `ready`.
- The v5 kernel directory has valid local metadata, an existing Python `code_file`, the expected
  dataset source, and a root-level source archive.
- The v5 attempt failed before remote resource creation, so it produced no checkpoint, losses,
  encoding proof, or gameplay result.
- Kaggle CLI authentication is sufficient for read-only dataset status and list operations.
- Locked test was not materialized or scored.

## Not Proven

- That Kaggle accepted the v5 save-kernel request.
- That the v5 code would import and train successfully on Kaggle.
- Any gameplay-scale LeWM training, glitch-detection metric, baseline superiority, or paper result.

## Ranked Root-Cause Hypotheses

1. **CLI/API response-path failure.** The installed Kaggle 2.2.1 client raised a JSON parse error
   during save-kernel handling before a remote resource appeared. This is the leading hypothesis.
2. **Request rejection not surfaced safely by the CLI.** Metadata, slug, or account-side policy may
   have produced an empty/non-JSON response that the client reduced to the same parse error.
3. **Windows invocation/path boundary.** The prior `python -c` CLI entry path and relative package
   path add avoidable ambiguity even though earlier pushes used that path.
4. **Package content/size.** Less likely because metadata and required files validate locally, but
   it remains unexcluded until a no-dataset canary succeeds.
5. **General auth/network/platform outage.** Less likely because authenticated read operations
   work, but only a minimal write canary can isolate write-path health.

## Next Live Action Decision

No Gate 6 v6 push is allowed yet. First run a secret-safe diagnostic capture, then submit exactly
one private, CPU-only, dataset-free heartbeat canary through the absolute Kaggle executable and an
absolute package path. If the canary does not appear remotely, stop live Gate 6 work. If it
completes, create a content-changed v6 package/fingerprint and submit that fingerprint once.

## Canary Result

The single canary `huynhdieuthanh/lewm-submit-canary-20260611-163859` used no GPU, dataset,
internet, or repository code. The direct absolute `kaggle.exe kernels push` invocation returned
`Expecting value: line 1 column 1 (char 0)`. After 30 seconds, exact-slug list returned
`Not found`, and status could not access the slug. No retry was made.

This falsifies package size, Gate 6 code, GPU allocation, and dataset attachment as necessary
causes. The active blocker is the Kaggle kernel write path exposed through the installed client,
account, network, or platform response. Read-only authenticated commands remain healthy. Gate 6
v6 was intentionally not created or pushed.
