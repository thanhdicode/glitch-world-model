from __future__ import annotations

import argparse
import json
import os
import shutil
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from glitch_detection.gate6_data import sha256_file
from glitch_detection.manifest import ClipRecord, read_manifest, write_manifest
from glitch_detection.neural_protocol import prepare_neural_partitions, rebase_clip_records
from glitch_detection.splits import read_grouped_split_csv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FREEZE_ROOT = ROOT / "outputs" / "glitchbench_k2_freeze"
PACKAGE_NAME = "lewm-k2-glitchbench-inputs"
MANIFEST_NAME = "combined_manifest.csv"
GROUPED_SPLIT_NAME = "grouped_split.csv"
PROTOCOL_AUDIT_NAME = "glitchbench_protocol_audit.json"
AUDIT_NAME = "k2_input_audit.json"
README_NAME = "README_KAGGLE.md"
COMMAND_NAME = "RUN_K2_COMMAND.txt"


def _portable_clip_dir(record: ClipRecord) -> str:
    return str(Path("clips_root") / record.source / "clips" / record.clip_id).replace("\\", "/")


def _link_or_copy_file(src: Path, dst: Path) -> str:
    try:
        if dst.exists():
            dst.unlink()
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def _materialize_clips(records: list[ClipRecord], clips_root: Path) -> dict[str, Any]:
    action_counts: Counter[str] = Counter()
    total_frame_count = 0
    for record in records:
        source_clip_dir = Path(record.clip_dir)
        if not source_clip_dir.is_dir():
            raise FileNotFoundError(
                f"Missing source clip directory for K2 package: {source_clip_dir}"
            )
        destination_dir = clips_root / record.source / "clips" / record.clip_id
        destination_dir.mkdir(parents=True, exist_ok=True)
        frame_files = sorted(path for path in source_clip_dir.iterdir() if path.is_file())
        if not frame_files:
            raise ValueError(
                f"GlitchBench clip directory contains no frame files: {source_clip_dir}"
            )
        for frame_file in frame_files:
            action_counts[_link_or_copy_file(frame_file, destination_dir / frame_file.name)] += 1
        total_frame_count += len(frame_files)
    return {
        "copied_clip_count": len(records),
        "total_frame_count": total_frame_count,
        "file_action_counts": dict(sorted(action_counts.items())),
    }


def _validate_package(manifest_path: Path, split_path: Path, clips_root: Path) -> dict[str, Any]:
    manifest_records = rebase_clip_records(read_manifest(manifest_path), clips_root)
    split_records = read_grouped_split_csv(split_path)
    partitions = prepare_neural_partitions(manifest_records, split_records)
    validation_labels = {row.label for row in split_records if row.split == "validation"}
    if validation_labels != {"Normal", "Buggy"}:
        raise ValueError("K2 package validation requires both Normal and Buggy validation rows.")
    return {
        "train_normal_clip_count": len(partitions.train_normal),
        "validation_clip_count": len(partitions.validation),
        "test_clip_count": len(partitions.test),
        "leakage_audit": partitions.audit,
    }


def _kaggle_command(dataset_name: str = PACKAGE_NAME) -> str:
    return "\n".join(
        [
            "python scripts/run_kaggle_glitchbench_benchmark.py \\",
            f"  --manifest /kaggle/input/{dataset_name}/combined_manifest.csv \\",
            f"  --split /kaggle/input/{dataset_name}/grouped_split.csv \\",
            f"  --clips-root /kaggle/input/{dataset_name}/clips_root \\",
            "  --output-root /kaggle/working/glitchbench_k2 \\",
            "  --device cuda",
        ]
    )


def _write_readme(path: Path, audit: dict[str, Any], dataset_name: str) -> Path:
    text = "\n".join(
        [
            "# K2 GlitchBench Kaggle Inputs",
            "",
            "This package contains the bounded, image-level GlitchBench subset inputs for K2.",
            "",
            "Expected Kaggle paths:",
            f"- /kaggle/input/{dataset_name}/combined_manifest.csv",
            f"- /kaggle/input/{dataset_name}/grouped_split.csv",
            f"- /kaggle/input/{dataset_name}/clips_root",
            "",
            "Claim boundary:",
            "- image-level benchmark only",
            "- synthetic normal clips are used",
            "- no temporal-localization claim",
            "- locked test remains closed",
            "",
            "Counts:",
            f"- Train-normal sources: {audit['train_normal_source_count']}",
            f"- Validation-normal sources: {audit['validation_normal_source_count']}",
            f"- Validation-buggy sources: {audit['validation_buggy_source_count']}",
            f"- Total clip records: {audit['selected_clip_record_count']}",
            "",
            "Suggested K2 command:",
            "```bash",
            _kaggle_command(dataset_name),
            "```",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return path


def _zip_package(package_root: Path, zip_path: Path) -> Path:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        for file_path in sorted(package_root.rglob("*")):
            if file_path.is_file():
                archive.write(
                    file_path,
                    str(Path(package_root.name) / file_path.relative_to(package_root)).replace(
                        "\\", "/"
                    ),
                )
    return zip_path


def build_k2_glitchbench_kaggle_dataset(
    *,
    manifest_path: Path,
    split_path: Path,
    protocol_audit_path: Path,
    output_root: Path,
    package_name: str = PACKAGE_NAME,
) -> dict[str, Any]:
    original_records = read_manifest(manifest_path)
    portable_records = [
        ClipRecord(
            clip_id=record.clip_id,
            source=record.source,
            clip_dir=_portable_clip_dir(record),
            start_frame=record.start_frame,
            end_frame=record.end_frame,
            frame_count=record.frame_count,
            fps=record.fps,
        )
        for record in original_records
    ]
    package_root = output_root / package_name
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)
    clips_root = package_root / "clips_root"
    combined_manifest_path = package_root / MANIFEST_NAME
    grouped_split_path = package_root / GROUPED_SPLIT_NAME
    packaged_protocol_audit_path = package_root / PROTOCOL_AUDIT_NAME
    write_manifest(combined_manifest_path, portable_records)
    shutil.copyfile(split_path, grouped_split_path)
    shutil.copyfile(protocol_audit_path, packaged_protocol_audit_path)
    copy_stats = _materialize_clips(original_records, clips_root)
    validation = _validate_package(combined_manifest_path, grouped_split_path, clips_root)
    split_records = read_grouped_split_csv(grouped_split_path)
    split_counts = Counter((row.split, row.label) for row in split_records)
    audit = {
        "status": "k2_input_ready",
        "dataset_name": package_name,
        "combined_manifest_path": str(combined_manifest_path),
        "grouped_split_path": str(grouped_split_path),
        "protocol_audit_path": str(packaged_protocol_audit_path),
        "clips_root_path": str(clips_root),
        "selected_clip_record_count": len(portable_records),
        "train_normal_source_count": split_counts[("train", "Normal")],
        "validation_normal_source_count": split_counts[("validation", "Normal")],
        "validation_buggy_source_count": split_counts[("validation", "Buggy")],
        **copy_stats,
        **validation,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    audit_path = package_root / AUDIT_NAME
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    (package_root / COMMAND_NAME).write_text(_kaggle_command(package_name) + "\n", encoding="utf-8")
    _write_readme(package_root / README_NAME, audit, package_name)
    zip_path = output_root / f"{package_name}.zip"
    _zip_package(package_root, zip_path)
    sha_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    sha_path.write_text(f"{sha256_file(zip_path)}  {zip_path.name}\n", encoding="utf-8")
    audit["zip_path"] = str(zip_path)
    audit["zip_sha256"] = sha256_file(zip_path)
    audit["zip_sha256_path"] = str(sha_path)
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the Kaggle input package for the K2 GlitchBench benchmark."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_FREEZE_ROOT / MANIFEST_NAME)
    parser.add_argument("--split", type=Path, default=DEFAULT_FREEZE_ROOT / GROUPED_SPLIT_NAME)
    parser.add_argument(
        "--protocol-audit",
        type=Path,
        default=DEFAULT_FREEZE_ROOT / PROTOCOL_AUDIT_NAME,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "outputs" / "k2_glitchbench_kaggle_dataset",
    )
    parser.add_argument("--package-name", default=PACKAGE_NAME)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    audit = build_k2_glitchbench_kaggle_dataset(
        manifest_path=args.manifest,
        split_path=args.split,
        protocol_audit_path=args.protocol_audit,
        output_root=args.output_root,
        package_name=args.package_name,
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
