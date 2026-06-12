# Artifact Manifest

| Artifact | Storage | Status |
| --- | --- | --- |
| Gate 6 source audit and Lance datasets | ignored `outputs/gate6/datasets/` | verified locally |
| Gate 6 Kaggle dataset | `huynhdieuthanh/lewm-tempglitch-gate6-pilot` | ready |
| Gate 6 v3 kernel log | ignored `outputs/gate6/kaggle_runs/` | failed before epoch 1 |
| Gate 6 v5 package/request | ignored `outputs/gate6/` | historical submission failure |
| Gate 6 v6 kernel | ignored run log | accepted, runtime packaging failure |
| Gate 6 v7 package/artifacts | ignored `outputs/gate6/automation/` | runtime mount-discovery failure |
| Gate 6 v8 package/audit | ignored `outputs/gate6/automation/lewm_gate6_pilot_v8/` | verified |
| Gate 6 v8 remote artifacts | ignored downloaded artifacts | strict validator `gate6_passed` |
| Gate 6 checkpoint | ignored downloaded artifact | SHA-256 `300cefe9622ab43acd79bc2202ac90a214cbc4ae9921ed3434573fc9198ff252` |
| Gate 7 canonical manifest | ignored `outputs/gate7/window_manifest.csv` | verified; SHA-256 `c1b2971d259cf0cdc495c9b7b171d1bcb9f34d2c6c073e4bdd51cb60fcb00003` |
| Gate 7 LeWM transition scores | ignored `outputs/gate7/lewm_transition_scores.csv` | verified; 10,081 finite rows; SHA-256 `b68f1be33b9410db22a855082eb61dcab74abdd23571b361ce6219ca5289eefa` |
| Gate 7 metadata | ignored `outputs/gate7/gate7_metadata.json` | verified; SHA-256 `7021dce9f3825fec5e1bbe3b9fbeb502c327b96e4059bf3736cbf47b28a92d8b` |
| Gate 8 baseline scores | ignored `outputs/gate8/baseline_scores.csv` | verified same-manifest rows; SHA-256 `5a0e0df78e002d294c37d28d0e9ae47936ab16b2a74d8d2f99da486c6017e2de` |
| Gate 8 metadata | ignored `outputs/gate8/gate8_metadata.json` | verified; SHA-256 `52370d3ab39b3d033c370df1dfb96d77bad077ff9eb8785c821a393e29fa0f2f` |
| Gate 9 comparison | ignored `outputs/gate9/comparison.csv` | verified; SHA-256 `102d45cd13c1cdc0fe15bc8291a11cf976bb58daa203f16f8d67ff5002bbc2af` |
| Gate 9 results | ignored `outputs/gate9/ablation_results.json` | verified window-level pilot; SHA-256 `89d1f3b4c4c66650fa307b542cee5e62a06cbb2ac0c20ca7834ae1be235b100a` |

No data, Lance dataset, checkpoint, Kaggle output, or credential is committed.
