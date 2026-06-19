# BOOT.md - Fast Start Context For Agents

Generated: 2026-06-19T15:35:03+00:00
Commit: `ba024d8b1fd41f7782b644d3461bce260984083a`

## Read Order
1. `RULES.md`
2. `AGENTS.md`
3. `docs/context/BOOT.md`
4. `docs/context/PROJECT_STATE.md`
5. `docs/context/NEXT_ACTION.md`
6. `docs/context/LAST_HANDOFF.md`
7. `docs/context/TASK_ROUTER.md`

Only open `PLAYBOOK.md` for roadmap, paper, claim, gate-status, or ambiguous tasks, or when the
context cache is stale. Use `docs/context/REPO_MAP.md` before broad repo searches.
The current execution roadmap is `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md`.

## Current Status
- Gates 1-4 passed at engineering/smoke level.
- Gate 5 passed strict Kaggle CUDA/resume artifact validation.
- Gate 6 v8 completed normal-only CUDA training and passed strict checkpoint/reload/encoding
  validation with locked-test flags false.
- Gates 7-9 completed a validation-only, non-locked, window-level pilot on one canonical Lance
  manifest.
- A separate non-locked research MVP source is ready with 36 train-normal, 14 validation-normal,
  and 22 validation-buggy episodes across all five categories.
- The exact 500-update research-MVP GPU profile completed as engineering evidence only.
- R4 rerun seed43/44 training artifacts are local SHA256-verified and pass per-seed validators.
- R5 identical-episode evaluation completed on the non-locked research MVP and wrote
  provenance-bound episode-level outputs.
- Local `WOB-P0` remains blocked on missing tar files, the Kaggle-native `WOB-P0` pass is
  verified from the downloaded evidence bundle, and WOB-P1 seed42/seed43/seed44 training
  artifact verification is complete.
- The seed42 non-locked WOB evaluation-readiness gate is frozen, all three planned WOB-P1
  training artifacts are now validator-backed, and the non-locked `R5-WOB` evaluation path
  remains closed pending a separate explicit human command.
- Gate 10 is closed.
- Locked test is closed.
- LeWM gameplay evaluation now exists for the non-locked TempGlitch research MVP only; locked
  test remains unopened, and WOB remains limited to audit-plus-training-artifact evidence.

## Immediate Next Task
- Preserve the verified Kaggle-native `WOB-P0` bundle, the seed42/seed43/seed44 training artifact
  hashes, and the frozen evaluation-readiness metadata.
- Keep the non-locked `R5-WOB` evaluation path closed until a separate explicit human command
  authorizes evaluation.
- Do not touch locked test.

## Safety
- Non-locked-test Kaggle actions use standing Kaggle authorization after security, license,
  protocol, and package validation.
- Fingerprints are audit/idempotency records, not approval artifacts.
- Locked-test materialization or scoring requires a separate direct user command.
- No locked-test materialization or scoring.
- No data, output, checkpoint, Lance dataset, cache, `.env`, token, or `kaggle.json` commits.
- No broad LeWM superiority, SIGReg benefit, temporal localization, SOTA, or neural locked-test
  claim from the current non-locked evidence bundle.
- No WOB detection-performance, cross-game, or action-conditioning claim from the seed42/seed43
  training artifacts.

## Required Checks
```powershell
python scripts/update_context_cache.py --refresh-boot
python scripts/validate_context_cache.py
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
pre-commit run --all-files
```

## Fast Workflow
- Start with the context files and task router.
- Open only the files named by the router plus files discovered with targeted `rg`.
- Update `docs/context/LAST_HANDOFF.md` after each task.
- Regenerate context cache before final verification.
- Treat `PLAYBOOK.md` as the long-form source of truth, not the default first read for every
  routine code edit.
