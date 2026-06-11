# BOOT.md - Fast Start Context For Agents

Generated: 2026-06-11T06:32:55+00:00
Commit: `54fa49f37b99dca85fcd9329c8924ede05776c21`

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
- Gate 5 is partial.
- Gates 6-10 have not run.
- Locked test is closed.
- LeWM integration engineering exists.
- LeWM gameplay evaluation is not established.

## Immediate Next Task
- Complete or unblock Gate 5 Kaggle CUDA smoke/resume artifact.
- Current known blocker: v5 failed because its fixed Kaggle mount path did not contain the Lance
  directories. The offline v6 package discovers each named Lance directory under
  `/kaggle/input`; its exact fingerprint is awaiting approval.

## Safety
- No Kaggle live action without a current fingerprint-bound approval.
- Dataset upload and kernel push require separate approvals.
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
