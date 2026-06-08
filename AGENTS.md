# AGENTS.md

Project-specific guidance for future Codex tasks:

- Preserve the CSV interfaces: `manifest.csv`, `scores.csv`, labels CSV, and `metrics.json`.
- Keep scorers pluggable through `src/glitch_detection/score_clips.py`.
- Do not commit raw data, generated outputs, checkpoints, `.test-tmp`, or cache folders.
- Prefer small, testable changes over broad rewrites.
- Keep docs and methodology aligned with the existing preprocess -> score -> evaluate -> report pipeline.
- Run tests when dependencies are available.
- Document failed or skipped tests honestly, including missing dependencies.
