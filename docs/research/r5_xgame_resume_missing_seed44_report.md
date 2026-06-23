# R5-XGame Resume Missing Seed44 Report

## Branch And Commit

- Branch: `main`
- Commit: `PENDING_LOCAL_COMMIT`

## Changed Files

- `cloud/wob_r5_xgame/run_kaggle_r5_xgame_resume_missing_seed44_and_finalize.sh`
- `scripts/run_r5_xgame_resume_missing_seed44.py`
- `scripts/run_r5_xgame_staged.py`
- `tests/test_r5_xgame_runner.py`
- `tests/test_r5_xgame_resume_missing_seed44.py`
- `tests/test_staged_install_completeness.py`
- `tests/test_validate_r5_xgame_output_bundle.py`
- `docs/research/r5_xgame_partial_output_intake_note.md`
- `docs/research/r5_xgame_resume_plan_after_quota.md`
- `docs/research/r5_xgame_resume_missing_seed44_runbook.md`
- `docs/research/r5_xgame_kaggle_live_runbook.md`
- `docs/research/r5_xgame_resume_missing_seed44_report.md`

## Partial Output Diagnosis

Verified from the downloaded partial output:

- preflight complete
- leakage audit passed
- materialize complete
- baseline scoring complete
- `train_lewm` complete for seed42, seed43, seed44
- `r5_xgame_window_manifest.csv` data rows: `362,695`
- `r5_xgame_lewm_scores_seed42.csv` data rows: `362,695`
- `r5_xgame_lewm_scores_seed43.csv` data rows: `362,695`
- `r5_xgame_lewm_scores_seed44.csv` missing
- `stage_lewm_score.json` missing
- downstream finalize stages missing

The staged log reached `lewm_score` after training and then stopped without a Python traceback,
which is consistent with a quota or wall-time interruption during scoring rather than a training
failure.

## Why A Full Rerun Is Not Needed

- The frozen window manifest is already materialized and verified.
- The baseline scores are already complete.
- All three seed training artifacts already exist, including `_lewm_seed44/best_weights.pt` and
  `_lewm_seed44/config.json`.
- Seed42 and seed43 score CSVs already match the frozen manifest row count exactly.
- The remaining work starts at seed44 scoring and then continues through deterministic downstream
  finalize stages.

## Exact Expected Partial Input Structure

The mounted Kaggle input must contain a leaf directory named `r5_xgame` under `/kaggle/input`
with:

- `stage_preflight.json`
- `stage_materialize.json`
- `stage_baseline_score.json`
- `stage_train_lewm.json`
- `r5_xgame_window_manifest.csv`
- `r5_xgame_baseline_scores.csv`
- `r5_xgame_lewm_scores_seed42.csv`
- `r5_xgame_lewm_scores_seed43.csv`
- `_lewm_seed42/`
- `_lewm_seed43/`
- `_lewm_seed44/`
- `_lewm_seed44/best_weights.pt`
- `_lewm_seed44/config.json`

The resume validator also checks that:

- `stage_train_lewm.json` status is `train_lewm_complete`
- locked-test flags remain `false`
- validation-buggy fit/select remains `false`
- seed42 and seed43 row counts match the frozen window manifest

## Exact Kaggle Command

```bash
cd /kaggle/working/glitch-world-model
bash cloud/wob_r5_xgame/run_kaggle_r5_xgame_resume_missing_seed44_and_finalize.sh
```

## Expected Runtime Estimate

Expected runtime is about `90-110 minutes` on the Kaggle GPU path.

This estimate is inferred from the local staged log spacing between the earlier `lewm_score`
seed-start messages, which was roughly `75-80 minutes` per seed before the interruption, plus
additional time for downstream finalize and packaging.

## Failure Modes

- No mounted `r5_xgame/` directory under `/kaggle/input`
- Missing `stage_train_lewm.json`
- Incomplete seed42 or seed43 score CSV row counts
- Missing `_lewm_seed44/best_weights.pt`
- Row-count mismatch after seed44 scoring
- Missing `stage_lewm_score.json` before packaging validation
- Old R5-WOB or checkpoint-looking mounted inputs

## Validation Commands And Results

Targeted lightweight validation completed locally:

```powershell
python -m pytest tests/test_r5_xgame_runner.py tests/test_r5_xgame_resume_missing_seed44.py tests/test_validate_r5_xgame_output_bundle.py tests/test_staged_install_completeness.py
```

Result:

- `45 passed`

Repository-wide lightweight validation also completed:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
pre-commit run --all-files
```

Results:

- `python -m pytest` -> `521 passed, 2 failed`
- The two failures are the pre-existing unrelated missing-doc checks in
  `tests/test_phase6e_kaggle_docs.py`
- All other listed validation commands passed

## Claim Boundary Reminder

This change adds a safe resume/finalize workflow only. It does **not** create any new R5-XGame
performance claim, and no metrics should be reported until the completed bundle passes final local
package validation.
