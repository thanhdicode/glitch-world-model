# BOOT.md - Fast Start Context For Agents

Generated: 2026-06-25T00:00:00+00:00
Commit: `ea7c8609e9cead37d90bcd8c97e9d6e72393a173`

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
- Gates 7-9 completed a validation-only, non-locked evidence lane on canonical TempGlitch support.
- The pair-disjoint TempGlitch follow-up is validator-backed on 2 calibration-normal, 12
  evaluation normal-negative, and 22 evaluation buggy-positive episodes with zero cross-role
  source, pair, and episode overlap.
- K1 learned-baseline intake is validator-backed locally and remains bounded to the cited
  TempGlitch support.
- P3 local GlitchBench preparation remains complete and the K2 input zip SHA256 is
  `d2c6be8f83d99cb6a04578532f0f80d620c168342ff3e630b4e6b5389c62b038`.
- The K2 runner is now repaired:
  - direct read-only `/kaggle/input` validation is supported
  - the scientific full K2 path now includes real LeWM scoring
  - the local LeWM seed-artifact zip SHA256 is
    `bf227ef26ac8316ccbc7456425e6218d2ac2172576fa874c35041b4913d04e69`
- The current executable GlitchBench path remains image-level, synthetic-normal, and not temporal.
- P4 local controlled SIGReg/action tooling exists, but no K3 artifact has been validated.
- Roadmap V4 remains canonical and locked test remains closed.

## Immediate Next Task
- Rerun the direct `/kaggle/input` K2 dry-run on Kaggle.
- Run the scientific full K2 command with the LeWM seed artifact dataset attached.
- Validate the downloaded K2 artifact locally before registering any benchmark metric claim.
- Keep K3 closed until K2 intake is complete.

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
