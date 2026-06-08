# Methodology v0

## Core method

The target method treats glitches as deviations from learned normal gameplay dynamics.

```text
normal gameplay
-> clip generation
-> latent encoding
-> next-latent prediction
-> prediction error / surprise score
-> threshold or lightweight classifier
-> glitch detection
```

For a clip with frames `x_1, ..., x_T`, an encoder maps frames to latents:

```text
z_t = f_encoder(x_t)
```

A dynamics model predicts the next latent:

```text
zhat_{t+1} = f_predictor(z_t, optional context)
```

The anomaly score can be the mean prediction error:

```text
score(clip) = (1 / (T - 1)) * sum_t ||z_{t+1} - zhat_{t+1}||_2
```

Higher scores indicate lower agreement with normal learned dynamics.

## Current MVP methods

### `frame_diff`

Computes mean absolute grayscale difference between consecutive frames. It is useful for strong visible changes, but it can confuse normal high-motion gameplay with glitches and miss subtle semantic or temporal errors.

### `feature_distance`

Computes simple RGB mean/std features per clip and scores distance from a normal centroid. It is useful for static or appearance-level anomalies, but it has limited temporal modeling.

### `mini_latent`

Uses PCA as a lightweight latent encoder. It fits a linear transition model from normal clips and predicts the next latent from current latent plus latent velocity. The score is mean latent prediction error. This is the current proxy for latent world model surprise.

## Future target: `lewm_latent`

The planned future scorer should use LeWorldModel or a compatible JEPA-style encoder/predictor. It should:

- load or adapt a verified checkpoint
- encode each clip into latent states
- predict future latents
- compute latent prediction error
- write `scores.csv` with the same schema used by current scorers

No real LeWM scoring is implemented in the current task.

## Expected file interfaces

### `manifest.csv`

Expected columns:

```text
clip_id,source,clip_dir,start_frame,end_frame,frame_count,fps
```

### `scores.csv`

Expected columns:

```text
clip_id,source,clip_dir,start_frame,end_frame,score
```

### labels CSV

Expected columns:

```text
source,start_frame,end_frame,label
```

Only `label == 1` is currently treated as glitch.

### `metrics.json`

Expected fields include:

- `threshold`
- `precision`
- `recall`
- `f1`
- `accuracy`
- `auroc`
- confusion counts
- `clip_count`
- `positive_clip_count`

## Practical alignment with code

- `preprocess.py` owns frame/video to clips.
- `score_clips.py` owns scorer selection.
- `evaluate.py` owns thresholding and metrics.
- `plot_scores.py`, `dataset_report.py`, and `compare_experiments.py` own reporting.
- Future LeWM integration should fit this structure rather than replacing it.
