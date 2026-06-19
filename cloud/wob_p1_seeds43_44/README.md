# WOB-P1 Seeds 43/44 Kaggle Runners

This directory provides human-run Kaggle notebook entrypoints for the controlled `WOB-P1`
seed43/44 real-action, train-normal-only training stage under Ambitious Plan A.

Scope:

- seed43 and seed44 training only;
- official mounted Kaggle WOB datasets only;
- train-normal fit;
- validation-normal checkpoint selection only;
- validation-buggy excluded from fit/select;
- locked rows skipped;
- no WOB evaluation;
- no locked-test materialization or scoring.

Expected artifact outputs:

- `/kaggle/working/wob_seed43_artifacts.tar.gz`
- `/kaggle/working/wob_seed43_artifacts.tar.gz.sha256`
- `/kaggle/working/wob_seed43_failure_debug.tar.gz` only on failure
- `/kaggle/working/wob_seed44_artifacts.tar.gz`
- `/kaggle/working/wob_seed44_artifacts.tar.gz.sha256`
- `/kaggle/working/wob_seed44_failure_debug.tar.gz` only on failure

Notebook entrypoints:

- `cloud/wob_p1_seeds43_44/run_kaggle_wob_p1_seed43_robust.sh`
- `cloud/wob_p1_seeds43_44/run_kaggle_wob_p1_seed44_robust.sh`
- `cloud/wob_p1_seeds43_44/run_kaggle_wob_p1_seeds43_44_all.sh` for sequential execution only

Minimal Kaggle cell shape:

```bash
%%bash
set -euo pipefail
git clone https://github.com/thanhdicode/glitch-world-model.git
cd glitch-world-model
git checkout <exact-commit-sha>
bash cloud/wob_p1_seeds43_44/run_kaggle_wob_p1_seed43_robust.sh
```
