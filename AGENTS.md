# AGENTS.md

## Project Identity

This repository studies latent-surprise methods for video game glitch detection. The current
verified phase is Phase 6E: a real Kaggle CUDA Conv3D autoencoder engineering run with
validation-only metrics. Real LeWorldModel (LeWM), JEPA, and SIGReg integration are not
implemented.

## Scientific Honesty

- `verified` means supported by a checked artifact, repository document, or primary source.
- `experiment-pending` means the experiment has not been run.
- `rejected` means the statement must not appear as a positive claim.
- `future-work` means planned only.
- Register paper-facing claims in `docs/research/16_claim_registry.md`.
- Do not claim LeWM, JEPA, or SIGReg until code, checkpoint loading, inference, and metrics exist.
- Do not claim state of the art.
- Do not claim a locked-test neural result until the validation decision is frozen and the
  locked-test release gate is explicitly opened.

## Engineering Rules

- Preserve `manifest.csv`, `scores.csv`, labels CSV, and `metrics.json` interfaces.
- Keep scorers pluggable through `src/glitch_detection/score_clips.py`.
- Prefer small, testable changes; use tests first for behavioral code.
- Keep methodology aligned with preprocess -> score -> evaluate -> report.
- Do not implement LeWM or fine-tune models unless the task explicitly opens that phase.

## Git And Artifact Hygiene

- Never commit raw data, generated outputs, checkpoints, artifacts, caches, credentials,
  `kaggle.json`, `.env`, access tokens, or private keys.
- Do not commit files under `outputs/`, `data/raw/`, or `data/processed/` except `.gitkeep`.
- Do not revert unrelated user changes.

## Kaggle, GPU, And Locked Test Gates

- Dataset upload and kernel push each require a separate, fingerprint-bound user approval.
- Never upload credentials or print their values.
- Do not run new GPU training unless explicitly requested and approved.
- Locked test must remain untouched until a saved validation decision names one configuration,
  claim scope is recorded, and the user explicitly opens the locked-test gate.

## LeWM Integration

- Treat `external/le-wm` as reference code until an integration audit is complete.
- Audit license, checkpoint provenance, preprocessing, tensor interfaces, and inference first.
- A guarded placeholder or proxy is not a real LeWM result.

## Required Verification

Run before completion:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
```

Document skipped checks and missing dependencies honestly.

## Final Codex Response

Report: changed files, verification evidence, scientific claim status, locked-test status,
unresolved risks, commit SHA/branch, and the recommended next research step.
