# LeWM Research-Grade Experiment Plan

Status date: 2026-06-12
Status: protocol implementation started; no new performance claim

## Why The 92-Second Run Is Not A Research Result

Gate 6 was deliberately limited to one epoch, 16 train batches, and eight validation batches.
The run's own metadata calls it `training_smoke_complete`. Most of its 92-second Kaggle runtime
was dependency installation and model initialization. It proves CUDA execution, checkpoint
writing, reload, and finite encoding. It does not establish convergence, generalization, glitch
detection, or scientific novelty.

Tests and validators were still necessary: without them, later metrics could silently use
leaked pairs, a broken checkpoint, mismatched preprocessing, or locked-test data. The project
mistake was not testing too much; it was allowing engineering gate completion to appear closer
to paper evidence than it really was.

## Research Question And Contribution

Primary question:

> Can a lightweight LeWM trained only on normal gameplay produce calibrated latent-transition
> surprise that distinguishes unseen non-locked buggy episodes from normal episodes?

Candidate contribution:

> A leakage-aware, calibration-aware latent-surprise protocol for lightweight gameplay glitch
> detection, with episode-level uncertainty and controlled action-conditioning ablations.

This is a hypothesis, not a claim. The contribution survives a negative result if the protocol
shows when latent ranking works but normal-only threshold calibration fails.

## Available Research MVP

The local TempGlitch cache currently contains 100 videos. Under the frozen pair/source split,
the usable non-locked research subset contains:

- 36 train-normal episodes;
- 14 validation-normal episodes;
- 22 validation-buggy episodes;
- all five glitch categories.

This is substantially stronger than the Gate 6 `20 + 10 + 1` pilot, but it is not yet the full
1,500-video metadata universe. Disk space is currently insufficient for an unplanned full
download plus duplicated Lance/Kaggle packages.

## Training Protocol

1. Materialize all locally available train-normal and validation-normal episodes into Lance.
2. Keep validation-buggy episodes out of optimization and checkpoint selection.
3. Run a 500-update engineering profile to measure memory, throughput, and projected Kaggle
   time. Do not report its performance as research evidence.
4. Run the main budget with 15,000 target optimizer updates, resume support, validation-normal
   checkpoint selection, and early stopping after five non-improving evaluations.
5. Repeat the frozen protocol for seeds 42, 43, and 44.
6. Score every non-locked validation episode with the frozen checkpoint from each seed.

Training duration is therefore governed by a predeclared update budget and convergence evidence,
not by an arbitrary wall-clock target.

## Evaluation Protocol

- Primary unit: episode/video. Correlated windows are diagnostic only.
- Primary metrics: AUROC and AUPRC.
- Secondary metrics: normal-calibrated F1 and FPR at 95% TPR.
- Uncertainty: 95% grouped episode-bootstrap intervals.
- Required baselines: frame difference, feature distance, Conv3D autoencoder, and one frozen
  video-representation baseline.
- Minimal ablations: SIGReg weight, surprise distance, transition aggregation, training budget,
  and real-action versus zero-action on World of Bugs.

## International-Standard Boundaries

A credible paper requires falsifiable hypotheses, multiple seeds, uncertainty, fair baselines,
episode-disjoint evaluation, negative-result disclosure, exact hashes, and reproducible code.
Longer training alone does not create international-standard evidence.

No claim of state of the art, broad superiority, temporal localization, SIGReg benefit, or
locked-test performance is allowed before the corresponding evidence exists. Locked test remains
closed until one configuration and threshold are frozen from non-locked validation evidence.

## Execution Order

1. Pass `audit_lewm_research_source.py`.
2. Materialize the 36/14/22 non-locked Lance datasets without duplicating raw videos.
3. Run the 500-update profile and record throughput/VRAM.
4. Freeze the feasible main-run batch size and evaluation interval.
5. Run seed 42 end to end and validate artifacts.
6. Run seeds 43 and 44.
7. Run same-manifest baselines, grouped metrics, and ablations.
8. Update claims and paper only after artifact validation.
