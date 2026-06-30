# BOOT.md - Fast Start Context For Agents

Generated: 2026-06-30T00:00:00+07:00
Commit: `5b45fb656bebde09d8788772f7b02c28be27c8c4`

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
  and the user-downloaded K-B / `R5-XGame` output is final-intake-validated for both the live
  output directory and the tarball/sidecar bundle.
- The best recorded K-B / `R5-XGame` configuration is LeWM seed44 with `lewm_mse_max` and
  `top2_mean`, reaching AUROC `0.909722` and AUPRC `0.981384` on the frozen non-locked
  12-negative / 60-positive split; this remains bounded validation evidence only.
- The expanded K-A TempGlitch Kaggle lane now has a user-downloaded, locally intake-reviewed
  validation artifact. It is safe only as auxiliary support-expansion evidence: 2 calibration
  normals, 67 evaluation episodes (38 buggy-positive / 29 normal-negative), zero cross-role
  overlap, best recorded LeWM AUROC `0.700544`, and no significance artifact.
- The pair-disjoint TempGlitch follow-up is validator-backed on 2 calibration-normal, 12
  evaluation normal-negative, and 22 evaluation buggy-positive episodes with zero cross-role
  source, pair, and episode overlap.
- Roadmap V4 is now canonical and reopens the evidence lane for a full Topic-A method-paper
  upgrade while preserving the existing anti-overclaim and locked-test rules.
- The full P7 method-paper rewrite is now complete locally, with regenerated paper tables from
  validated P2-P6 artifacts plus refreshed claim, bibliography, anonymization, and similarity
  audit docs.
- Gate 10 is closed.
- Locked test is closed.
- LeWM gameplay evaluation now includes the original non-locked TempGlitch research MVP family,
  the expanded K-A TempGlitch auxiliary support-expansion artifact, and final-intake-validated
  K-B / R5-XGame evidence. Locked test remains unopened, and WOB remains limited to audit,
  training-artifact, positive-probe, and K-C launch-readiness evidence.

## Immediate Next Task
- Run the evidence-safe paper revision pass from `CODEX_MASTER_PROMPT_LeWM_v6.md` on top of the
  completed local P7 rewrite, final-intake-validated K-B output, and the bounded K-A expanded
  intake report.
- Do not add unverified VLM AUROC numbers, broad K-A superiority language, locked-test language,
  or cross-game-generalization language during the paper pass.
- Keep all paper-facing numbers, figures, and conclusions synchronized with
  `docs/research/16_claim_registry.md`.
- Keep locked test closed and preserve the P5/P6 claim boundary: qualitative timelines are allowed,
  temporal-localization metrics are not.

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
- No broad K-A, WOB, or R5-XGame detection-performance, cross-game, action-conditioning, or
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
