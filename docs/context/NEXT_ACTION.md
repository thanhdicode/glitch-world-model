# NEXT_ACTION.md

Last updated: 2026-06-24T01:07:30.4365951+07:00
Commit: `228f128559edb6154ff82143477b42f45fe84501`

## Current Priority
Execute the bounded TempGlitch follow-up from existing validated `R5` artifacts only. The follow-up
must freeze a pair-disjoint calibration split, recompute support-matched episode metrics and
provenance, and stay entirely non-locked without retraining or Kaggle execution.

## Next Gate
1. Re-freeze TempGlitch calibration on the pair-disjoint normal episodes
   `Godot_Blinking_Normal_106` and `Godot_Frozen_Animation_Platformer_Normal_107`.
2. Reuse the existing validated `R5` raw score files to build a fresh bounded follow-up output
   directory with one frozen manifest and exact support matching across all compared rows.
3. Report AUROC, AUPRC, F1, precision, recall, balanced accuracy, FPR@95TPR, support counts, and
   grouped confidence intervals with explicit non-locked claim language.
4. Add a command log plus a dedicated validator receipt so the follow-up is evidence-bearing
   without relying on old Phase 6D or locked-test-style artifacts.

## Success Criteria
- Preserve the completed `R5` TempGlitch raw score, metrics, and provenance hashes as source
  evidence.
- Preserve the pair-disjoint follow-up calibration freeze:
  `Godot_Blinking_Normal_106` and `Godot_Frozen_Animation_Platformer_Normal_107`.
- Preserve follow-up evaluation support at `34` episodes:
  `12` normal-negative and `22` buggy-positive.
- Keep every compared row on exact manifest and support alignment.
- Do not relaunch Kaggle or rerun LeWM training unless a required raw artifact is truly missing.
- Keep locked-test materialization/scoring false.
- Make no broad TempGlitch/WOB/XGame performance, cross-game, action-conditioning, or
  SIGReg-benefit claim beyond the exact qualified non-locked bundles.
- Keep the follow-up explicit about its bounded public-benchmark scope, binary video labels, and
  non-locked status.

## Current Known Blocker
The bounded TempGlitch lane is ready, but the current `R5` manifest still uses one
calibration/evaluation pair overlap and does not emit a dedicated validator receipt or full
comparison metric surface. `R5-XGame` remains positive-heavy and `R5-WOB` remains positive-probe
only, so broad generalization, final paper-grade benchmark claims, WOB binary benchmark claims,
and locked-test claims remain blocked. Locked test stays closed.
