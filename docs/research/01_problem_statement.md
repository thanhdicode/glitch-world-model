# Problem Statement

## Background

Video game glitches and bugs are unintended, player-visible failures in rendering, physics, animation, collision, state transitions, or gameplay logic. Examples include clipping through walls, teleportation, missing textures, flickering objects, frozen characters, impossible velocity changes, invalid camera behavior, or actions resolving in an impossible direction.

Automated glitch detection is useful for game QA because modern games have large state spaces, long interaction horizons, and many rare edge cases. Manual testing remains valuable, but it is difficult to exhaustively explore every combination of actions, camera states, assets, physics interactions, and rendering conditions.

## Limits of static frame anomaly detection

Static frame anomaly detection can catch visible errors such as missing textures, severe geometry clipping, or a black screen. It is weaker when the glitch is only obvious after observing motion over time. A single frame may look plausible even if the sequence is wrong.

Examples where static frames are limited:

- A character moves behind the player immediately after aiming forward.
- A player appears at a valid position, but reached it through impossible velocity.
- An object is visible in each frame, but flickers over time.
- A character is stuck despite repeated movement attempts.
- A collision violation is only clear from before/after context.

## Why temporal dynamics matter

Gameplay is governed by state transitions. Even if the full game engine state is not available, ordered visual frames carry clues about expected dynamics: position changes, velocities, collisions, animation phase, object persistence, and camera motion. Glitches can therefore be framed as violations of learned transition expectations.

The core modeling question is not only "does this frame look strange?" but also "does this next state make sense given the previous states?"

## Why latent world models fit

Latent world models compress observations into a representation space and learn to predict future latent states. This is attractive for glitch detection because:

- latent representations can suppress pixel noise and focus on meaningful state
- next-latent prediction can model dynamics without reconstructing every pixel
- prediction error gives a natural anomaly score
- normal-only training or adaptation can support one-class detection
- JEPA-style objectives are aligned with predicting abstract future representations

## Problem statement

Given gameplay clips and optional temporal glitch labels, build a reproducible pipeline that scores each clip for glitch likelihood using temporal dynamics. The target research method is latent prediction error from a world model trained or adapted on normal gameplay. The current repository should first establish reliable baselines and documentation before real LeWorldModel integration.

## Success criteria

- The pipeline can preprocess clips, score them, evaluate metrics, and write reports without changing file interfaces.
- Simple baselines are documented and comparable.
- `mini_latent` provides a lightweight proxy for latent-dynamics surprise.
- Public benchmark use is prioritized over synthetic evidence.
- Any future LeWM result can be compared against existing baselines using the same `scores.csv` and `metrics.json` formats.
- Claims remain proportional to available data and verified benchmarks.
