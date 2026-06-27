from __future__ import annotations

import argparse
import ast
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_DIR = Path("docs/context")
REQUIRED_CONTEXT_FILES = (
    "BOOT.md",
    "PROJECT_STATE.md",
    "NEXT_ACTION.md",
    "LAST_HANDOFF.md",
    "REPO_MAP.md",
    "TASK_ROUTER.md",
    "CONTEXT_POLICY.md",
    "README.md",
)
IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".test-tmp",
    ".venv",
    "__pycache__",
    "checkpoints",
    "data",
    "dist",
    "external",
    "outputs",
}
TEXT_CREDENTIAL_PATTERNS = (
    "kaggle.json",
    "access_token",
    "api_key",
    "private_key",
    "id_rsa",
    "id_ed25519",
)


class CacheMetadata(NamedTuple):
    generated_at: str
    commit: str


def git_sha(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return completed.stdout.strip()


def metadata(root: Path) -> CacheMetadata:
    return CacheMetadata(
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        commit=git_sha(root),
    )


def read_optional(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8-sig")


def has_gate5_conflict_record(root: Path) -> bool:
    return (root / "docs/research/43_gate5_kaggle_cuda_smoke_results.md").is_file()


def build_boot(meta: CacheMetadata) -> str:
    return f"""# BOOT.md - Fast Start Context For Agents

Generated: {meta.generated_at}
Commit: `{meta.commit}`

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
- Execute roadmap V4 Phase P7. The P6 demo lane is now present, so the next work is the full
  paper rewrite and submission packaging on top of the validated bounded evidence.
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
"""


def build_project_state(meta: CacheMetadata, root: Path) -> str:
    return f"""# PROJECT_STATE.md

Last updated: {meta.generated_at}
Commit: `{meta.commit}`
Generated by: `scripts/update_context_cache.py`

| Gate | Status | Evidence | Missing | Next action |
|---|---|---|---|---|
| 1 | passed | baseline pipeline, tests, release tooling | none | maintain |
| 2 | passed | strict LeWM checkpoint/runtime smoke | gameplay use | maintain |
| 3 | passed | frozen TempGlitch/WOB protocols | full official action/pair certainty | maintain |
| 4 | passed | reduced real Lance loader proof | full-scale materialization | maintain |
| 5 | passed | strict v6 Kaggle CUDA/resume artifact validation | none | maintain |
| 6 | passed | v8 Kaggle CUDA normal-only training; strict reload/encoding validator passed | detection metrics | maintain frozen checkpoint |
| 7 | passed | 10,081 real frozen-checkpoint LeWM window scores on a canonical non-locked Lance manifest | broader buggy validation coverage | preserve artifacts |
| 8 | passed | frame-difference and train-normal-fitted feature-distance scores on the identical manifest | broader comparison scope | preserve artifacts |
| 9 | passed pilot | AUROC/AUPRC plus grouped-normal-P95 F1 for six LeWM aggregations and two baselines | robust multi-episode evidence and working LeWM threshold calibration | report limitations |
| 10 | closed | no locked-test materialization or scoring | frozen decision and separate direct user command | keep closed |

## Current Safe Claims
- Checkpoint-level LeWM integration feasibility.
- Reduced real-data conversion and loader compatibility.
- Local CPU forward/backward/resume smoke evidence.
- Gate 5 Kaggle CUDA smoke/resume artifact validation passed.
- Gate 6 normal-only source audit and Lance loader evidence.
- Gate 6 bounded normal-only gameplay training engineering on Kaggle CUDA.
- Frozen Gate 6 LeWM scores and named baselines were evaluated on one identical non-locked Lance
  window manifest.
- A broader non-locked research MVP source is audited and Lance-materialized for 36/14/22
  train-normal/validation-normal/validation-buggy episodes.
- A non-locked research-MVP LeWM GPU profile completed exactly 500 CUDA optimizer updates at batch
  size 8 with AMP, strict checkpoint reload validation, artifact hashing, and eight
  validation-normal pipeline-verification batches.
- R4 rerun seed43/44 training artifacts are local SHA256-verified and pass per-seed artifact
  validators.
- R5 completed a provenance-bound non-locked TempGlitch identical-episode evaluation on one frozen
  30,549-window manifest spanning two calibration-normal and 34 evaluation episodes.
- Within the frozen R5 family, the highest observed AUROC and AUPRC rows came from LeWM seed44
  mean-aggregated L2 variants, while the best baseline AUROC/AUPRC rows came from
  `feature_distance`; all such comparisons remain limited to this non-locked evaluation family.
- WOB-P1 seed42 produced a SHA256-verified, validator-passed training artifact under the
  train-normal / validation-normal protocol, with validation-buggy rows excluded from fit/selection
  and locked test unmaterialized and unscored.
- WOB-P1 seed43 produced a SHA256-verified, validator-passed training artifact under the
  train-normal / validation-normal protocol, with validation-buggy rows excluded from fit/selection,
  `action_dim=4`, no WOB evaluation run, and locked test unmaterialized and unscored.
- WOB-P1 seed44 produced a SHA256-verified, validator-passed training artifact under the
  train-normal / validation-normal protocol, with validation-buggy rows excluded from fit/selection,
  `action_dim=4`, no WOB evaluation run, and locked test unmaterialized and unscored.
- The seed42 non-locked WOB evaluation-readiness gate is frozen as metadata only: a 72-row
  validation manifest (12 normal calibration + 60 buggy evaluation, all 59 locked rows excluded),
  recorded artifact hashes, frozen reporting paths, and a frozen claim boundary, with no WOB
  evaluation run.
- The repository now provides a generalized WOB seed artifact validator plus robust Kaggle
  training runners for WOB seeds43/44 under the same real-action, train-normal-only, locked-test-
  closed protocol.
- `R5-WOB` completed as a provenance-bound positive-probe bundle demonstrating pipeline execution
  and class-conditional signal presence under a normal-calibrated threshold.
- The repository provides a staged R5-XGame Kaggle runner and output validator that materialize
  only the frozen 120 non-locked rows, train fresh seed42/43/44 artifacts on the 36
  train-normal rows, calibrate on the 12 calibration-normal rows, evaluate the 12/60 held-out
  binary set, package outputs, and require false locked-test flags.
- `R5-XGame` compute completed without locked-test materialization, and the downloaded live
  output directory plus repaired tarball/sidecar now pass local intake validation with statuses
  `r5_xgame_output_validated` and `r5_xgame_tarball_validated`.
- `R5-XGame` now provides bounded non-locked binary validation evidence that latent surprise
  scores separate buggy-positive and normal-negative gameplay episodes on the frozen split, with
  the best recorded configuration reaching AUROC `0.909722` and AUPRC `0.981384`.
- The repaired `R5-XGame` tarball SHA256 is
  `65f8b21bf9b31dd6498cb2b46ca0d368f7d4b1f8fef15480b915a1ff9a8204ac`; this was a
  packaging/intake fix only and did not relaunch Kaggle or retrain LeWM.
- The TempGlitch pair-disjoint follow-up is validator-backed on the same 12-normal-negative /
  22-buggy-positive evaluation support for every row, with the best recorded LeWM AUROC `0.7159`
  and best recorded baseline AUROC `0.6136`; the AUROC intervals overlap and best LeWM
  FPR@95TPR is `0.7500`.
- The repository now provides three learned video baseline code paths for the frozen follow-up
  support: Conv3D autoencoder, CNN-LSTM next-frame prediction, and VideoMAE-small feature-
  distance, plus a unified Kaggle runner/validator that preserves train-normal-only fit, zero
  leakage, and false locked-test flags.

## Current Unsafe Claims
- LeWM detects gameplay glitches.
- LeWM beats baselines or is state of the art.
- SIGReg helps glitch detection.
- Temporal localization performance.
- LeWM gameplay glitch-detection performance.
- WOB detection performance or cross-game generalization.
- Broad R5-XGame detection-performance, cross-game generalization, or final-benchmark claims
  beyond the frozen non-locked split.
- WOB action-conditioning benefit.
- Neural locked-test result.

## Current Blocker
- Topic A remains method-paper-incomplete because the repo still needs the P7 full paper rewrite
  and submission packaging on top of the current bounded evidence.
- `R5-WOB` is complete, but it remains a positive-probe bundle rather than a valid binary
  benchmark because it has zero normal-negative evaluation episodes.
- K3 is intake-validated as an honest negative mechanistic readout; it does not support
  SIGReg-benefit or action-conditioning-benefit language.
- P5 confirms that temporal localization remains future work until a validated artifact exposes
  real span labels.
- P6 is now a reproducibility/demo lane only; it does not widen the scientific claim surface.
- Locked test remains closed.

## 2026-06-17 R4 Rerun Verification

| Item | Status | Evidence | Required hash / value | Boundary |
|---|---|---|---|---|
| FIX-0 GPU capability guard | DONE | `gpu_compute_capability` failure bucket and `sm_70+` guards are present on `main` | commit `614a6ef` | Infrastructure guard only. |
| R3 seed42 | LOCAL_EXTRACT_PRESENT / ARCHIVE_PROVENANCE_SEPARATE | Prior local extracted artifact root exists, but this task did not recover a fresh seed42 tarball | `a51fa19517b69cadcd96273e37094fed50bd14440d854ce0dac521b78a580d48` | Separate from this R4 rerun confirmation. |
| R4 seed43 | ARTIFACT_BACKED_RERUN | Local SHA256 matches downloaded `.sha256`; per-seed validator passed | `3ec2fa25b2b2b952bcd1087aeb755c2b0c413fa95b9ec9a71a320f5df9dd33f7`; seed 43; 3000/15000 updates; early-stopped at best update 500; best validation loss `0.615883181833121` | Training-gate evidence only. |
| R4 seed44 | ARTIFACT_BACKED_RERUN | Local SHA256 matches downloaded `.sha256`; per-seed validator passed | `ffd6d917f134f3cce37cd0a1e666b10ab1122678d9c3f483936f9b1ad69efa83`; seed 44; 8000/15000 updates; early-stopped at best update 5500; best validation loss `0.6347979751979919` | Training-gate evidence only. |
| R4 bundle | ARTIFACT_BACKED_RERUN | Local SHA256 matches downloaded `.sha256` | `4d4575679a91ab54ae58005bae6a483bdf63e06750336400f3448873ee0afd01` | Bundle integrity only. |
| R5 | COMPLETED_NONLOCKED | `outputs/r5_tempglitch_identical_episode/` contains frozen manifest, raw scores, episode scores, comparison, metrics, provenance, and report hashes | broader benchmark generalization and locked test remain out of scope | preserve hashes and update claims conservatively |
| WOB expansion | LOCAL_WOB_P0_STATUS=BLOCKED_MISSING_INPUTS; WOB_P0_KAGGLE_STATUS=PASSED; WOB_STATUS=R5_WOB_VALIDATED_POSITIVE_PROBE; WOB_P1_TRAINING_STATUS=SEED44_VALIDATED; WOB_EVALUATION_STATUS=R5_XGAME_INTAKE_VALIDATED | verified WOB-P0 bundle confirms 120/120 non-locked rows resolved and 59 locked rows skipped; verified WOB-P1 seed42/seed43/seed44 bundles confirm train-normal/validation-normal training artifacts with false locked-test flags; R5-WOB is positive-probe only; R5-XGame intake and bounded R6 docs are complete | use only as a separate bounded secondary paper result | No binary-benchmark claim for R5-WOB, no broad R5-XGame/WOB generalization or action-conditioning claim, and no locked-test claim. |
| Locked test | UNTOUCHED / NOT_MATERIALIZED / NOT_SCORED | Per-seed validators and metadata keep false flags | false flags required | Separate direct user command still required. |

## Current Phase

- Current phase: Roadmap V4 is active and the repository is upgrading from a bounded evaluation
  note into a full Topic-A method-paper lane.
- Next phase on this branch: Phase P7 full paper rewrite.
- Later phases: bounded submission packaging decisions only.
- Locked-test access remains closed and requires a separate explicit human command after R7
  recommends it.

## Current Branch Policy
- Routine safe code/docs may be committed and pushed to `main` after all checks pass.
- Non-locked-test Kaggle actions use standing authorization. Remote deletion and validator bypass
  remain prohibited; locked-test access still requires a separate direct user command.
"""


def build_next_action(meta: CacheMetadata) -> str:
    return f"""# NEXT_ACTION.md

Last updated: {meta.generated_at}
Commit: `{meta.commit}`

## Current Priority
Advance to roadmap V4 Phase P7. The P6 demo lane is now implemented, so the next work is the full
paper rewrite and submission package preparation under the existing bounded claim surface.
Authority roadmap: `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`.

## Next Gate (Phase P7, local)
1. Regenerate paper tables from the validated P2-P6 artifacts.
2. Rewrite the paper sections so every empirical paragraph stays mapped to
   `docs/research/16_claim_registry.md`.
3. Keep the P5/P6 boundary explicit: qualitative timelines are allowed, temporal-localization
   metrics are not.
4. Preserve the closed locked-test state and keep all output artifacts outside Git.

## Success Criteria
- Demo outputs are reproducible from already validated non-locked artifacts.
- The claim registry, paper text, and context cache remain consistent with the bounded evidence.
- No temporal-localization metric, onset/offset claim, or locked-test action is introduced.
- Locked test remains closed and the repository verification suite stays green.

## Phase Sequence After P7
Bounded submission packaging decisions, venue checklist completion, and user-operated submission.

## Current Known Blocker
No local blocker remains for P6. The current limitation is scientific rather than operational:
temporal-localization claims remain unavailable until a validated artifact supplies real span
annotations, and the paper rewrite must stay inside the current bounded evidence. Locked test
remains closed.
"""


def build_last_handoff_template(meta: CacheMetadata) -> str:
    return f"""# LAST_HANDOFF.md

Last completed task: Phase P2 learned-baseline local preparation
Commit: `{meta.commit}`
Date: {meta.generated_at}

## What Changed
- Added `src/glitch_detection/cnn_lstm.py` with an optional CNN-LSTM next-frame baseline that
  mirrors the video autoencoder train/score interface.
- Added `src/glitch_detection/video_transformer.py` with an optional VideoMAE-small
  feature-distance baseline and checkpointed train/score flow.
- Registered the new learned baselines in `src/glitch_detection/score_clips.py`.
- Added `scripts/run_kaggle_learned_baselines.py` and
  `scripts/validate_learned_baselines.py` for the shared K1 train/score/validate path.
- Added CPU-mock coverage for the new baselines and the unified runner.

## Checks Passed
- `python -m pytest`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python scripts/validate_research_release.py --ci`
- `python scripts/check_claim_registry.py`
- `python scripts/doctor.py`
- `python scripts/validate_context_cache.py`

## Safety Status
- No Kaggle launch, retraining run, or downloaded evidence claim was performed in this task.
- New paper-facing learned-baseline claims stay blocked until K1 artifacts are validated.
- No locked-test access.
- No data/output/checkpoint/cache/credential commit intended.

## Gate Status After Task
- Gates 1-8 passed; Gate 9 remains a bounded pilot and R5 follow-up evidence remains bounded.
- Gate 10 remains closed.
- Phase P2 local preparation is complete; K1 is the next external gate.
- Locked test remains closed.

## Open Blockers
- K1 still requires a user-operated Kaggle run plus local validator-backed artifact intake.
- Phase P3-P5 evidence is still missing: public benchmark scoring, controlled ablations, and
  temporal-localization scope/results.
- Official-kit compile remains a later P7 packaging blocker.

## Next Recommended Task
- Run Kaggle gate K1 with the frozen follow-up manifest/split and the new learned-baseline
  runner, then validate the downloaded artifact directory locally.

## Files Likely Relevant Next
- `src/glitch_detection/video_autoencoder.py`
- `src/glitch_detection/cnn_lstm.py`
- `src/glitch_detection/video_transformer.py`
- `scripts/run_kaggle_learned_baselines.py`
- `scripts/validate_learned_baselines.py`
- `tests/test_cnn_lstm.py`
- `tests/test_video_transformer.py`
- `tests/test_learned_baselines_runner.py`
"""


def build_context_readme(meta: CacheMetadata) -> str:
    return f"""# Context Cache

Generated: {meta.generated_at}
Commit: `{meta.commit}`

This directory is the fast-start layer for coding agents. It keeps routine tasks from re-reading
the full repository and long playbook unless the task truly needs deep context.

## Files

- `BOOT.md`: first compact boot context.
- `PROJECT_STATE.md`: current gate and claim status.
- `NEXT_ACTION.md`: exactly one priority task.
- `LAST_HANDOFF.md`: latest completed-task handoff.
- `REPO_MAP.md`: generated repository and symbol map.
- `TASK_ROUTER.md`: task type to files-to-read map.
- `CONTEXT_POLICY.md`: maintenance and token-budget rules.

Regenerate with:

```powershell
python scripts/update_context_cache.py --refresh-boot
python scripts/validate_context_cache.py
```
"""


def build_context_policy() -> str:
    return """# CONTEXT_POLICY.md

## Default Rule

Do not read the whole repo for routine tasks. Start with the fast context files, then follow
`TASK_ROUTER.md` and targeted `rg` searches.

## PLAYBOOK.md

`PLAYBOOK.md` is the long-form operating bible. Open it for roadmap, paper, claim, gate-status,
safety ambiguity, or stale-cache resolution. Do not auto-load it for every small code edit.
Use `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md` as the current execution roadmap.

## Cache Maintenance

- Update `LAST_HANDOFF.md` at the end of each task.
- Run `python scripts/update_context_cache.py --refresh-boot` before final verification.
- Run `python scripts/validate_context_cache.py` before commit.
- If generated context conflicts with checked artifacts, trust the artifact and refresh context.

## Safety Visibility

Safety rules must remain visible in `BOOT.md`; reducing token use must not hide Kaggle,
locked-test, artifact, credential, or claim restrictions.

## Token Budget Target

Keep `BOOT.md` under 200 lines. Use `REPO_MAP.md` and `TASK_ROUTER.md` to select files rather
than reading broad directories.
"""


def build_task_router() -> str:
    return """# TASK_ROUTER.md

| Task type | Read first | Then inspect | Do not open by default |
|---|---|---|---|
| GPU live launch / profile | `BOOT.md`, `NEXT_ACTION.md`, `docs/workflows/failure_modes_registry.md`, `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`, profile plan/spec | `scripts/run_kaggle_parity_check.py`, `scripts/run_lewm_gpu_profile_automation.py`, `src/glitch_detection/failure_triage.py`, Kaggle package/validator modules, focused tests | locked test, old roadmap drafts, unrelated outputs |
| GPU profile / main training | `BOOT.md`, `NEXT_ACTION.md`, `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`, profile plan/spec | `src/glitch_detection/lewm_training.py`, Kaggle package/validator modules, focused tests | locked test, old roadmap drafts, unrelated outputs |
| Gate 5 Kaggle | `BOOT.md`, `PROJECT_STATE.md`, `NEXT_ACTION.md`, `docs/workflows/kaggle_automation_policy.md` | `src/glitch_detection/lewm_kaggle.py`, `src/glitch_detection/lewm_training.py`, `scripts/prepare_lewm_kaggle_package.py`, `scripts/validate_lewm_kaggle_artifacts.py`, `tests/test_lewm_kaggle.py` | `paper/`, old roadmap drafts, `outputs/` |
| Roadmap / long-horizon agent | `BOOT.md`, `PROJECT_STATE.md`, `NEXT_ACTION.md`, `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md` | `PLAYBOOK.md`, claim registry, relevant gate reports | old roadmap drafts, outputs, raw data |
| Context cache | `BOOT.md`, `CONTEXT_POLICY.md`, this file | `scripts/update_context_cache.py`, `scripts/validate_context_cache.py`, `tests/test_context_cache.py`, `scripts/doctor.py`, `scripts/validate_research_release.py` | `outputs/`, `data/`, `external/` |
| Paper writing | `BOOT.md`, claim registry, `PLAYBOOK.md` paper sections | `paper/`, `docs/research/`, `docs/workflows/paper_claim_rules.md` | `outputs/`, raw data |
| Dataset protocol | `BOOT.md`, `docs/research/40_gate3_gate4_real_dataset_protocol.md` | `src/glitch_detection/lewm_data.py`, protocol modules, related tests | `paper/`, Kaggle packages |
| Locked test | `BOOT.md`, `docs/workflows/locked_test_release.md`, `RULES.md` | locked-test gate scripts and selected decision artifacts | never materialize or score without explicit approval |
| Baseline/scorer code | `BOOT.md`, `REPO_MAP.md` | `src/glitch_detection/score_clips.py`, scorer module, matching tests | `PLAYBOOK.md` unless claims/gates change |
| Release/CI hygiene | `BOOT.md`, `CONTEXT_POLICY.md` | `scripts/validate_research_release.py`, `scripts/doctor.py`, `.pre-commit-config.yaml`, release tests | experiment outputs |
"""


def path_allowed(path: Path) -> bool:
    return not any(part in IGNORED_PARTS for part in path.parts)


def python_symbols(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            names.append(node.name)
    return names[:12]


def first_doc_line(path: Path) -> str:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except (SyntaxError, UnicodeDecodeError):
        return ""
    docstring = ast.get_docstring(tree) or ""
    return docstring.splitlines()[0] if docstring else ""


def tracked_files(root: Path) -> list[Path]:
    try:
        completed = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return [path.relative_to(root) for path in root.rglob("*") if path.is_file()]
    return [Path(line) for line in completed.stdout.splitlines() if line.strip()]


def build_repo_map(meta: CacheMetadata, root: Path) -> str:
    files = [path for path in tracked_files(root) if path_allowed(path)]
    top_level = sorted({path.parts[0] for path in files if path.parts})
    python_files = [
        path
        for path in files
        if path.suffix == ".py" and path.parts and path.parts[0] in {"src", "scripts", "tests"}
    ]
    docs = [
        path
        for path in files
        if path.suffix.lower() == ".md" and path.parts and path.parts[0] in {"docs", "paper"}
    ][:80]
    lines = [
        "# REPO_MAP.md",
        "",
        f"Generated: {meta.generated_at}",
        f"Commit: `{meta.commit}`",
        "Generator: `scripts/update_context_cache.py`",
        "",
        "## Top-Level Map",
        "| Path | Purpose |",
        "|---|---|",
    ]
    purpose = {
        "src": "Reusable pipeline and model integration code.",
        "scripts": "Auditable command-line entry points.",
        "tests": "Fast default-environment tests.",
        "docs": "Research evidence, workflows, context cache, and roadmap.",
        "configs": "Experiment and runtime configuration.",
        "kaggle": "Validation-only launch packages.",
        "paper": "Cautious manuscript scaffold and generated tables.",
        "requirements": "Optional runtime requirement pins.",
    }
    for name in top_level:
        if name.startswith("."):
            continue
        lines.append(f"| `{name}/` | {purpose.get(name, 'Tracked repository path.')} |")
    lines.extend(["", "## Python Modules", "| File | Symbols | Purpose |", "|---|---|---|"])
    for path in python_files:
        if path.parts[0] == "scripts" or path.parts[0] == "src":
            symbols = ", ".join(python_symbols(root / path)) or "-"
            doc = first_doc_line(root / path) or "Python module."
            lines.append(f"| `{path.as_posix()}` | {symbols} | {doc} |")
    lines.extend(["", "## Scripts", "| Script | Purpose | Related gate |", "|---|---|---|"])
    for path in sorted(path for path in files if path.parts[:1] == ("scripts",))[:80]:
        if path.suffix == ".py":
            doc = first_doc_line(root / path) or "CLI/helper script."
            gate = "Gate 5" if "lewm" in path.name or "kaggle" in path.name else "general"
            lines.append(f"| `{path.as_posix()}` | {doc} | {gate} |")
    lines.extend(["", "## Tests", "| Test | Coverage |", "|---|---|"])
    for path in sorted(path for path in files if path.parts[:1] == ("tests",))[:120]:
        if path.suffix == ".py":
            lines.append(f"| `{path.as_posix()}` | {path.stem.removeprefix('test_')} |")
    lines.extend(["", "## Docs", "| Doc | Purpose |", "|---|---|"])
    for path in docs:
        lines.append(f"| `{path.as_posix()}` | {path.stem.replace('_', ' ')} |")
    lines.append("")
    return "\n".join(lines)


def expected_files(root: Path, *, refresh_boot: bool) -> dict[str, str]:
    meta = metadata(root)
    return {
        "PROJECT_STATE.md": build_project_state(meta, root),
        "NEXT_ACTION.md": build_next_action(meta),
        "REPO_MAP.md": build_repo_map(meta, root),
        "TASK_ROUTER.md": build_task_router(),
        "CONTEXT_POLICY.md": build_context_policy(),
        "README.md": build_context_readme(meta),
        **({"BOOT.md": build_boot(meta)} if refresh_boot else {}),
    }


def write_if_changed(path: Path, content: str) -> bool:
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def update_context_cache(root: Path, *, refresh_boot: bool = False) -> list[Path]:
    context_dir = root / CONTEXT_DIR
    context_dir.mkdir(parents=True, exist_ok=True)
    changed: list[Path] = []
    for name, content in expected_files(root, refresh_boot=refresh_boot).items():
        path = context_dir / name
        if write_if_changed(path, content):
            changed.append(path)
    boot = context_dir / "BOOT.md"
    if not boot.is_file():
        if write_if_changed(boot, build_boot(metadata(root))):
            changed.append(boot)
    handoff = context_dir / "LAST_HANDOFF.md"
    if not handoff.is_file():
        if write_if_changed(handoff, build_last_handoff_template(metadata(root))):
            changed.append(handoff)
    return changed


def context_validation_errors(root: Path) -> list[str]:
    context_dir = root / CONTEXT_DIR
    errors: list[str] = []
    for name in REQUIRED_CONTEXT_FILES:
        if not (context_dir / name).is_file():
            errors.append(f"missing context file: {(CONTEXT_DIR / name).as_posix()}")
    if errors:
        return errors

    boot_lines = (context_dir / "BOOT.md").read_text(encoding="utf-8-sig").splitlines()
    if len(boot_lines) > 200:
        errors.append(f"BOOT.md exceeds 200 lines: {len(boot_lines)}")

    project_state = (context_dir / "PROJECT_STATE.md").read_text(encoding="utf-8-sig")
    if "| Gate | Status | Evidence | Missing | Next action |" not in project_state:
        errors.append("PROJECT_STATE.md missing gate table")
    if "| 5 | passed |" not in project_state:
        errors.append("PROJECT_STATE.md must record Gate 5 passed")

    next_action = (context_dir / "NEXT_ACTION.md").read_text(encoding="utf-8-sig")
    if next_action.count("## Current Priority") != 1:
        errors.append("NEXT_ACTION.md must contain exactly one Current Priority section")

    handoff = (context_dir / "LAST_HANDOFF.md").read_text(encoding="utf-8-sig")
    for heading in (
        "Last completed task:",
        "Commit:",
        "Date:",
        "## What Changed",
        "## Checks Passed",
        "## Safety Status",
        "## Gate Status After Task",
        "## Open Blockers",
        "## Next Recommended Task",
        "## Files Likely Relevant Next",
    ):
        if heading not in handoff:
            errors.append(f"LAST_HANDOFF.md missing heading: {heading}")

    repo_map = (context_dir / "REPO_MAP.md").read_text(encoding="utf-8-sig")
    for heading in ("## Python Modules", "## Scripts", "## Tests"):
        if heading not in repo_map:
            errors.append(f"REPO_MAP.md missing section: {heading}")

    task_router = (context_dir / "TASK_ROUTER.md").read_text(encoding="utf-8-sig")
    if "Gate 5 Kaggle" not in task_router:
        errors.append("TASK_ROUTER.md missing Gate 5 row")

    for path in REQUIRED_CONTEXT_FILES:
        text = (context_dir / path).read_text(encoding="utf-8-sig").lower()
        if any(pattern in text for pattern in TEXT_CREDENTIAL_PATTERNS):
            if path in {"BOOT.md", "CONTEXT_POLICY.md"} and "kaggle.json" in text:
                continue
            errors.append(f"{path} contains credential-looking text")
        if "outputs/" in text and path in {"LAST_HANDOFF.md", "REPO_MAP.md"}:
            errors.append(f"{path} references forbidden output paths as context")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate or validate fast agent context cache.")
    parser.add_argument("--refresh-boot", action="store_true", help="Regenerate BOOT.md.")
    parser.add_argument("--check", action="store_true", help="Validate without modifying files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.check:
        changed = update_context_cache(ROOT, refresh_boot=args.refresh_boot)
        if changed:
            for path in changed:
                print(f"updated: {path.relative_to(ROOT).as_posix()}")
        else:
            print("Context cache already current.")
    errors = context_validation_errors(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Context cache validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
