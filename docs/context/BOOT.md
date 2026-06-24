# BOOT.md - Fast Start Context For Agents

Generated: 2026-06-24T08:15:50+00:00
Commit: `8853fc5de1ad85e0fe874f72a9a0ebcd745d01f3`

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
The current execution roadmap is `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

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
  training artifacts are now validator-backed, `R5-WOB` is validated as a positive-probe bundle,
  and `R5-XGame` compute is now intake-validated for both the live output directory and the
  repaired tarball/sidecar bundle.
- The best recorded `R5-XGame` configuration reached AUROC `0.909722` on the frozen non-locked
  12-negative / 60-positive split, but this remains bounded validation evidence only.
- The pair-disjoint TempGlitch follow-up is validator-backed on 2 calibration-normal, 12
  evaluation normal-negative, and 22 evaluation buggy-positive episodes with zero cross-role
  source, pair, and episode overlap.
- Roadmap V4 is now canonical and reopens the evidence lane for a full Topic-A method-paper
  upgrade while preserving the existing anti-overclaim and locked-test rules.
- Gate 10 is closed.
- Locked test is closed.
- LeWM gameplay evaluation now exists for the non-locked TempGlitch research MVP only; locked
  test remains unopened, and WOB remains limited to audit-plus-training-artifact evidence.

## Immediate Next Task
- Execute roadmap V4 Phase P1 (Statistical & Support Hardening). The project is upgrading from a
  bounded evaluation note into a full empirical method paper for Topic A.
- Add paired-comparison statistics, multi-seed aggregation, and a four-calibration-normal
  TempGlitch follow-up freeze while keeping leakage at 0.
- Keep locked test closed and stop before Kaggle gates K1-K4.

## Safety
- Non-locked-test Kaggle actions use standing Kaggle authorization after security, license,
  protocol, and package validation.
- Fingerprints are audit/idempotency records, not approval artifacts.
- Locked-test materialization or scoring requires a separate direct user command.
- No locked-test materialization or scoring.
- No data, output, checkpoint, Lance dataset, cache, `.env`, token, or `kaggle.json` commits.
- No new performance, superiority, SIGReg-benefit, action-benefit, cross-game, temporal-
  localization, SOTA, or neural locked-test claim may appear until a supporting artifact is
  validated.
- No broad WOB/R5-XGame detection-performance, cross-game, action-conditioning, or
  SIGReg-benefit claim outside the exact qualified non-locked bundles.

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
