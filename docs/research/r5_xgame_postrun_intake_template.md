# R5-XGame Post-Run Intake Template

Download `r5_xgame_outputs.tar.gz`, its `.sha256` sidecar, and the Kaggle log. Extract only outside
the repository, then validate the extracted output directory against the frozen manifest:

```powershell
python scripts/validate_r5_xgame_output_bundle.py --output-dir <extracted-output-dir>
```

Do not update claims until this validator passes. Quarantine a bundle if it includes test/locked
rows, lacks fresh seed provenance, has missing stage markers, or has incomplete binary metrics.
