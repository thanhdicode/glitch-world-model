# Real LeWorldModel Integration Audit

## Verified Upstream Identity

- Local reference: `external/le-wm`
- Audited commit: `8edfeb336732b5f3ce7b8b210d0ba370a09e2cac`
- License: MIT
- Upstream implementation files: `train.py`, `jepa.py`, `module.py`, `utils.py`
- External runtime dependencies: `stable-worldmodel[train,env]`, `stable-pretraining`, Hydra,
  Lightning, PyTorch
- Current local default environment does not contain `stable_worldmodel`,
  `stable_pretraining`, `lightning`, `h5py`, or `torch`.

## Verified Model And Training Contract

| Item | Verified behavior |
| --- | --- |
| Pixels | `JEPA.encode()` expects `pixels` shaped `(B,T,C,H,W)` after dataset transforms |
| Actions | Official training always reads `batch["action"]` and predicts with action embeddings |
| History/prediction | Default `history_size=3`, `num_preds=1`, dataset window length `4` |
| Image processing | ImageNet conversion/normalization plus resize to default `224` |
| Encoder | ViT tiny, patch size `14`, trained from scratch by default |
| Predictor | Action-conditioned autoregressive transformer |
| Loss | Next-embedding MSE plus weighted SIGReg |
| Default SIGReg weight | `0.09` |
| Default precision | `bf16` GPU training |
| Checkpoints | Lightning weights checkpoint plus epoch `weights.pt` exports/object checkpoint |
| Resume | Existing weights checkpoint is passed to `stable_pretraining.Manager` |

## Dataset Findings

The README describes HDF5 datasets under `STABLEWM_HOME`, but the current PushT training config
uses a `.lance` dataset while DMC/OGB configs use `.h5`. Therefore the exact custom-writer
contract must be verified against the installed `stable-worldmodel` version before implementing
the converter.

The minimum logical columns inferred from upstream code are:

- `pixels`
- `action`
- `episode_idx` or `ep_idx`
- `step_idx`

Optional environment columns include `observation`, `proprio`, and `state`.

The official `train.py` performs a random dataset split. For gameplay research this is unsafe
until confirmed to split whole episodes rather than overlapping temporal windows. The adapter
must create train/validation datasets from source-disjoint episode lists before loading.

## Action Availability Decision

TempGlitch supplies gameplay video but no verified action logs. Three modes are scientifically
distinct:

1. **Original action-conditioned LeWM:** requires real action-logged trajectories. This is the
   strongest and preferred claim path.
2. **Zero-action LeWM adaptation:** write a fixed one-dimensional zero action per frame. This
   preserves the official encoder, predictor, and SIGReg training code but removes useful action
   conditioning. It is a valid MVP experiment only when named explicitly.
3. **Action-free predictor variant:** replace action conditioning with an unconditional temporal
   predictor. This is a method modification and must be described as such.

Optical-flow pseudo-actions are an optional ablation, not a substitute for real actions, because
they are derived from the observations being predicted.

## Checkpoint Feasibility

Official pretrained checkpoints are environment-specific. Their visual domains and action
dimensions do not match TempGlitch by default. A checkpoint-load smoke test is feasible, but
direct TempGlitch prediction is not considered valid until preprocessing, predictor input, and
action dimensions match.

Recommended checkpoint decisions:

- First prove reconstruction/loading of one official checkpoint on CPU.
- Verify output tensor shapes on matching official sample data.
- Use pretrained encoder weights only as a documented ablation if full predictor dimensions do
  not match.
- Prefer training the action-agnostic gameplay model from scratch over silently coercing an
  incompatible environment checkpoint.

## Kaggle Feasibility

The upstream README states approximately 15M trainable parameters and single-GPU training.
Kaggle feasibility is plausible but not yet verified in this repo. Default batch size `128`,
image size `224`, six-layer predictor, and SIGReg with `1024` projections may exceed practical
memory. Smoke training must start with a small batch, short run, and checkpoint resume test.

## Go / No-Go

**GO for Phase 1-4 integration engineering.**

Do not claim training success yet. The next required proof is:

1. isolated Python 3.10 dependency environment;
2. official checkpoint load smoke test;
3. verified custom dataset schema and 5-10 clip loader test;
4. local CPU forward/backward smoke;
5. Kaggle GPU smoke with a saved checkpoint.

If action-logged data cannot be obtained, proceed with zero-action and action-free adaptations
but restrict the paper claim accordingly.
