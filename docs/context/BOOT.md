# BOOT.md - Fast Start Context For Agents

Generated: 2026-06-12T05:15:10+00:00
Commit: `acb5e4c72e65cbc150593501c13bbda682c0b396`

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

## Current Status
- Gates 1-4 passed at engineering/smoke level.
- Gate 5 passed strict Kaggle CUDA/resume artifact validation.
- Gate 6 data passed audit/materialization; v7 dataset readiness now reconciles status/files/
  metadata/list, and kernel v7 version 1 failed on duplicate nested Lance mount directories.
- Gate 7 infrastructure exists but experiments have not run; Gates 8-10 have not run.
- Locked test is closed.
- LeWM integration engineering exists.
- LeWM gameplay evaluation is not established.

## Immediate Next Task
- Repair Gate 6 Lance mount discovery for the verified duplicate nested-directory layout and
  validate the next changed kernel fingerprint strictly.
- Do not run Gate 7 experiments until Gate 6 strictly passes.

## Safety
- Non-locked-test Kaggle actions use standing Kaggle authorization after security, license,
  protocol, and package validation.
- Fingerprints are audit/idempotency records, not approval artifacts.
- Locked-test materialization or scoring requires a separate direct user command.
- No locked-test materialization or scoring.
- No data, output, checkpoint, Lance dataset, cache, `.env`, token, or `kaggle.json` commits.
- No LeWM detection, superiority, SIGReg benefit, temporal localization, SOTA, or neural
  locked-test claim before the documented gates pass.

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
