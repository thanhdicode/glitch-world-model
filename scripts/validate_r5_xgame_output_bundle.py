"""Fail-closed validator for a completed R5-XGame output directory or tarball."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from glitch_detection.r5_xgame_protocol import validate_r5_xgame_manifest

REQUIRED = {
    "r5_xgame_manifest.csv",
    "r5_xgame_window_manifest.csv",
    "r5_xgame_baseline_scores.csv",
    "r5_xgame_episode_scores.csv",
    "r5_xgame_comparison.csv",
    "r5_xgame_metrics.json",
    "R5_XGAME_REPORT.md",
    "r5_xgame_provenance.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_output_dir(output_dir: Path, frozen_manifest: Path) -> dict[str, object]:
    missing = sorted(name for name in REQUIRED if not (output_dir / name).is_file())
    missing.extend(
        f"r5_xgame_lewm_scores_seed{seed}.csv"
        for seed in (42, 43, 44)
        if not (output_dir / f"r5_xgame_lewm_scores_seed{seed}.csv").is_file()
    )
    if missing:
        raise ValueError(f"R5-XGame output is incomplete: {missing}")
    manifest = output_dir / "r5_xgame_manifest.csv"
    if sha256(manifest) != sha256(frozen_manifest):
        raise ValueError("Output manifest hash differs from the frozen R5-XGame manifest.")
    with manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        counts = validate_r5_xgame_manifest(csv.DictReader(handle))
    provenance = json.loads((output_dir / "r5_xgame_provenance.json").read_text(encoding="utf-8"))
    for field in (
        "git_commit",
        "manifest_sha256",
        "role_counts",
        "seeds",
        "train_role_sha256",
        "calibration_role_sha256",
        "evaluation_role_sha256",
    ):
        if not provenance.get(field):
            raise ValueError(f"Provenance field is missing: {field}")
    for field in (
        "locked_test_materialized",
        "locked_test_scored",
        "validation_buggy_used_for_fit_select",
    ):
        if provenance.get(field) is not False:
            raise ValueError(f"Unsafe provenance flag: {field}")
    if provenance.get("old_r5_wob_checkpoint_reused") is not False:
        raise ValueError("Old R5-WOB checkpoint provenance is not explicitly rejected.")
    metrics = json.loads((output_dir / "r5_xgame_metrics.json").read_text(encoding="utf-8"))
    for field in (
        "auroc",
        "auprc",
        "f1",
        "precision",
        "recall",
        "fpr_at_95_tpr",
        "balanced_accuracy",
    ):
        if field not in metrics:
            raise ValueError(f"Missing binary metric: {field}")
    markers = list(output_dir.glob("stage_*.json"))
    if not markers:
        raise ValueError("No stage markers found.")
    return {
        "status": "r5_xgame_output_validated",
        "role_counts": counts,
        "output_dir": str(output_dir),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate an R5-XGame completed output bundle.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--frozen-manifest", type=Path, default=Path("configs/wob_protocol/r5_xgame_split.csv")
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(json.dumps(validate_output_dir(args.output_dir, args.frozen_manifest), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
