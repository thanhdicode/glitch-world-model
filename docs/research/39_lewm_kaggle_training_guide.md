# Gate 5 LeWM Kaggle Training Guide

The current Kaggle foundation is validation-only and locked-test fail-closed. It prepares a
runnable private CUDA training package, scans it for credentials, records separate dataset/kernel
fingerprints, and requires fresh fingerprint-bound approvals before any live action.

## Required Live Sequence

1. Build and inspect train and validation Lance datasets.
2. Prepare the private Kaggle package with `scripts/prepare_lewm_kaggle_package.py`.
3. Review package inventory and config hashes.
4. Request and consume a dataset-upload approval bound to that fingerprint.
5. Request and consume a separate kernel-push approval bound to the final kernel fingerprint.
6. Run CUDA smoke, download artifacts, and verify checkpoint resume.

No locked-test dataset is included. Gate 5 remains incomplete because no locally validated LeWM
Kaggle CUDA train/resume artifact exists. An approval record, upload, or kernel push by itself
does not prove successful training.

On 2026-06-11, the approved TempGlitch dataset upload was confirmed ready and matched the local
Lance package inventory by file name and size. One exact fingerprint-approved kernel push first
returned HTTP `409 Conflict`; the approval was consumed and no run or downloaded artifacts
existed. See
[the current-state audit](41_gate5_current_state.md),
[approval status](42_gate5_kernel_approval_status.md), and
[execution record](43_gate5_kaggle_cuda_smoke_results.md).

The local 409 diagnosis found that the consumed package reused the dataset slug as the kernel
slug. Current package preflight rejects placeholder owners, kernel/dataset slug equality, missing
kernel code files, dataset-source mismatches, and consumed approval reuse.

A second exact approval for fingerprint `4d1108...e3f8` was created and consumed for one v2
kernel push. Kaggle accepted version 1, then the run failed before training because the generated
script looked for `/kaggle/src/lewm-runtime.txt`, which Kaggle did not place beside
`/kaggle/src/script.py`. The strict artifact validator failed because the required Gate 5
artifacts were missing.

The generator now makes the kernel clone the repository and install from
`requirements/lewm-runtime.txt`. A new ignored package/request uses kernel slug
`huynhdieuthanh/lewm-gate5-cuda-smoke-v3` and waits for fresh approval of fingerprint
`47107246ea537fce9c435717301b12c0408f296b34567602f6408b77a5d856c9`.

A third exact approval for fingerprint `47107246...56c9` was created and consumed for one v3
kernel push. Kaggle accepted version 1, then the run failed before training because full
`stable-worldmodel[env,train]` installation pulled `box2d-py`, which failed to build on Kaggle
Python 3.12. The strict artifact validator again failed because the required Gate 5 artifacts
were missing.

The generator now clones the repository into `/tmp/glitch-world-model`, keeping the clone out of
Kaggle output artifacts, and installs only the minimal LeWM smoke dependencies. A new ignored
package/request uses kernel slug `huynhdieuthanh/lewm-gate5-cuda-smoke-v4` and waits for fresh
approval of fingerprint `e3a3ad6bcfd73c99ee295003041db7651e375a1d970b11bd3665a7393c87382a`.

The approved v4 push installed the minimal runtime and reached the Lance loader, but failed before
epoch 1 because `stable-worldmodel==0.1.1` attempted to create writable Lance connection state
under read-only `/kaggle/input`. V5 copied train and validation Lance directories to
`/tmp/lewm_input`, but failed because Kaggle did not expose them under the fixed dataset-slug
mount path. V6 resolves each uniquely named Lance directory recursively under `/kaggle/input`
before copying it. V6 is prepared offline and remains unapproved.

The reusable runner `scripts/run_kaggle_lewm.py` was first verified locally on synthetic data.
On 2026-06-11, reduced real-gameplay CPU smokes also completed forward/backward and hash-matching
resume from epoch 1 to epoch 2 for both the TempGlitch zero-action and WOB real-action paths.
This does not establish Kaggle CUDA training or gameplay glitch-detection performance.

The generated Gate 5 kernel now fails closed without CUDA, trains once, resumes once with the same
config/data hashes, and requires the resumed epoch to advance. Downloaded artifacts must pass
`scripts/validate_lewm_kaggle_artifacts.py`. The validator rejects missing artifacts, non-finite
losses or collapse diagnostics, hash/resume mismatches, non-CUDA execution, and locked-test flags
in protocol or training metadata.

## Quota Policy

- 50%: dual-primary LeWM.
- 25%: CNN-LSTM, VideoMAE, and TimeSformer.
- 15%: LeWM ablations.
- 10%: open VLM.
