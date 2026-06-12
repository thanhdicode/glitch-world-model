# TASK_ROUTER.md

| Task type | Read first | Then inspect | Do not open by default |
|---|---|---|---|
| Gate 5 Kaggle | `BOOT.md`, `PROJECT_STATE.md`, `NEXT_ACTION.md`, `docs/workflows/kaggle_automation_policy.md` | `src/glitch_detection/lewm_kaggle.py`, `src/glitch_detection/lewm_training.py`, `scripts/prepare_lewm_kaggle_package.py`, `scripts/validate_lewm_kaggle_artifacts.py`, `tests/test_lewm_kaggle.py` | `paper/`, old roadmap drafts, `outputs/` |
| Context cache | `BOOT.md`, `CONTEXT_POLICY.md`, this file | `scripts/update_context_cache.py`, `scripts/validate_context_cache.py`, `tests/test_context_cache.py`, `scripts/doctor.py`, `scripts/validate_research_release.py` | `outputs/`, `data/`, `external/` |
| Paper writing | `BOOT.md`, claim registry, `PLAYBOOK.md` paper sections | `paper/`, `docs/research/`, `docs/workflows/paper_claim_rules.md` | `outputs/`, raw data |
| Dataset protocol | `BOOT.md`, `docs/research/40_gate3_gate4_real_dataset_protocol.md` | `src/glitch_detection/lewm_data.py`, protocol modules, related tests | `paper/`, Kaggle packages |
| Locked test | `BOOT.md`, `docs/workflows/locked_test_release.md`, `RULES.md` | locked-test gate scripts and selected decision artifacts | never materialize or score without explicit approval |
| Baseline/scorer code | `BOOT.md`, `REPO_MAP.md` | `src/glitch_detection/score_clips.py`, scorer module, matching tests | `PLAYBOOK.md` unless claims/gates change |
| Release/CI hygiene | `BOOT.md`, `CONTEXT_POLICY.md` | `scripts/validate_research_release.py`, `scripts/doctor.py`, `.pre-commit-config.yaml`, release tests | experiment outputs |
