# AGENTS.md

## Project Identity

This repository studies LeWM/JEPA-style latent-surprise methods for video game glitch
detection.

For routine tasks, use the fast context cache before opening the long playbook. For full project
context, roadmap, evidence policy, skills, and next actions, read `PLAYBOOK.md` when the task
requires deep context.

The current execution roadmap is `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md`. Older roadmap
files are historical inputs, not the current next-action authority.

Current verified status:

- Gates 1-8 passed; Gate 9 completed as a limited validation-only window-level pilot.
- Gate 7 produced 10,081 real frozen-checkpoint scores; Gate 8 scored two baselines on the exact
  same canonical Lance manifest.
- A separate research MVP source is ready with 36 train-normal, 14 validation-normal, and 22
  validation-buggy episodes across all five categories.
- The exact 500-update non-locked GPU profile completed as engineering evidence only.
- R4 rerun seed43/44 training artifacts are local SHA256-verified and pass per-seed validators.
- R5 TempGlitch non-locked identical-episode evaluation completed and produced
  provenance-bound episode-level outputs under the frozen validation-only protocol.
- The pair-disjoint TempGlitch follow-up is validator-backed on two calibration normals and a
  same-support 12-normal-negative / 22-buggy-positive evaluation split with zero cross-role
  source, pair, and episode overlap.
- Kaggle-native `WOB-P0` passed with a verified downloaded evidence bundle; WOB-P1 seed42,
  seed43, and seed44 training artifact verification are complete; R5-WOB is positive-probe only
  and R5-XGame is validated bounded non-locked binary evidence.
- Controlled World of Bugs expansion is `LOCAL_WOB_P0_STATUS=BLOCKED_MISSING_INPUTS`,
  `WOB_P0_KAGGLE_STATUS=PASSED`, `WOB_STATUS=WOB_P1_SEED44_TRAINING_VALIDATED`,
  `WOB_P1_TRAINING_STATUS=SEED44_VALIDATED`, `WOB_EVALUATION_STATUS=NOT_STARTED`.
- The first bounded paper draft is complete locally and has a paragraph-level claim audit.
- The next gate is paper build/claim audit followed by an explicit bounded-submission versus
  stronger-compute decision.
- Locked test is closed.
- LeWM gameplay evaluation now includes the earlier one-buggy-episode window pilot plus the
  completed non-locked TempGlitch R5 identical-episode family.

Safe claims include bounded normal-only CUDA training and the exact qualified Gate 7-9 pilot
metrics, research-source readiness, the validated 500-update GPU profile, artifact-backed R4
rerun seed43/44 training evidence, the exact qualified pair-disjoint TempGlitch follow-up,
bounded R5-XGame split results, the R5-WOB positive-probe status, and the narrow WOB-P1
seed42/seed43/seed44 validator-passed training-artifact claims. Do not claim broad LeWM
glitch-detection performance,
superiority, state of the art, temporal localization, SIGReg benefit, WOB evaluation
performance, cross-game generalization, action-conditioning benefit, or a neural locked-test
result.

## Agent Operating Mode

- Work as a senior research engineer: inspect evidence before editing or claiming.
- Use gate-based execution and keep `docs/research/16_claim_registry.md` synchronized.
- Prefer small, testable changes and tests first for behavioral code.
- Preserve unrelated user changes and report skipped checks honestly.
- Never convert scaffolding, fixture output, or smoke evidence into an experiment claim.
- Follow the non-negotiable rules in `RULES.md`.

## Fast Context Policy

Default read order for routine tasks:

1. `RULES.md`
2. `AGENTS.md`
3. `docs/context/BOOT.md`
4. `docs/context/PROJECT_STATE.md`
5. `docs/context/NEXT_ACTION.md`
6. `docs/context/TASK_ROUTER.md`

Open `PLAYBOOK.md` only for roadmap, paper, claim, gate-status, or ambiguous tasks. Use
`docs/context/REPO_MAP.md` before grepping the entire repo. Update
`docs/context/LAST_HANDOFF.md` and rerun context validators before completion.

## Repository Map

- `src/`: reusable pipeline and model integration code.
- `scripts/`: auditable command-line entry points.
- `tests/`: fast default-environment tests.
- `docs/research/`: evidence, protocols, results, and claim registry.
- `docs/roadmap/`: gate definitions and planned work.
- `docs/workflows/`: operational playbooks.
- `configs/`: experiment and runtime configuration.
- `kaggle/`: validation-only launch packages.
- `paper/`: cautious manuscript scaffold and generated tables.
- `external/`: read-only upstream references unless an integration task explicitly says otherwise.

## Engineering Contracts

- Preserve `manifest.csv`, labels CSV, `scores.csv`, and `metrics.json` interfaces.
- Keep scorers pluggable through `src/glitch_detection/score_clips.py`.
- Keep the default install and CI free of heavy GPU dependencies.
- Split by source/pair/episode before windowing; fit train-dependent methods on allowed
  train-normal data only.
- Select configurations and thresholds on validation only.
- Do not edit upstream code under `external/` to make local checks pass.

## Safety Gates

- Non-locked-test Kaggle actions use repository standing authorization after security, license,
  protocol, package, and idempotency checks.
- GPU profile/live launch must read `docs/workflows/failure_modes_registry.md`, pass
  `scripts/run_kaggle_parity_check.py`, provide a matching parity receipt to the live launcher, and
  classify every failure through `src/glitch_detection/failure_triage.py`; only `cuda_oom` may
  advance the batch-size ladder.
- Fingerprints are mandatory audit records and idempotency keys, not approval artifacts.
- Locked test requires a frozen validation decision naming exactly one configuration and claim
  scope plus a separate direct user command.
- Remote resource deletion, credential publication, unlicensed public data, and validator bypass
  remain prohibited.
- Never print or commit credentials, tokens, private keys, `.env`, or `kaggle.json`.
- Never commit raw data, processed data, outputs, Lance datasets, checkpoints, or caches.

## Required Commands

Run before completion:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
python scripts/validate_context_cache.py
```

When pre-commit is available:

```powershell
pre-commit run --all-files
```

## Documentation And Claims

- `verified`: supported by a checked artifact, repository document, or primary source.
- `experiment-pending`: experiment has not run.
- `future-work`: planned only.
- `rejected`: must not appear as a positive claim.
- Paper-facing claims must be registered before use.
- Cite primary sources and keep negative results and limitations visible.

## Final Report

Report changed files, verification evidence, scientific claim status, locked-test and Kaggle-live
status, artifact/credential safety, unresolved risks, branch/SHA, and the next gate.
