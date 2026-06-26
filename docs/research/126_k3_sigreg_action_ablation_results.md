# 126 - K3 SIGReg / Action Ablation Results

Date: 2026-06-26
Status: K3 downloaded output intake validated; negative mechanistic readout

## Evidence Intake

The completed user-operated Kaggle K3 output was found at:

- `C:\Users\ADMIN\Downloads\results\r6_sigreg_ablation`

Local intake command:

```powershell
python scripts\ingest_k3_ablation_bundle.py --bundle C:\Users\ADMIN\Downloads\results\r6_sigreg_ablation --output-root outputs\k3_ablation_intake
```

The intake validator passed with:

- status: `k3_ablation_bundle_validated`
- variants: `12`
- controlled pairs: `12`
- seeds: `[42, 43, 44]`
- train hash:
  `34ef70fd3e7cb288646b8e5e1fb4f8ae60e9308cddcd2401c8d77c717c076efc`
- validation hash:
  `ecb4c9ef1349b8e1896b783a7ae7b3f6761b2d445370ff814e2cfc179ebbfa19`
- locked test materialized: `false`
- locked test scored: `false`
- intake summary SHA256:
  `d28cb1ffaab1f61015b4522a208100cfc944bb1dd12b2031183c21b6fd89b670`
- intake report SHA256:
  `7fcfdd00666d86c9db3f5eacd60c1baaf10f7712cc56aebed32b78b06da30441`

## Training Completion

All 12 variants completed 500 optimizer updates, wrote five validation evaluations, and reported
checkpoint reload verification. The run is therefore valid as a controlled K3 validation-normal
training/readout artifact.

The four variant groups were:

| SIGReg | Action mode | Mean best total validation loss | Mean best prediction loss |
|---|---|---:|---:|
| off | real | `0.001181` | `0.001181` |
| off | zero_action | `0.001075` | `0.001075` |
| on | real | `0.280237` | `0.019721` |
| on | zero_action | `0.284195` | `0.018489` |

For SIGReg-on variants, total validation loss includes the SIGReg penalty, so prediction loss is
the safer cross-toggle diagnostic when interpreting reconstruction/prediction behavior.

## Paired Readout

Best prediction-loss deltas for SIGReg-on minus SIGReg-off were positive in all six matched
comparisons, meaning lower-is-better prediction loss did not improve with SIGReg in this K3 run:

| Seed | Real-action delta | Zero-action delta |
|---:|---:|---:|
| 42 | `+0.016560` | `+0.019388` |
| 43 | `+0.020677` | `+0.017309` |
| 44 | `+0.018384` | `+0.015546` |

Real-action minus zero-action best prediction-loss deltas were not directionally stable:

| Seed | SIGReg-on delta | SIGReg-off delta |
|---:|---:|---:|
| 42 | `-0.003042` | `-0.000215` |
| 43 | `+0.003361` | `-0.000008` |
| 44 | `+0.003377` | `+0.000539` |

## Claim Boundary

Allowed after K3:

- The K3 controlled-pair output bundle validated locally with 12 variants, 12 controlled pairs,
  seeds 42/43/44, matching dataset hashes, and false locked-test flags.
- On the K3 validation-normal training objective, no measurable SIGReg benefit was observed.
- On the same K3 artifact, no stable real-action-over-zero-action benefit was observed.

Still forbidden:

- broad SIGReg benefit
- broad action-conditioning benefit
- detection-performance, AUROC, superiority, or state-of-the-art claims from K3
- temporal-localization claims
- cross-game generalization claims
- locked-test claims

## Next Task

Phase P4/K3 is no longer blocked on Kaggle execution or intake. The next roadmap task is Phase P5:
temporal localization metrics or explicit documented future-work scoping. Before P5 implementation,
paper-facing surfaces should use the K3 result as an honest negative mechanistic readout rather
than as an improvement claim.
