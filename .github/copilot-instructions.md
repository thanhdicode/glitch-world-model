# Repository Instructions

Read and follow `AGENTS.md`, `RULES.md`, and `CONVENTIONS.md`. Consult `PLAYBOOK.md` for the
full roadmap, evidence map, role playbooks, and current next actions.

- For long-horizon research execution, follow
  `docs/agents/CLAUDE_OPUS_GITHUB_MASTER_PROMPT.md` and
  `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v3.md`.
- Start with the fast context cache and use CodeGraph or `docs/context/REPO_MAP.md` plus targeted
  searches. Do not broadly read the repository.
- Preserve the CSV/JSON interfaces and keep heavy ML dependencies optional.
- Use tests first for behavioral changes and make narrowly scoped edits.
- Keep the claim registry synchronized with paper-facing wording.
- Do not claim LeWM gameplay performance, superiority, SOTA, temporal localization, or neural
  locked-test results from current engineering/smoke evidence.
- Non-locked Kaggle live work follows repository standing authorization when credentials and
  inputs are available. Never score or materialize locked test without a separate direct user
  command.
- Never commit or print data, outputs, checkpoints, Lance datasets, credentials, or tokens.

Before completion run:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
```
