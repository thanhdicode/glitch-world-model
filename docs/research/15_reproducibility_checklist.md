# Reproducibility Checklist

Use this checklist before any result is copied into a paper draft, slide deck, or public report.

## Environment

- [ ] Record OS, Python version, and package install command.
- [ ] Record `git rev-parse HEAD`.
- [ ] Record whether the run used CPU or GPU.
- [ ] Confirm optional dependencies used by the run are documented.
- [ ] Confirm no local-only patches are present with `git status --short`.

## Dependency install

- [ ] Core/dev setup: `python -m pip install -e ".[dev]"`.
- [ ] Research extras, only when needed: `python -m pip install -e ".[dev,research]"`.
- [ ] Video extras, only when needed: `python -m pip install -e ".[dev,video]"`.
- [ ] Avoid adding PyTorch/GPU stacks without a separate integration task.

## Seed control

- [ ] Record random seeds for generated datasets.
- [ ] Record split seeds for train/validation/test.
- [ ] Record any model initialization seed.
- [ ] Record any non-deterministic libraries or hardware settings.

## Dataset version, source, and license

- [ ] Record dataset name and official URL.
- [ ] Record access date.
- [ ] Record license or permitted research use.
- [ ] Record exact subset, split, or filtering parameters.
- [ ] Keep raw data under gitignored `data/`.
- [ ] Do not commit downloaded videos, generated clips, or checkpoints.

## Command log

- [ ] Save preprocessing command.
- [ ] Save scoring command.
- [ ] Save evaluation command.
- [ ] Save reporting or comparison command.
- [ ] Include command logs in experiment notes or result logs.

## Metrics log

- [ ] Confirm `scores.csv` exists.
- [ ] Confirm `metrics.json` exists.
- [ ] Record AUROC, F1, precision, recall.
- [ ] Record threshold selection method.
- [ ] Mark all unrun experiments as `TBD`.

## Output file paths

- [ ] `manifest.csv`
- [ ] `scores.csv`
- [ ] labels CSV with `source,start_frame,end_frame,label`
- [ ] `metrics.json`
- [ ] plots and Markdown reports, if generated

## Data leakage check

- [ ] Split by video/source, not by overlapping clips, when evaluating real datasets.
- [ ] For paired datasets, verify that official or clearly labeled heuristic pair groups do not
  cross train, validation, and test.
- [ ] Save a pair/group leakage report and split seed before scoring.
- [ ] Fit normal-only baselines only on allowed train/validation data.
- [ ] Choose thresholds on validation data before reporting test results.
- [ ] Check that generated clips from the same original video do not cross split boundaries.

## Threshold selection check

- [ ] Record whether threshold was fixed, chosen by validation F1, or chosen by another rule.
- [ ] Do not tune threshold on the final test set.
- [ ] If current MVP best-F1 thresholding is used, label it as exploratory.
- [ ] Select scorer and aggregation on validation only; do not rank test candidates to choose a
  reported configuration.
- [ ] Evaluate exactly one saved selected configuration on locked test.
- [ ] Report source- or pair-level confidence intervals for the locked test result.

## Phase 6D repeated grouped release gate

- [ ] Record the fixed subset provenance and original sample mode.
- [ ] Run every registered seed through pair-suspect grouped split validation.
- [ ] Confirm zero cross-split groups for every seed.
- [ ] Record train-normal sources and clips used by every fitted scorer.
- [ ] Confirm all validation candidates exist before the selected test scorer is scored.
- [ ] Confirm exactly one test score file and one locked-test configuration per seed.
- [ ] Report per-seed grouped bootstrap intervals and mean plus population standard deviation
  across seeds.
- [ ] Describe repeated results as selected-pipeline performance, not per-scorer superiority.

## Figure/table provenance

- [ ] Every table value points to a metrics file or script output.
- [ ] Every figure points to the command and source file used to generate it.
- [ ] Qualitative examples include source IDs and frame/clip ranges.

## Paper claim evidence check

- [ ] Every experimental claim has a metrics artifact.
- [ ] Every background claim has a citation.
- [ ] Every limitation is stated honestly.
- [ ] Synthetic data is labeled as sanity check only.
- [ ] Benchmark results are only claimed after dataset format and protocol are verified.

## What must not be claimed

- [ ] Do not claim state of the art without direct benchmark comparison.
- [ ] Do not claim real LeWorldModel integration before `lewm_latent` is actually implemented.
- [ ] Do not claim TempGlitch is downloaded or parsed before verified local files exist.
- [ ] Do not claim all game bugs are detectable.
- [ ] Do not claim VLM superiority or inferiority unless measured under the same protocol.
