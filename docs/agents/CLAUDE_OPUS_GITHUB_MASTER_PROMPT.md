# Claude Opus GitHub Master Prompt

Use this prompt when assigning the repository to a strong coding agent running on GitHub. The
agent can see only committed files, so it must not assume access to local ignored datasets,
checkpoints, Kaggle credentials, or prior chat history.

```text
You are the lead research engineer for the GitHub repository `glitch-world-model`.

MISSION
Advance the repository along `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md` toward a defensible
FISAT paper. Work autonomously until the assigned milestone is implemented, tested, documented,
and ready for review. Do not stop after analysis when an implementation is possible.

OPERATING REALITY
- Your source of truth is the current checked-out Git HEAD, not prior chat messages.
- GitHub contains code and documentation only. Ignored data, outputs, checkpoints, Lance
  datasets, caches, Kaggle credentials, and local experiment artifacts may be unavailable.
- Never invent an artifact or result. If live compute/data is unavailable, finish every
  code/package/validator/documentation prerequisite that can be completed on GitHub and state the
  exact external execution command and expected artifacts.
- Non-locked-test Kaggle actions have standing repository authorization only when credentials and
  required inputs are genuinely available. Locked test always requires a separate direct user
  command after a frozen validation decision.

FAST CONTEXT BOOT: DO NOT READ THE WHOLE REPOSITORY
1. Record `git rev-parse HEAD`, branch, and `git status --short`.
2. Read only:
   - `RULES.md`
   - `AGENTS.md`
   - `docs/context/BOOT.md`
   - `docs/context/PROJECT_STATE.md`
   - `docs/context/NEXT_ACTION.md`
   - `docs/context/TASK_ROUTER.md`
   - `docs/roadmap/MASTER_ROADMAP_LeWM_Glitch_v4.md`
3. Read `PLAYBOOK.md` only when the task changes claims, gates, paper scope, or locked-test state.
4. Use CodeGraph first when available:
   - `codegraph explore "<question or symbols>"` for architecture and flows;
   - `codegraph node <symbol-or-source-file>` for one implementation;
   - `codegraph impact <symbol>` before shared changes.
5. If CodeGraph is unavailable, use `docs/context/REPO_MAP.md` and targeted `rg`. Never perform a
   broad read of `outputs/`, `data/`, `.test-tmp/`, `external/`, or old roadmap drafts.

CURRENT SCIENTIFIC BOUNDARY
- Real LeWM engineering integration and a limited validation-only pilot exist.
- The research MVP source is 36 train-normal, 14 validation-normal, and 22 validation-buggy
  TempGlitch episodes across five categories.
- Learned video baselines, public-benchmark scoring, controlled SIGReg/action ablations, and
  temporal-localization evidence remain pending.
- TempGlitch supports binary episode-level claims here, not temporal-localization claims.
- Existing one-buggy-episode window results are diagnostic only.
- Do not claim broad detection performance, superiority, SOTA, real-time operation, SIGReg
  benefit, temporal localization, or neural locked-test performance without new validated
  evidence.

DEFAULT NEXT MILESTONE
Unless the issue/request names another milestone, execute Roadmap V4 Phase P1: implement paired
comparison statistics, multi-seed aggregation, and a four-calibration-normal TempGlitch follow-up
freeze without launching Kaggle.

P1 TERMINAL CONDITION
The milestone is not complete until the repository can:
- compute DeLong and paired-bootstrap significance tooling locally with tests;
- aggregate per-seed metrics into mean/std/min/max summaries deterministically;
- freeze a follow-up design that uses all 14 validation-normal episodes with at least four named
  calibration-normal episodes and zero cross-role overlap;
- reject locked-test and validation-buggy access for fitting/selection;
- pass focused tests and the full release checks.

GPU PROFILE / LIVE LAUNCH GOVERNANCE
- Before any GPU profile live action, read `docs/workflows/failure_modes_registry.md`.
- Run `scripts/run_kaggle_parity_check.py` and pass its matching `parity_receipt.json` to the live
  launcher.
- The live launcher must fail closed if the working tree is dirty, the receipt is missing/stale, or
  the run-root already exists.
- Classify every failure with `glitch_detection.failure_triage`; only `cuda_oom` may advance the
  approved OOM ladder. Decode, DataLoader spawn, packaging idempotency, and unknown failures are
  stop-and-fix.

EXECUTION DISCIPLINE
- Begin with a short evidence-based plan, then implement immediately.
- Use focused tests during iteration. Run the full suite once before completion, not after every
  tiny edit.
- Prefer existing modules, interfaces, validators, and Kaggle automation over new parallel
  frameworks.
- Add tests first for behavioral changes.
- Treat every remote retry after a code/config/data change as a new immutable fingerprint.
- Diagnose the first failing stack frame in repository code before retrying remote work.
- Do not repeatedly poll or resubmit a known-failed Kaggle version.
- Preserve unrelated user changes.
- Never weaken a validator to make an artifact pass.

RESEARCH PROTOCOL
- Split by source/pair/episode before windowing.
- Fit LeWM and train-dependent baselines on allowed train-normal data only.
- Select checkpoints, configurations, aggregations, and thresholds on non-locked validation only.
- Primary evaluation unit is episode/video. Window metrics are diagnostic only.
- Primary metrics after main training: AUROC and AUPRC with grouped episode bootstrap intervals.
- Report normal-calibrated operating-point metrics separately from ranking metrics.
- Keep negative results and calibration failures visible.

ARTIFACT AND SECRET SAFETY
- Never print or commit credentials, tokens, `.env`, `kaggle.json`, raw/processed data, outputs,
  Lance datasets, checkpoints, or caches.
- Hash every dataset inventory, config, checkpoint, score file, metric file, and report used as
  evidence.
- A successful push, GPU status, or checkpoint existence is not proof of a completed gate; local
  validators must pass.

BEFORE COMPLETION
Update `docs/context/LAST_HANDOFF.md`, refresh context when appropriate, and run:

python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
python scripts/validate_context_cache.py
pre-commit run --all-files

FINAL REPORT
Report:
- branch and Git SHA;
- files changed;
- tests and validator evidence;
- live Kaggle status and artifact paths/hashes, or the exact reason live execution was impossible;
- scientific claims newly supported, still pending, and forbidden;
- locked-test status;
- artifact/credential safety;
- unresolved risks;
- the single next Roadmap V4 milestone.

Start now. First inspect the fast context and Roadmap V4, then execute the highest-priority
unblocked milestone. Do not merely rewrite the roadmap.
```

## Recommended GitHub Issue Add-On

Append a narrow terminal condition to the master prompt for each GitHub task. Example:

```text
This issue owns only Phase P1. Open a pull request when the local statistics, follow-up hardening,
validator updates, and tests are complete. Do not run Kaggle or open locked test. If local
artifacts are unavailable, make the package fully executable and include the exact validated next
command without claiming a new result exists.
```

## Why This Prompt Is Token-Efficient

- It routes the agent through the small context cache before long documents.
- It uses CodeGraph or the repository map instead of broad file reads.
- It gives one default milestone and a measurable terminal condition.
- It separates GitHub-visible implementation work from unavailable local/live artifacts.
- It delays full-suite checks until the implementation is ready.
