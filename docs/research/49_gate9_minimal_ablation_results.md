# Gate 9 Minimal Ablation Results

Status date: 2026-06-12
Result: `gate9_passed_window_pilot`

Gate 9 compares six predeclared LeWM transition aggregations and two baselines. AUROC and AUPRC
are primary. F1 is secondary and uses a scorer-specific threshold equal to the 95th percentile
of scores from the two calibration-normal episodes.

## Results

| Scorer | AUROC | AUPRC | P95 F1 |
| --- | ---: | ---: | ---: |
| LeWM L2 max | 0.795879 | 0.375364 | 0.000000 |
| LeWM MSE max | 0.795879 | 0.375364 | 0.000000 |
| Frame difference | 0.758981 | 0.290643 | 0.370700 |
| LeWM MSE top-2 mean | 0.739406 | 0.296952 | 0.000000 |
| LeWM L2 top-2 mean | 0.738275 | 0.295776 | 0.000000 |
| LeWM MSE mean | 0.696881 | 0.266296 | 0.000000 |
| LeWM L2 mean | 0.694722 | 0.264492 | 0.000000 |
| Feature distance | 0.064110 | 0.068626 | 0.000000 |

The LeWM max variants rank the single buggy episode's windows above normal windows more often
than the named baselines. However, every LeWM normal-P95 threshold is above all buggy scores,
yielding zero recall and F1. Ranking and operating-point evidence therefore disagree.

## Protocol And Artifacts

- Evaluation windows: 8,528.
- Positive windows: 1,088; negative windows: 7,440.
- Positive prevalence: 0.127580.
- Buggy episodes: one, `Godot_Shooting_Error_Buggy_107`.
- Comparison SHA-256:
  `102d45cd13c1cdc0fe15bc8291a11cf976bb58daa203f16f8d67ff5002bbc2af`.
- Results SHA-256:
  `89d1f3b4c4c66650fa307b542cee5e62a06cbb2ac0c20ca7834ae1be235b100a`.
- Evaluation code Git SHA: `f22e1be92fed098752069616deb7ed2b26b8fcc1`.

Windows from one episode are correlated, and only one buggy episode is present. These values are
diagnostic pilot metrics, not a broad benchmark result. No model retraining, locked-test access,
or post-evaluation threshold fitting occurred.
