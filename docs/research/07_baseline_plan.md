# Baseline Plan

| Baseline | Why included | Expected strength | Expected weakness | Compute cost | Integration priority |
| --- | --- | --- | --- | --- | --- |
| Frame difference | Minimal temporal baseline already implemented | Catches sudden visual changes and flicker | False positives on normal high motion; misses semantic glitches | Very low | Already implemented |
| Feature distance | Simple appearance anomaly baseline already implemented | Catches static visual outliers and color/texture shifts | Weak temporal understanding | Very low | Already implemented |
| Mini latent PCA transition model | Lightweight proxy for latent-dynamics hypothesis | Models simple temporal transitions and surprise | Linear/PCA capacity is limited; toy-friendly | Low | Already implemented |
| Video autoencoder / ConvLSTM autoencoder | Classic video anomaly baseline | Learns normal spatiotemporal reconstruction | Reconstruction can focus on pixels rather than game rules | Medium | Future baseline |
| CNN-LSTM | Supervised or weakly supervised temporal classifier | Strong if enough labeled clips exist | Needs labels and can overfit to datasets | Medium | Future baseline |
| TimeSformer | Standard video transformer baseline | Strong representation for labeled video tasks | Not an anomaly detector by default | Medium-High | Optional future baseline |
| VideoMAE / VideoMAE V2 | Self-supervised video representation baseline | Strong video features; can support linear probes | Needs checkpoints and adaptation choices | Medium-High | Optional future baseline |
| VLM-based baseline | Aligns with GlitchBench and open-ended reports | Can reason about visible/semantic glitches | Expensive, prompt-sensitive, weaker temporal grounding | High | Future comparison only |
| LeWM latent prediction error | Main research target | Directly tests latent world model surprise hypothesis | Integration and compute risk | Medium-High | Future primary method |

## Baseline ordering

1. Keep existing lightweight baselines stable.
2. Add only one new baseline at a time.
3. Require each baseline to write the existing `scores.csv` schema.
4. Compare against `mini_latent` before making claims about LeWM.
