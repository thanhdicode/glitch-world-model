from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path, PurePosixPath
from typing import Any

from glitch_detection.glitchbench_protocol import (
    validate_glitchbench_manifest,
    validate_glitchbench_split,
)
from glitch_detection.manifest import ClipRecord, read_manifest
from glitch_detection.splits import read_grouped_split_csv

REQUIRED_FILES = {
    "combined_manifest.csv",
    "grouped_split.csv",
    "glitchbench_protocol_audit.json",
    "k2_input_audit.json",
    "README_KAGGLE.md",
    "RUN_K2_COMMAND.txt",
}


def _resolve_downloaded_kaggle_path(path_text: str, package_root: Path) -> Path:
    candidate = Path(path_text)
    if candidate.exists():
        return candidate
    posix_parts = PurePosixPath(path_text).parts
    if "clips_root" in posix_parts:
        return package_root.joinpath(*posix_parts[posix_parts.index("clips_root") :])
    if "combined_manifest.csv" in posix_parts:
        return package_root / "combined_manifest.csv"
    if "grouped_split.csv" in posix_parts:
        return package_root / "grouped_split.csv"
    return candidate


def _protocol_manifest_from_package(
    package_root: Path, combined_manifest: list[ClipRecord], split_path: Path
) -> Path:
    split_records = read_grouped_split_csv(split_path)
    split_by_source = {row.source: row for row in split_records}
    protocol_manifest_path = package_root / "_validator_glitchbench_records.csv"
    rows: list[dict[str, str]] = []
    for record in combined_manifest:
        split_row = split_by_source[record.source]
        clip_dir = _resolve_downloaded_kaggle_path(record.clip_dir, package_root)
        frame_files = sorted(path for path in clip_dir.iterdir() if path.is_file())
        if not frame_files:
            raise FileNotFoundError(f"Packaged clip directory contains no frame files: {clip_dir}")
        rows.append(
            {
                "source": record.source,
                "clip_id": record.clip_id,
                "clip_dir": str(clip_dir),
                "image_path": str(frame_files[0]),
                "record_id": split_row.pair_id_heuristic,
                "reddit_id": split_row.pair_id_heuristic,
                "game": split_row.category,
                "glitch_type": split_row.category,
                "source_domain": "packaged_glitchbench_subset",
                "raw_label": ("synthetic_normal" if split_row.label == "Normal" else "glitch"),
                "mapped_label": split_row.label,
                "group_key": split_row.pair_id_heuristic,
                "synthetic_normal": str(split_row.label == "Normal").lower(),
                "temporal_label_available": "false",
            }
        )
    with protocol_manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return protocol_manifest_path


def validate_glitchbench_bundle(package_root: Path) -> dict[str, Any]:
    missing = sorted(name for name in REQUIRED_FILES if not (package_root / name).is_file())
    if missing:
        raise FileNotFoundError(f"GlitchBench K2 package is incomplete: {missing}")
    combined_manifest_path = package_root / "combined_manifest.csv"
    split_path = package_root / "grouped_split.csv"
    protocol_audit_path = package_root / "glitchbench_protocol_audit.json"
    protocol = json.loads(protocol_audit_path.read_text(encoding="utf-8-sig"))
    audit = json.loads((package_root / "k2_input_audit.json").read_text(encoding="utf-8-sig"))
    if audit.get("locked_test_materialized") is not False:
        raise ValueError("K2 input audit must report locked_test_materialized=false.")
    if audit.get("locked_test_scored") is not False:
        raise ValueError("K2 input audit must report locked_test_scored=false.")
    manifest_records = read_manifest(combined_manifest_path)
    rebased_records = [
        ClipRecord(
            clip_id=record.clip_id,
            source=record.source,
            clip_dir=str(_resolve_downloaded_kaggle_path(record.clip_dir, package_root)),
            start_frame=record.start_frame,
            end_frame=record.end_frame,
            frame_count=record.frame_count,
            fps=record.fps,
        )
        for record in manifest_records
    ]
    missing_clips = [
        record.clip_dir for record in rebased_records if not Path(record.clip_dir).is_dir()
    ]
    if missing_clips:
        raise FileNotFoundError(
            f"GlitchBench package is missing {len(missing_clips)} clip folders."
        )
    temp_protocol_manifest = _protocol_manifest_from_package(
        package_root, rebased_records, split_path
    )
    manifest_summary = validate_glitchbench_manifest(temp_protocol_manifest)
    split_summary = validate_glitchbench_split(temp_protocol_manifest, split_path)
    return {
        "status": "validated",
        "package_root": str(package_root),
        "manifest_summary": manifest_summary,
        "split_summary": split_summary,
        "protocol_claim_boundary": protocol.get("limitations", {}).get("claim_boundary")
        or protocol.get("claim_boundary"),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a local or extracted K2 GlitchBench input package."
    )
    parser.add_argument("--package-root", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    receipt = validate_glitchbench_bundle(args.package_root)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
