---
name: Kaggle launcher runtime scaffolding
description: Any new Kaggle staged launcher must install the isolated LeWM runtime + verify imports, mirroring the R5-WOB launcher.
---

# Kaggle launcher runtime scaffolding

Any Kaggle staged launcher that reaches a Lance/LeWM stage (materialize, baseline_score,
train_lewm, lewm_score) must install the isolated LeWM runtime BEFORE running stages and verify
imports up front. A plain `pip install -e .` is NOT enough — the materialize stage fails with
`ModuleNotFoundError: No module named 'stable_worldmodel'` -> `LeWMDataUnavailableError`.

Required install pattern (copy from `cloud/wob_r5_eval/run_kaggle_r5_wob_staged.sh`):
- `--no-deps` block: stable-worldmodel==0.1.1, lancedb==0.30.0, pylance==4.0.0,
  lance-namespace==0.7.7, lance-namespace-urllib3-client==0.7.7, loguru, hydra-core.
- SEPARATE full-deps call: stable-pretraining==0.1.7 (+ transformers==4.57.6). It has ~24
  transitive deps (lightning, timm, …); `--no-deps` here causes `ModuleNotFoundError: lightning`.
- Then editable repo install (`pip install -e . --no-deps`).
- Then a fail-fast python import check: `stable_worldmodel.data`, the stable_pretraining hydra
  target, lightning, and the runner modules.

**Why:** Two consecutive R5-XGame Kaggle runs failed on different missing pieces (audit --output,
then this runtime) because the X-Game launcher was authored without the scaffolding the R5-WOB
launcher already had. Each gap burned a GPU run.

**How to apply:** When adding a new staged launcher under `cloud/`, mirror the R5-WOB install +
verification block and add install-completeness assertions to
`tests/test_staged_install_completeness.py` (version floors lancedb>=0.30.0, pylance>=4.0.0;
stable-pretraining pinned 0.1.7 and not in the --no-deps block; verification runs before the
materialize stage). Note the lazy `import stable_worldmodel` inside functions means importing the
runner module alone does NOT catch the missing runtime — probe it explicitly.
