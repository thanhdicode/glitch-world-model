# Gate 6 LeWM Training Pilot Results

Status date: 2026-06-11
Result: `partial`

Gate 6 is open for preparation because Gate 5 passed strict CUDA/resume validation. The pilot
configuration and acceptance criteria are frozen in `configs/lewm_gate6_pilot.yaml` and report
45.

The local source audit passed:

- 20 deterministic train-normal episodes and 20,156 four-step windows.
- 10 deterministic validation-normal episodes and 8,993 four-step windows.
- One separate validation-buggy encoding probe and 1,088 four-step windows.
- Zero train/validation source or heuristic-pair overlap.
- Metadata SHA-256 `5aed6612d2c4bcee3da000db08ff56e9283432d4ba8795b7c388155b65916472`.
- Split SHA-256 `717b43f123e89681d81ad92e4c7308104c52a4068c1ef7a47f77230e6e74f207`.

The Gate 6 dataset was uploaded and reached Kaggle status `ready`. Exactly one v3 kernel was
pushed. It reached `ERROR` before epoch 1 because `glitch_detection` was not importable from the
Kaggle script mount. Strict validation failed because all required training artifacts were absent.
This is an infrastructure failure, not a training or model result.

The corrected v5 package stores the source tree as `glitch_detection_src.zip` beside the entry
script and unpacks it before import. Its content-based kernel fingerprint is
`ae0aae43793adb94f8498f8d07c292426e69a0657ba545dbecbfda8682e03504`.
That exact approval was created, validated, consumed, and submitted exactly once. Kaggle CLI then
returned `Expecting value: line 1 column 1 (char 0)` and no remote `lewm-gate6-pilot-v5` kernel
appeared in `kernels list --mine` or `kernels status`. This is preserved as a submission-stage
failure with no same-fingerprint retry.

A secret-safe diagnostic confirmed Kaggle CLI 2.2.1 on Python 3.14.4, authenticated read access,
dataset status `ready`, valid v5 metadata, an existing entry script, and a 447,813-byte package.
One private CPU-only, dataset-free canary was then pushed through the absolute Kaggle executable.
It returned the same JSON parse error and did not appear remotely after exact-slug list/status
checks. The canary was not retried.

This isolates the current blocker to the Kaggle kernel write path rather than Gate 6 source,
dataset attachment, package size, or GPU allocation. Per protocol, no v6 package or live Gate 6
attempt was made after the failed canary.

No Gate 6 checkpoint, loss, encoding result, or gameplay performance metric exists.

Locked test remains unmaterialized and unscored.
