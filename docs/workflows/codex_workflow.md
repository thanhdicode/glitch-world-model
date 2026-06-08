# Codex Workflow

This is the operating manual for future Codex sessions in this repo.

## Start every task

1. Inspect `git status --short`.
2. Confirm the current branch.
3. Read the relevant docs and code before editing.
4. Identify whether the task is code, docs, experiment, or infrastructure.
5. Work one roadmap task at a time unless the user explicitly asks for a whole phase.

## Guardrails

- Never fabricate results.
- Never claim a dataset is downloaded before local files exist.
- Never commit generated outputs, raw data, checkpoints, `.test-tmp`, or caches.
- Preserve the CSV interfaces:
  - `manifest.csv`
  - `scores.csv`
  - labels CSV: `source,start_frame,end_frame,label`
  - `metrics.json`
- Keep scorers pluggable through `src/glitch_detection/score_clips.py`.
- Keep `lewm_latent` guarded until a specific LeWM integration task.

## After code changes

Run:

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

If formatting is the only issue and the change is low risk, run:

```powershell
python -m ruff check . --fix
python -m ruff format .
```

Then rerun lint, format check, and tests.

## After docs-only changes

- Review `git diff --stat`.
- Run lint/tests only if docs changed commands, configs, or code-adjacent instructions.
- Do not rerun all experiments unless requested.

## Before finishing

Report:

- commands run
- changed files
- test/lint result
- generated ignored files
- risks and TODOs
- next recommended task

## Commit policy

- Commit only when the user asks.
- Push only when the user asks.
- Keep commits small and scoped.
- Do not include ignored generated artifacts in commits.
