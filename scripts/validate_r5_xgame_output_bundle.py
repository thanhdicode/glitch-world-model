"""Fail-closed validator for a completed R5-XGame output directory or tarball."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from glitch_detection.r5_xgame_protocol import (
    BUGGY_EVAL_ROLE,
    CALIBRATION_ROLE,
    NORMAL_EVAL_ROLE,
    TRAIN_ROLE,
    validate_r5_xgame_manifest,
)

EXPECTED_ROLE_COUNTS = {
    TRAIN_ROLE: 36,
    CALIBRATION_ROLE: 12,
    NORMAL_EVAL_ROLE: 12,
    BUGGY_EVAL_ROLE: 60,
}
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
REQUIRED_STAGE_MARKERS = (
    "stage_preflight.json",
    "stage_materialize.json",
    "stage_baseline_score.json",
    "stage_train_lewm.json",
    "stage_lewm_score.json",
    "stage_aggregate_episode.json",
    "stage_calibrate_thresholds.json",
    "stage_evaluate_binary.json",
    "stage_bootstrap_ci.json",
    "stage_package.json",
)
REQUIRED_METRICS = (
    "auroc",
    "auprc",
    "f1",
    "precision",
    "recall",
    "fpr_at_95_tpr",
    "balanced_accuracy",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_sha256(sidecar: Path) -> str:
    tokens = sidecar.read_text(encoding="utf-8-sig").strip().split()
    if not tokens:
        raise ValueError(f"Invalid SHA256 sidecar: {sidecar}")
    return tokens[0].lower()


def _verify_sidecar(path: Path, sidecar: Path) -> dict[str, Any]:
    expected = _expected_sha256(sidecar)
    actual = sha256(path)
    if expected != actual:
        raise ValueError(f"SHA256 mismatch for {path}: expected {expected}, found {actual}")
    return {"path": str(path), "sha256": actual, "sha256_verified": True}


def _safe_extract(tarball: Path, dest: Path) -> Path:
    destination = dest.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tarball, "r:gz") as archive:
        for member in archive.getmembers():
            resolved = (destination / member.name).resolve()
            if not resolved.is_relative_to(destination):
                raise ValueError(f"Path traversal detected in bundle: {member.name}")
            if member.issym() or member.islnk():
                raise ValueError(f"Archive links are not allowed: {member.name}")
            if not (member.isdir() or member.isreg()):
                raise ValueError(f"Unsupported archive member type: {member.name}")
        archive.extractall(destination)
    return destination


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _require_metrics(metrics: dict[str, Any]) -> None:
    for field in REQUIRED_METRICS:
        if field not in metrics or not math.isfinite(float(metrics[field])):
            raise ValueError(f"Missing or non-finite binary metric: {field}")
    if not metrics.get("results"):
        raise ValueError("R5-XGame metrics are missing per-configuration results.")


def _validate_evaluation_classes(output_dir: Path) -> None:
    rows = _read_csv(output_dir / "r5_xgame_episode_scores.csv")
    evaluation_labels = {
        row["label"].lower() for row in rows if row["evaluation_role"] == "evaluation"
    }
    if evaluation_labels != {"normal", "buggy"}:
        raise ValueError("R5-XGame output must contain both evaluation classes.")


def _validate_provenance(provenance: dict[str, Any]) -> None:
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
    if provenance["role_counts"] != EXPECTED_ROLE_COUNTS:
        raise ValueError("R5-XGame provenance role counts do not match the frozen contract.")
    if sorted(int(seed) for seed in provenance["seeds"]) != [42, 43, 44]:
        raise ValueError("R5-XGame provenance must contain fresh seeds 42, 43, and 44.")
    for field in (
        "locked_test_materialized",
        "locked_test_scored",
        "validation_buggy_used_for_fit_select",
    ):
        if provenance.get(field) is not False:
            raise ValueError(f"Unsafe provenance flag: {field}")
    if provenance.get("old_r5_wob_checkpoint_reused") is not False:
        raise ValueError("Old R5-WOB checkpoint provenance is not explicitly rejected.")


def validate_output_dir(
    output_dir: Path, frozen_manifest: Path, *, require_package_files: bool = True
) -> dict[str, object]:
    missing = sorted(name for name in REQUIRED if not (output_dir / name).is_file())
    missing.extend(
        f"r5_xgame_lewm_scores_seed{seed}.csv"
        for seed in (42, 43, 44)
        if not (output_dir / f"r5_xgame_lewm_scores_seed{seed}.csv").is_file()
    )
    if require_package_files:
        missing.extend(
            name
            for name in ("r5_xgame_outputs.tar.gz", "r5_xgame_outputs.tar.gz.sha256")
            if not (output_dir / name).is_file()
        )
    missing.extend(name for name in REQUIRED_STAGE_MARKERS if not (output_dir / name).is_file())
    if missing:
        raise ValueError(f"R5-XGame output is incomplete: {sorted(missing)}")

    manifest = output_dir / "r5_xgame_manifest.csv"
    if sha256(manifest) != sha256(frozen_manifest):
        raise ValueError("Output manifest hash differs from the frozen R5-XGame manifest.")
    counts = validate_r5_xgame_manifest(_read_csv(manifest))
    if counts != EXPECTED_ROLE_COUNTS:
        raise ValueError(f"R5-XGame role counts changed: {counts}")

    metrics = json.loads((output_dir / "r5_xgame_metrics.json").read_text(encoding="utf-8"))
    _require_metrics(metrics)
    _validate_evaluation_classes(output_dir)

    provenance = json.loads((output_dir / "r5_xgame_provenance.json").read_text(encoding="utf-8"))
    _validate_provenance(provenance)

    if require_package_files:
        _verify_sidecar(
            output_dir / "r5_xgame_outputs.tar.gz",
            output_dir / "r5_xgame_outputs.tar.gz.sha256",
        )
    return {
        "status": "r5_xgame_output_validated",
        "role_counts": counts,
        "output_dir": str(output_dir),
        "manifest_sha256": sha256(manifest),
        "metrics_sha256": sha256(output_dir / "r5_xgame_metrics.json"),
    }


def validate_tarball(tarball: Path, sha256_file: Path, frozen_manifest: Path) -> dict[str, object]:
    sidecar = _verify_sidecar(tarball, sha256_file)
    with tempfile.TemporaryDirectory(prefix="r5_xgame_validate_") as tmp:
        root = _safe_extract(tarball, Path(tmp))
        result = validate_output_dir(root, frozen_manifest, require_package_files=False)
    return {"status": "r5_xgame_tarball_validated", "bundle": sidecar, "validator": result}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate an R5-XGame completed output bundle.")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--tarball", type=Path)
    parser.add_argument("--sha256-file", type=Path)
    parser.add_argument(
        "--frozen-manifest", type=Path, default=Path("configs/wob_protocol/r5_xgame_split.csv")
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.tarball is not None or args.sha256_file is not None:
        if args.tarball is None or args.sha256_file is None:
            raise ValueError("--tarball and --sha256-file must be provided together.")
        print(
            json.dumps(
                validate_tarball(args.tarball, args.sha256_file, args.frozen_manifest), indent=2
            )
        )
        return 0
    if args.output_dir is None:
        raise ValueError("Provide --output-dir or a --tarball/--sha256-file pair.")
    print(json.dumps(validate_output_dir(args.output_dir, args.frozen_manifest), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
