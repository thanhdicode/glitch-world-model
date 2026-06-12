# RULES.md - Research Engineering Operating Rules

`PLAYBOOK.md` is the long-form operating bible; `RULES.md` remains the non-negotiable safety
layer.

## 1. Non-Negotiable Safety Rules

- Kaggle live actions and GPU training operate under repository standing authorization after
  required security, license, protocol, and package validation.
- Locked-test materialization or scoring requires a separate direct user command.
- Do not weaken gates, validators, or locked tests to make a task pass.
- Do not execute unreviewed scripts from reference repositories or skill marketplaces.

## 2. Scientific Claim Rules

- Evidence precedes claims. Register paper-facing claims in the claim registry.
- Never claim state of the art, LeWM superiority, SIGReg benefit, or real-time performance
  without direct comparable evidence.
- Never use fixture, synthetic, smoke, or scaffold output as a paper metric.
- Never claim temporal localization without verified temporal-span labels and temporal metrics.

## 3. Gate-Based Execution Rules

- Treat each roadmap gate as closed until its required artifacts pass the documented validator.
- Engineering readiness, smoke completion, gameplay-scale evaluation, and paper evidence are
  distinct states.
- A later gate cannot be inferred from earlier code or artifacts.

## 4. Dataset And Locked-Test Rules

- Split sources, pairs, and episodes before generating windows.
- Train normal-only protocols must never fit on glitch samples.
- Select configurations and thresholds on validation only; never fit a threshold on test.
- Freeze exactly one validation-selected configuration before locked-test approval.
- Score locked test once and disclose any invalidating post-test tuning.

## 5. Kaggle And GPU Rules

- Default every workflow to dry-run and validation-only.
- Kaggle dataset upload/version, kernel push/version, GPU execution, polling, artifact download,
  and validated public publication operate under repository standing authorization.
- Kaggle fingerprints remain mandatory audit and idempotency records; no request, approved, or
  consumed approval artifact is required.
- Remote deletion, credential publication, unlicensed public data, and validator bypass remain
  prohibited.
- Validate downloaded artifacts locally before updating any claim.
- A successful push, remote status, or audit record is not proof of successful training.

## 6. Artifact And Credential Hygiene

- Never commit `outputs/`, raw/processed data, Lance datasets, checkpoints, caches, credentials,
  `.env`, `kaggle.json`, access tokens, or private keys.
- Never print secret values.
- Hash datasets, splits, configs, checkpoints, scores, and metrics used as evidence.

## 7. Runtime And Dependency Rules

- Keep the default dev/CI environment lightweight.
- Use the isolated Python 3.10 LeWM runtime and pinned requirements for LeWM work.
- Keep optional imports isolated and fail closed when dependencies are unavailable.

## 8. Code Quality Rules

- Preserve public CSV/JSON interfaces and existing scorer registration.
- Prefer small changes, typed Python, structured parsers, and tests first for behavior.
- Do not rewrite external upstream code or revert unrelated user changes.

## 9. Experiment Tracking Rules

- Record git SHA, command, environment, seed, dataset/split/config hashes, checkpoint hash,
  score/metric hashes, action mode, and allowed claim scope.
- Optional tracking tools do not replace immutable local artifacts.

## 10. Paper And Citation Rules

- Use primary sources where available and verify venue format before submission.
- A LeWM-framed title requires Gate 7; a locked-test metric requires Gate 10.
- Keep validation-only, diagnostic, exposed-test, and locked-test evidence visibly separate.

## 11. Commit And Release Checklist

- Run tests, Ruff lint/format, release validation, claim validation, doctor, and pre-commit.
- Inspect `git diff --check`, changed paths, and tracked artifacts before commit.
- Document any skipped dependency or unavailable check.

## 12. Agent Final Report Format

- State branch/SHA, files changed, commands/results, claims allowed/forbidden, Kaggle/locked-test
  status, artifact/credential status, risks, and the next recommended gate.
