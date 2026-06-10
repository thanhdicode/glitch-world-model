from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from glitch_detection.evaluate import evaluate_scores

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ARTIFACTS = (
    "protocol_audit.json",
    "training_metadata.json",
    "validation_scores.csv",
    "phase6e_summary.json",
)
REQUIRED_SCORE_FIELDS = {
    "clip_id",
    "source",
    "clip_dir",
    "start_frame",
    "end_frame",
    "score",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _validate_required_artifacts(artifact_root: Path) -> dict[str, Path]:
    paths = {name: artifact_root / name for name in REQUIRED_ARTIFACTS}
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required artifact(s): {', '.join(missing)}")
    return paths


def _read_and_validate_scores(path: Path) -> tuple[list[dict[str, str]], int]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_SCORE_FIELDS - fields)
        if missing:
            raise ValueError(f"validation_scores.csv is missing fields: {', '.join(missing)}")
        rows = list(reader)
    invalid_count = 0
    for row in rows:
        try:
            value = float(row["score"])
        except (TypeError, ValueError):
            invalid_count += 1
            continue
        if not math.isfinite(value):
            invalid_count += 1
    if invalid_count:
        raise ValueError(
            f"validation_scores.csv contains {invalid_count} non-numeric or non-finite scores."
        )
    return rows, invalid_count


def _write_report(summary: dict[str, Any], output_path: Path) -> Path:
    lines = [
        "# Phase 6E Kaggle Artifact Validation",
        "",
        f"- Status: `{summary['status']}`",
        f"- Device: `{summary['device']}`",
        f"- Validation rows: `{summary['validation_row_count']}`",
        f"- NaN/non-finite scores: `{summary['nan_or_non_finite_score_count']}`",
        f"- Cross-split groups: `{summary['cross_split_group_count']}`",
        f"- Test materialized: `{str(summary['test_materialized']).lower()}`",
        f"- Test scored: `{str(summary['test_scored']).lower()}`",
        f"- Validation metrics generated: `{str(summary['validation_metrics_generated']).lower()}`",
        "",
        "This validates a Conv3D video autoencoder learned-baseline artifact package only. "
        "It does not establish locked-test performance, LeWorldModel integration, or JEPA.",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def ingest_phase6e_kaggle_artifacts(
    artifact_root: Path,
    output_root: Path,
    expected_validation_rows: int = 1071,
    require_cuda: bool = True,
    labels_path: Path | None = None,
) -> dict[str, Any]:
    paths = _validate_required_artifacts(artifact_root)
    audit = _read_json(paths["protocol_audit.json"])
    metadata = _read_json(paths["training_metadata.json"])
    phase_summary = _read_json(paths["phase6e_summary.json"])
    rows, invalid_count = _read_and_validate_scores(paths["validation_scores.csv"])

    device = str(metadata.get("device", ""))
    if require_cuda and "cuda" not in device.lower():
        raise ValueError(
            f"Strict CUDA validation requires a CUDA device, got: {device or 'missing'}"
        )
    if len(rows) != expected_validation_rows:
        raise ValueError(
            f"Expected {expected_validation_rows} validation score rows, found {len(rows)}."
        )
    cross_split_group_count = int(audit.get("leakage_audit", {}).get("cross_split_group_count", -1))
    if cross_split_group_count != 0:
        raise ValueError(
            f"Protocol audit must report zero cross-split groups, got {cross_split_group_count}."
        )
    test_materialized = bool(
        audit.get("test_materialized", False) or phase_summary.get("test_materialized", False)
    )
    test_scored = bool(audit.get("test_scored", False) or phase_summary.get("test_scored", False))
    if test_materialized:
        raise ValueError("Phase 6E artifact package must keep test_materialized=false.")
    if test_scored:
        raise ValueError("Phase 6E artifact package must keep test_scored=false.")

    output_root.mkdir(parents=True, exist_ok=True)
    metrics_path = output_root / "validation_metrics.json"
    validation_metrics_generated = labels_path is not None
    if labels_path is not None:
        if not labels_path.is_file():
            raise FileNotFoundError(f"Missing validation labels: {labels_path}")
        evaluate_scores(
            paths["validation_scores.csv"],
            labels_path,
            metrics_path,
            allow_fit_threshold=True,
        )

    summary: dict[str, Any] = {
        "status": "artifact validation complete",
        "artifact_root": str(artifact_root),
        "device": device,
        "epoch_losses": metadata.get("epoch_losses", []),
        "validation_row_count": len(rows),
        "expected_validation_row_count": expected_validation_rows,
        "nan_or_non_finite_score_count": invalid_count,
        "cross_split_group_count": cross_split_group_count,
        "test_materialized": test_materialized,
        "test_scored": test_scored,
        "validation_metrics_generated": validation_metrics_generated,
        "validation_metrics_path": str(metrics_path) if validation_metrics_generated else None,
        "claim_status": "engineering artifact validated; locked test untouched",
    }
    summary_path = output_root / "artifact_validation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_report(summary, output_root / "artifact_validation_report.md")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate downloaded Phase 6E Kaggle artifacts.")
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "outputs" / "tempglitch_phase6e" / "seed_42" / "ingested",
    )
    parser.add_argument("--expected-validation-rows", type=int, default=1071)
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--labels", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    summary = ingest_phase6e_kaggle_artifacts(
        artifact_root=args.artifact_root,
        output_root=args.output_root,
        expected_validation_rows=args.expected_validation_rows,
        require_cuda=not args.allow_cpu,
        labels_path=args.labels,
    )
    print(f"Phase 6E artifact status: {summary['status']}")
    print(f"Device: {summary['device']}")
    print(f"Validation rows: {summary['validation_row_count']}")
    print(f"Cross-split groups: {summary['cross_split_group_count']}")
    print(f"Test scored: {summary['test_scored']}")
    print(f"Report: {args.output_root / 'artifact_validation_report.md'}")


if __name__ == "__main__":
    main()
