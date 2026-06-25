# K3 SIGReg And Action-Conditioning Ablation

This package is the local launch surface for Phase P4 / Kaggle K3.

Scope:

- controlled SIGReg on/off ablations
- controlled real-action vs zero-action ablations
- seeds `42`, `43`, and `44`

Guardrails:

- locked test must remain closed
- no SIGReg or action-conditioning scientific claim is allowed before the downloaded K3 bundle
  validates locally
- the scientific run requires the prepared `k3_input_manifest.json` plus matching Lance inputs

Entry point:

```bash
python kaggle/k3_sigreg_action_ablation/run_k3_ablation.py --device cuda
```

See:

- [KAGGLE_RUN_COMMAND.md](./KAGGLE_RUN_COMMAND.md)
- [KAGGLE_OUTPUTS_EXPECTED.md](./KAGGLE_OUTPUTS_EXPECTED.md)
- [POST_KAGGLE_INTAKE.md](./POST_KAGGLE_INTAKE.md)
