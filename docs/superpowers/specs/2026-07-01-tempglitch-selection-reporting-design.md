# TempGlitch Selection Reporting Design

Date: 2026-07-01
Status: approved for implementation planning

## Objective

Clarify and harden the no-GPU TempGlitch evidence path after the scorer/aggregation audit showed
that the relevant `max`-style LeWM rows already exist in validated artifacts. The work should
prevent paper or claim-registry drift between the best validated rows and the reported rows,
without retraining, rescoring windows, launching Kaggle, or touching locked-test material.

## Context

The current `r5_tempglitch_eval` path already evaluates multiple LeWM window scorers:
`lewm_mse_mean`, `lewm_mse_max`, `lewm_mse_top2_mean`, `lewm_l2_mean`, `lewm_l2_max`, and
`lewm_l2_top2_mean`. It also evaluates episode aggregations `mean`, `max`, and `top2_mean`.

Current validated observations:

- R5 TempGlitch identical-episode evidence: best inspected row is seed44 `lewm_l2_max` with
  episode `mean`, AUROC `0.69696969697`.
- Pair-disjoint TempGlitch follow-up: best inspected row is seed44 `lewm_l2_max` with episode
  `mean`, AUROC `0.715909090909`.
- K-A expanded TempGlitch intake: best recorded row is seed43 `lewm_l2_max` with episode `mean`,
  AUROC `0.700544`.

This means the immediate task is not to add a missing scorer. It is to make the existing best-row
selection and reporting harder to misread, especially the distinction between window scorer
selection and episode aggregation.

## Scope

This task includes:

- Audit paper text, paper tables, and claim registry entries against the validated TempGlitch
  artifacts.
- Add or tighten a lightweight reporting helper that reads comparison artifacts and emits ranked
  best-row summaries.
- Add tests for the helper using small synthetic CSV/JSON fixtures.
- Preserve all locked-test, Kaggle, output, checkpoint, Lance, cache, and credential safety
  boundaries.

This task excludes:

- Any GPU retraining or new model scoring.
- Any new performance claim not already backed by validated artifacts.
- Any locked-test materialization or scoring.
- Any broad superiority, state-of-the-art, temporal-localization, cross-game, SIGReg-benefit, or
  action-conditioning-benefit language.

## Design

### Audit Pass

Review the current manuscript and claim registry for stale or ambiguous wording around TempGlitch
results. The audit should verify that reported rows match the validated artifacts and that wording
does not imply that episode `max` is the best TempGlitch aggregation when the validated best rows
use `lewm_l2_max` as the window scorer with episode `mean`.

The audit should treat K-B / R5-XGame as a separate bounded result and should not use its high
AUROC to infer a TempGlitch result.

### Reporting Helper

Introduce a small command-line helper, or extend an existing reporting script if a suitable one
already exists, with this behavior:

- Input: one comparison CSV and optional metrics/provenance JSON.
- Output: top rows by AUROC, AUPRC, and F1, with method family, method, seed, `window_scorer`,
  `episode_aggregation`, support counts, threshold source, confidence intervals, and safety flags
  when present.
- Validation: fail closed if required columns are missing, numeric metrics are non-finite, or
  locked-test flags indicate materialization/scoring.
- Guardrail: print a clear note that `window_scorer=max` and `episode_aggregation=max` are distinct
  concepts.

The helper should be evidence-audit tooling, not an experiment runner.

### Tests

Add focused tests using tiny synthetic comparison rows. Tests should cover:

- Correct ranking by AUROC.
- Correct distinction between `window_scorer` and `episode_aggregation`.
- Failure on missing required columns.
- Failure on non-finite metric values.
- Failure when optional safety metadata indicates locked-test materialization or scoring.

Tests must not depend on ignored output artifacts.

## Acceptance Criteria

- A no-GPU command can summarize best validated rows from a comparison CSV.
- The helper makes it hard to confuse `lewm_l2_max` as a window scorer with episode-level `max`
  aggregation.
- Paper-facing TempGlitch wording remains bounded to validated non-locked artifacts.
- Claim registry and manuscript text are synchronized if any stale wording is found.
- Focused tests pass.
- Required repository validators are run or any skipped checks are reported honestly.

## Later GPU Decision Gate

A future GPU experiment should only be designed after this no-GPU audit is complete and one of the
following is true:

- K-C WOB binary intake fails or remains unavailable.
- The paper still needs a stronger bounded TempGlitch result after correct best-row reporting.
- The user explicitly chooses to spend GPU budget on a combined retraining experiment.

If that gate opens, the next GPU design should combine history-size and encoder/pretraining
choices into one controlled experiment family instead of launching isolated one-off runs.

## Spec Self-Review

- Placeholder scan: no placeholders remain.
- Consistency check: the design treats current scorer coverage as existing and focuses on reporting
  hardening.
- Scope check: the implementation is small enough for one plan and excludes GPU work.
- Ambiguity check: acceptance criteria name the exact distinction that caused the current confusion.
