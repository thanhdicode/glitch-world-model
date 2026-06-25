# K3 Kaggle Run Command

Scientific command:

```bash
python kaggle/k3_sigreg_action_ablation/run_k3_ablation.py \
  --input-manifest kaggle/k3_sigreg_action_ablation/k3_input_manifest.json \
  --device cuda \
  --output-root /kaggle/working/r6_sigreg_ablation
```

Optional overrides:

- `--train-path <mounted_train_lance>`
- `--validation-path <mounted_validation_lance>`
- `--resume`

The run must stop if:

- CUDA is unavailable
- the train or validation Lance inputs are missing
- the mounted input hashes do not match the prepared manifest
