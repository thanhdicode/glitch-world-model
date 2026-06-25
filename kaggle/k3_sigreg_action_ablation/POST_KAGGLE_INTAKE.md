# Post-Kaggle Intake

After the Kaggle job completes:

1. Download the produced output bundle or extracted output directory.
2. Run the local intake validator:

```bash
python scripts/ingest_k3_ablation_bundle.py \
  --bundle <downloaded_k3_bundle_or_extracted_dir> \
  --output-root outputs/k3_ablation_intake
```

Expected local outputs:

- `outputs/k3_ablation_intake/k3_ablation_intake_summary.json`
- `outputs/k3_ablation_intake/K3_ABLATION_INTAKE_REPORT.md`

No scientific claim may expand before this intake step succeeds.
