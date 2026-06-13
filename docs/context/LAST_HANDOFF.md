# LAST_HANDOFF.md

Last completed task: Claude GitHub master prompt and research roadmap v3
Commit: pending
Date: 2026-06-13

## What Changed

- Added a token-efficient master prompt for Claude/strong GitHub coding agents.
- Added Roadmap v3 with the critical path from exact 500-update profile through paper submission.
- Synchronized Claude, Copilot, AGENTS, PLAYBOOK, context-cache generation, and claim registry.
- Recorded the engineering causes of prior profile delays and anti-stall execution rules.
- No Kaggle, GPU, locked-test, or paper-claim action was performed.

## Checks Passed

- `python scripts/validate_research_release.py --ci` passed.
- `python scripts/check_claim_registry.py` passed with 59 claims including the new protocol claim.
- `python -m pytest` passed with 277 tests.
- Ruff, doctor, context validation, and pre-commit passed.

## Safety Status

- Locked test remains closed, unmaterialized, and unscored.
- No live Kaggle action was performed.
- No long GPU job was run.
- No secret material was printed or committed.
- No model-performance claim was added.
- Roadmap v3 is a protocol artifact, not experiment evidence.

## Gate Status After Task

- Gates 1-8 remain passed.
- Gate 9 remains only the limited non-locked one-buggy-episode validation pilot.
- Research MVP source readiness remains unchanged.
- Gate 10 and locked test remain closed.

## Open Blockers

- The 500-update Kaggle GPU throughput/VRAM profile has not run.
- Main training batch size, evaluation interval, and wall-clock budget are not frozen.
- Multi-seed episode-level results and robust calibration do not yet exist.

## Next Recommended Task

- Execute Roadmap v3 Stages R0-R1: implement and strictly validate the exact 500-update
  non-locked Kaggle GPU profile.

## Files Likely Relevant Next

- `docs/agents/CLAUDE_OPUS_GITHUB_MASTER_PROMPT.md`
- `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md`
- `docs/superpowers/plans/2026-06-13-lewm-500-update-kaggle-gpu-profile.md`
- `src/glitch_detection/lewm_training.py`
