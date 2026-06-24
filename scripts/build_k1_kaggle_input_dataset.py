from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from glitch_detection.manifest import ClipRecord, read_manifest, write_manifest  # noqa: E402
from glitch_detection.neural_protocol import (  # noqa: E402
    prepare_neural_partitions,
    rebase_clip_records,
)
from glitch_detection.splits import (  # noqa: E402
    GroupedSplitRecord,
    read_grouped_split_csv,
    validate_no_group_leakage,
)

DEFAULT_SPLIT_SOURCE = ROOT / "outputs" / "gate3" / "tempglitch" / "split.csv"
K1_DATASET_NAME = "lewm-k1-tempglitch-inputs"
MANIFEST_NAME = "combined_manifest.csv"
GROUPED_SPLIT_NAME = "grouped_split.csv"
AUDIT_NAME = "k1_input_audit.json"
README_NAME = "README_KAGGLE.md"
COMMAND_NAME = "RUN_K1_COMMAND.txt"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_file(path: Path, description: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {description}: {path}")
    return path


def _load_split_rows(path: Path) -> list[dict[str, str]]:
    with _require_file(path, "K1 split source").open(
        "r", newline="", encoding="utf-8-sig"
    ) as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "source",
        "pair_id",
        "category",
        "label",
        "split",
        "materialize",
    }
    if not rows:
        raise ValueError("K1 split source is empty.")
    missing = sorted(required - set(rows[0]))
    if missing:
        raise ValueError(f"K1 split source is missing required fields: {', '.join(missing)}")
    return rows


def _select_split_rows(
    manifest_records: list[ClipRecord],
    split_rows: list[dict[str, str]],
    *,
    required_train_normal: int = 36,
    required_validation_normal: int = 14,
    required_validation_buggy: int = 22,
) -> list[dict[str, str]]:
    manifest_sources = {record.source for record in manifest_records}
    selected = [
        row
        for row in split_rows
        if row["source"] in manifest_sources
        and row["materialize"].lower() == "true"
        and row["split"] in {"train", "validation"}
    ]
    if len({row["source"] for row in selected}) != len(selected):
        raise ValueError("Selected K1 split rows contain duplicate sources.")
    counts = Counter((row["split"], row["label"]) for row in selected)
    actual_train_normal = counts[("train", "Normal")]
    actual_validation_normal = counts[("validation", "Normal")]
    actual_validation_buggy = counts[("validation", "Buggy")]
    if actual_train_normal != required_train_normal:
        raise ValueError(
            f"K1 split requires {required_train_normal} train-normal sources, found {actual_train_normal}."
        )
    if actual_validation_normal != required_validation_normal:
        raise ValueError(
            "K1 split requires "
            f"{required_validation_normal} validation-normal sources, found {actual_validation_normal}."
        )
    if actual_validation_buggy != required_validation_buggy:
        raise ValueError(
            "K1 split requires "
            f"{required_validation_buggy} validation-buggy sources, found {actual_validation_buggy}."
        )
    if counts[("validation", "Normal")] == 0 or counts[("validation", "Buggy")] == 0:
        raise ValueError("K1 validation split must contain both normal and buggy sources.")
    return sorted(selected, key=lambda row: row["source"])


def _build_grouped_split_records(rows: list[dict[str, str]]) -> list[GroupedSplitRecord]:
    records = [
        GroupedSplitRecord(
            source=row["source"],
            category=row["category"],
            label=row["label"],
            split=row["split"],
            pair_id_heuristic=row["pair_id"],
        )
        for row in rows
    ]
    audit = validate_no_group_leakage(records)
    if audit["cross_split_group_count"] != 0:
        raise ValueError("K1 grouped split has cross-split leakage.")
    return records


def _write_grouped_split(path: Path, records: list[GroupedSplitRecord]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source", "category", "label", "split", "pair_id_heuristic"],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "source": record.source,
                    "category": record.category,
                    "label": record.label,
                    "split": record.split,
                    "pair_id_heuristic": record.pair_id_heuristic,
                }
            )
    return path


def _portable_clip_dir(record: ClipRecord) -> str:
    return str(Path("clips_root") / record.source / "clips" / record.clip_id).replace("\\", "/")


def _build_combined_manifest(
    manifest_records: list[ClipRecord], selected_sources: set[str]
) -> list[ClipRecord]:
    selected = [
        ClipRecord(
            clip_id=record.clip_id,
            source=record.source,
            clip_dir=_portable_clip_dir(record),
            start_frame=record.start_frame,
            end_frame=record.end_frame,
            frame_count=record.frame_count,
            fps=record.fps,
        )
        for record in manifest_records
        if record.source in selected_sources
    ]
    if not selected:
        raise ValueError("Selected combined manifest is empty.")
    return selected


def _resolve_source_clip_dir(record: ClipRecord, source_roots: list[Path]) -> Path:
    direct = Path(record.clip_dir)
    candidates = [
        direct,
        *[root / record.source / "clips" / record.clip_id for root in source_roots],
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        f"Could not resolve clip directory for {record.clip_id}. Tried: "
        + ", ".join(str(path) for path in candidates)
    )


def _iter_frame_files(clip_dir: Path) -> list[Path]:
    files = sorted(
        path
        for path in clip_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )
    if not files:
        raise ValueError(f"Clip directory contains no readable frame files: {clip_dir}")
    return files


def _link_or_copy_file(src: Path, dst: Path) -> str:
    try:
        if dst.exists():
            dst.unlink()
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def _materialize_clips(
    original_records: list[ClipRecord],
    portable_records: list[ClipRecord],
    source_roots: list[Path],
    clips_root: Path,
) -> dict[str, Any]:
    clips_root.mkdir(parents=True, exist_ok=True)
    copied_clip_folders = 0
    total_frame_count = 0
    missing_clip_count = 0
    file_actions: Counter[str] = Counter()
    for original, portable in zip(original_records, portable_records):
        source_clip_dir = _resolve_source_clip_dir(original, source_roots)
        frame_files = _iter_frame_files(source_clip_dir)
        destination_dir = clips_root / portable.source / "clips" / portable.clip_id
        destination_dir.mkdir(parents=True, exist_ok=True)
        for frame_file in frame_files:
            file_actions[_link_or_copy_file(frame_file, destination_dir / frame_file.name)] += 1
        copied_clip_folders += 1
        total_frame_count += len(frame_files)
        if not destination_dir.is_dir():
            missing_clip_count += 1
    return {
        "copied_clip_folders": copied_clip_folders,
        "total_frame_count": total_frame_count,
        "missing_clip_count": missing_clip_count,
        "file_action_counts": dict(sorted(file_actions.items())),
    }


def _validate_packaged_dataset(
    manifest_path: Path,
    grouped_split_path: Path,
    clips_root: Path,
) -> dict[str, Any]:
    manifest_records = read_manifest(manifest_path)
    split_records = read_grouped_split_csv(grouped_split_path)
    rebased = rebase_clip_records(manifest_records, clips_root)
    partitions = prepare_neural_partitions(rebased, split_records)
    missing = [record.clip_id for record in rebased if not Path(record.clip_dir).is_dir()]
    if missing:
        raise FileNotFoundError(f"Packaged clips_root is missing {len(missing)} clip folder(s).")
    if not partitions.validation:
        raise ValueError("Packaged K1 dataset has an empty validation partition.")
    validation_labels = {row.label for row in split_records if row.split == "validation"}
    if validation_labels != {"Normal", "Buggy"}:
        raise ValueError(
            "Packaged K1 dataset must keep a two-class validation split; found "
            + ", ".join(sorted(validation_labels))
        )
    return {
        "train_normal_clip_count": len(partitions.train_normal),
        "validation_clip_count": len(partitions.validation),
        "test_clip_count": len(partitions.test),
        "leakage_audit": partitions.audit,
    }


def _kaggle_command(dataset_name: str = K1_DATASET_NAME) -> str:
    return "\n".join(
        [
            "python scripts/run_kaggle_learned_baselines.py \\",
            f"  --manifest /kaggle/input/{dataset_name}/combined_manifest.csv \\",
            f"  --split /kaggle/input/{dataset_name}/grouped_split.csv \\",
            f"  --clips-root /kaggle/input/{dataset_name}/clips_root \\",
            "  --output-root /kaggle/working/learned_baselines_k1 \\",
            "  --device cuda \\",
            "  --image-size 64 \\",
            "  --clip-length 16 \\",
            "  --batch-size 4 \\",
            "  --epochs 8 \\",
            "  --learning-rate 1e-3 \\",
            "  --seed 42 \\",
            "  --num-workers 2 \\",
            "  --video-transformer-batch-size 2 \\",
            "  --video-transformer-learning-rate 1e-4 \\",
            "  --video-transformer-epochs 1",
        ]
    )


def _write_readme(path: Path, audit: dict[str, Any], dataset_name: str = K1_DATASET_NAME) -> Path:
    text = "\n".join(
        [
            "# K1 TempGlitch Kaggle Inputs",
            "",
            "This dataset packages the frozen non-locked TempGlitch inputs for K1 learned baselines.",
            "",
            "Included files:",
            "- combined_manifest.csv",
            "- grouped_split.csv",
            "- k1_input_audit.json",
            "- README_KAGGLE.md",
            "- RUN_K1_COMMAND.txt",
            "- clips_root/",
            "",
            f"Suggested Kaggle Dataset name: `{dataset_name}`",
            "",
            "Expected Kaggle paths:",
            f"- /kaggle/input/{dataset_name}/combined_manifest.csv",
            f"- /kaggle/input/{dataset_name}/grouped_split.csv",
            f"- /kaggle/input/{dataset_name}/clips_root",
            "",
            "Counts from the local audit:",
            f"- Split sources: {audit['split_source_count']}",
            f"- Train-normal sources: {audit['train_normal_source_count']}",
            f"- Validation-normal sources: {audit['validation_normal_source_count']}",
            f"- Validation-buggy sources: {audit['validation_buggy_source_count']}",
            f"- Selected clip records: {audit['selected_clip_record_count']}",
            f"- Copied clip folders: {audit['copied_clip_folders']}",
            f"- Total frame count: {audit['total_frame_count']}",
            "",
            "Exact K1 command:",
            "```bash",
            _kaggle_command(dataset_name),
            "```",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return path


def _zip_package(package_root: Path, zip_path: Path) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(
        zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
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


def _write_sha256_sidecar(path: Path) -> Path:
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar.write_text(f"{sha256_file(path)}  {path.name}\n", encoding="utf-8")
    return sidecar


def build_k1_kaggle_input_dataset(
    *,
    manifest_path: Path,
    split_source_path: Path,
    source_roots: list[Path],
    output_root: Path,
    package_name: str = K1_DATASET_NAME,
    required_train_normal: int = 36,
    required_validation_normal: int = 14,
    required_validation_buggy: int = 22,
) -> dict[str, Any]:
    manifest_records = read_manifest(_require_file(manifest_path, "processed TempGlitch manifest"))
    split_rows = _load_split_rows(split_source_path)
    selected_split_rows = _select_split_rows(
        manifest_records,
        split_rows,
        required_train_normal=required_train_normal,
        required_validation_normal=required_validation_normal,
        required_validation_buggy=required_validation_buggy,
    )
    selected_sources = {row["source"] for row in selected_split_rows}
    grouped_split_records = _build_grouped_split_records(selected_split_rows)
    original_selected_records = [
        record for record in manifest_records if record.source in selected_sources
    ]
    portable_manifest_records = _build_combined_manifest(manifest_records, selected_sources)
    if len(original_selected_records) != len(portable_manifest_records):
        raise ValueError("Portable manifest size does not match selected source records.")

    package_root = output_root / package_name
    if package_root.exists():
        shutil.rmtree(package_root)
    clips_root = package_root / "clips_root"
    package_root.mkdir(parents=True, exist_ok=True)

    combined_manifest_path = package_root / MANIFEST_NAME
    grouped_split_path = package_root / GROUPED_SPLIT_NAME
    write_manifest(combined_manifest_path, portable_manifest_records)
    _write_grouped_split(grouped_split_path, grouped_split_records)
    copy_stats = _materialize_clips(
        original_selected_records, portable_manifest_records, source_roots, clips_root
    )
    validation = _validate_packaged_dataset(combined_manifest_path, grouped_split_path, clips_root)

    split_counts = Counter((row["split"], row["label"]) for row in selected_split_rows)
    audit = {
        "status": "k1_input_ready",
        "dataset_name": package_name,
        "manifest_source_path": str(manifest_path),
        "split_source_path": str(split_source_path),
        "source_roots": [str(path) for path in source_roots],
        "combined_manifest_path": str(combined_manifest_path),
        "grouped_split_path": str(grouped_split_path),
        "clips_root_path": str(clips_root),
        "split_source_count": len(selected_sources),
        "train_normal_source_count": split_counts[("train", "Normal")],
        "validation_normal_source_count": split_counts[("validation", "Normal")],
        "validation_buggy_source_count": split_counts[("validation", "Buggy")],
        "selected_clip_record_count": len(portable_manifest_records),
        **copy_stats,
        **validation,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    audit_path = package_root / AUDIT_NAME
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    command_text = _kaggle_command(package_name)
    (package_root / COMMAND_NAME).write_text(command_text + "\n", encoding="utf-8")
    _write_readme(package_root / README_NAME, audit, package_name)

    zip_path = output_root / f"{package_name}.zip"
    _zip_package(package_root, zip_path)
    zip_sha_path = _write_sha256_sidecar(zip_path)
    audit["zip_path"] = str(zip_path)
    audit["zip_sha256"] = sha256_file(zip_path)
    audit["zip_sha256_path"] = str(zip_sha_path)
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the Kaggle input package for K1 learned baselines."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--split-source",
        type=Path,
        default=DEFAULT_SPLIT_SOURCE,
        help="Source-level frozen split used to derive the K1 grouped split.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        action="append",
        default=[],
        help="Optional roots used to resolve clip folders as <root>/<source>/clips/<clip_id>.",
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--package-name", default=K1_DATASET_NAME)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    source_roots = [path.resolve() for path in args.source_root]
    audit = build_k1_kaggle_input_dataset(
        manifest_path=args.manifest.resolve(),
        split_source_path=args.split_source.resolve(),
        source_roots=source_roots,
        output_root=args.output_root.resolve(),
        package_name=args.package_name,
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
