from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .manifest import read_manifest
from .splits import read_grouped_split_csv, validate_no_group_leakage

GLITCHBENCH_MANIFEST_FIELDS = [
    "source",
    "clip_id",
    "clip_dir",
    "image_path",
    "record_id",
    "reddit_id",
    "game",
    "glitch_type",
    "source_domain",
    "raw_label",
    "mapped_label",
    "group_key",
    "synthetic_normal",
    "temporal_label_available",
]
REQUIRED_GLITCHBENCH_FIELDS = set(GLITCHBENCH_MANIFEST_FIELDS)
ALLOWED_LABELS = {"Normal", "Buggy"}
ALLOWED_SPLITS = {"train", "validation", "test"}
BUGGY_LABEL_ALIASES = {"buggy", "glitch", "glitch_image"}
NORMAL_LABEL_ALIASES = {"normal", "synthetic_normal", "reference_normal"}


class GlitchBenchProtocolError(ValueError):
    """Raised when a GlitchBench benchmark artifact violates the fail-closed protocol."""


@dataclass(frozen=True)
class GlitchBenchRecord:
    source: str
    clip_id: str
    clip_dir: str
    image_path: str
    record_id: str
    reddit_id: str
    game: str
    glitch_type: str
    source_domain: str
    raw_label: str
    mapped_label: str
    group_key: str
    synthetic_normal: bool
    temporal_label_available: bool


def _resolve_manifest_clip_dir(path_text: str, manifest_root: Path) -> Path:
    direct = Path(path_text)
    if direct.is_dir():
        return direct
    relative = manifest_root / path_text
    if relative.is_dir():
        return relative
    posix_parts = PurePosixPath(path_text).parts
    if "clips_root" in posix_parts:
        rebased = manifest_root / Path(*posix_parts[posix_parts.index("clips_root") :])
        if rebased.is_dir():
            return rebased
    return direct


def map_glitchbench_label(raw_label: str, *, synthetic_normal: bool | None = None) -> str:
    label = raw_label.strip().lower()
    if synthetic_normal is True:
        if label and label not in NORMAL_LABEL_ALIASES:
            raise GlitchBenchProtocolError(
                f"Synthetic-normal GlitchBench rows must use a normal alias, got {raw_label!r}."
            )
        return "Normal"
    if label in NORMAL_LABEL_ALIASES:
        return "Normal"
    if label in BUGGY_LABEL_ALIASES:
        return "Buggy"
    raise GlitchBenchProtocolError(f"Unsupported or ambiguous GlitchBench label: {raw_label!r}.")


def write_glitchbench_manifest(path: Path, records: list[GlitchBenchRecord]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=GLITCHBENCH_MANIFEST_FIELDS)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["synthetic_normal"] = str(record.synthetic_normal).lower()
            row["temporal_label_available"] = str(record.temporal_label_available).lower()
            writer.writerow(row)
    return path


def read_glitchbench_manifest(path: Path) -> list[GlitchBenchRecord]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise GlitchBenchProtocolError("GlitchBench manifest is empty.")
    missing = REQUIRED_GLITCHBENCH_FIELDS - set(rows[0])
    if missing:
        raise GlitchBenchProtocolError(
            f"GlitchBench manifest missing required fields: {sorted(missing)}"
        )
    records: list[GlitchBenchRecord] = []
    for row in rows:
        synthetic_normal = str(row["synthetic_normal"]).strip().lower()
        temporal_available = str(row["temporal_label_available"]).strip().lower()
        records.append(
            GlitchBenchRecord(
                source=row["source"].strip(),
                clip_id=row["clip_id"].strip(),
                clip_dir=row["clip_dir"].strip(),
                image_path=row["image_path"].strip(),
                record_id=row["record_id"].strip(),
                reddit_id=row["reddit_id"].strip(),
                game=row["game"].strip(),
                glitch_type=row["glitch_type"].strip(),
                source_domain=row["source_domain"].strip(),
                raw_label=row["raw_label"].strip(),
                mapped_label=row["mapped_label"].strip(),
                group_key=row["group_key"].strip(),
                synthetic_normal=synthetic_normal == "true",
                temporal_label_available=temporal_available == "true",
            )
        )
    return records


def validate_glitchbench_manifest(path: Path) -> dict[str, Any]:
    records = read_glitchbench_manifest(path)
    label_counts = {"Normal": 0, "Buggy": 0}
    unique_groups: set[str] = set()
    missing_clip_dirs: list[str] = []
    missing_images: list[str] = []
    temporal_true_count = 0
    for record in records:
        for field_name in (
            "source",
            "clip_id",
            "clip_dir",
            "image_path",
            "record_id",
            "reddit_id",
            "game",
            "glitch_type",
            "source_domain",
            "group_key",
        ):
            if not getattr(record, field_name):
                raise GlitchBenchProtocolError(
                    f"GlitchBench rows require non-empty {field_name}; got {record!r}"
                )
        mapped = map_glitchbench_label(
            record.raw_label, synthetic_normal=bool(record.synthetic_normal)
        )
        if record.mapped_label != mapped:
            raise GlitchBenchProtocolError(
                f"Manifest mapped_label mismatch for {record.source}: "
                f"{record.mapped_label!r} vs expected {mapped!r}."
            )
        if record.mapped_label not in ALLOWED_LABELS:
            raise GlitchBenchProtocolError(
                f"GlitchBench mapped label must be Normal/Buggy, got {record.mapped_label!r}."
            )
        if record.synthetic_normal != (record.mapped_label == "Normal"):
            raise GlitchBenchProtocolError(
                f"Synthetic-normal flag mismatch for {record.source}: "
                "Normal rows must be synthetic and Buggy rows must not be."
            )
        if not Path(record.clip_dir).is_dir():
            missing_clip_dirs.append(record.clip_dir)
        if not Path(record.image_path).is_file():
            missing_images.append(record.image_path)
        label_counts[record.mapped_label] += 1
        unique_groups.add(record.group_key)
        if record.temporal_label_available:
            temporal_true_count += 1
    if missing_clip_dirs:
        raise GlitchBenchProtocolError(
            f"GlitchBench manifest references {len(missing_clip_dirs)} missing clip_dir values."
        )
    if missing_images:
        raise GlitchBenchProtocolError(
            f"GlitchBench manifest references {len(missing_images)} missing image_path values."
        )
    if label_counts["Normal"] == 0 or label_counts["Buggy"] == 0:
        raise GlitchBenchProtocolError(
            "GlitchBench manifest must contain both synthetic Normal and Buggy rows."
        )
    if temporal_true_count:
        raise GlitchBenchProtocolError(
            "GlitchBench protocol expects temporal_label_available=false for every row."
        )
    return {
        "record_count": len(records),
        "group_count": len(unique_groups),
        "label_counts": label_counts,
        "synthetic_normal_count": sum(record.synthetic_normal for record in records),
        "temporal_label_available": False,
        "temporal_claim_allowed": False,
        "image_level_only": True,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def validate_glitchbench_split(manifest_path: Path, split_path: Path) -> dict[str, Any]:
    manifest_records = read_glitchbench_manifest(manifest_path)
    split_records = read_grouped_split_csv(split_path)
    manifest_by_source = {record.source: record for record in manifest_records}
    split_sources = {record.source for record in split_records}
    if split_sources - set(manifest_by_source):
        raise GlitchBenchProtocolError("Grouped split references sources missing from manifest.")
    if not split_records:
        raise GlitchBenchProtocolError("Grouped split is empty.")
    for row in split_records:
        if row.split not in ALLOWED_SPLITS:
            raise GlitchBenchProtocolError(f"Unsupported GlitchBench split: {row.split!r}.")
        if row.label not in ALLOWED_LABELS:
            raise GlitchBenchProtocolError(f"Unsupported split label: {row.label!r}.")
        manifest_row = manifest_by_source[row.source]
        if row.label != manifest_row.mapped_label:
            raise GlitchBenchProtocolError(
                f"Split label mismatch for source {row.source}: "
                f"{row.label!r} vs {manifest_row.mapped_label!r}."
            )
        if row.pair_id_heuristic != manifest_row.group_key:
            raise GlitchBenchProtocolError(
                f"Split grouping mismatch for source {row.source}: "
                f"{row.pair_id_heuristic!r} vs {manifest_row.group_key!r}."
            )
        if row.split == "train" and row.label != "Normal":
            raise GlitchBenchProtocolError("Train split may contain only synthetic Normal rows.")
    leakage = validate_no_group_leakage(split_records)
    if leakage["cross_split_group_count"] != 0:
        raise GlitchBenchProtocolError("Grouped split contains cross-split leakage groups.")
    validation_labels = {row.label for row in split_records if row.split == "validation"}
    if validation_labels != {"Normal", "Buggy"}:
        raise GlitchBenchProtocolError("Validation split must contain both Normal and Buggy rows.")
    combined_manifest = (
        read_manifest(manifest_path.with_name("combined_manifest.csv"))
        if manifest_path.with_name("combined_manifest.csv").is_file()
        else []
    )
    if combined_manifest:
        manifest_root = manifest_path.parent
        missing_clip_dirs = [
            record.clip_dir
            for record in combined_manifest
            if not _resolve_manifest_clip_dir(record.clip_dir, manifest_root).is_dir()
        ]
        if missing_clip_dirs:
            raise GlitchBenchProtocolError(
                f"Combined manifest references {len(missing_clip_dirs)} missing clip_dir values."
            )
    return {
        "split_source_count": len(split_records),
        "train_source_count": sum(row.split == "train" for row in split_records),
        "validation_source_count": sum(row.split == "validation" for row in split_records),
        "test_source_count": sum(row.split == "test" for row in split_records),
        "validation_label_counts": {
            label: sum(row.split == "validation" and row.label == label for row in split_records)
            for label in sorted(ALLOWED_LABELS)
        },
        "leakage_audit": leakage,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def summarize_glitchbench_protocol(
    manifest_path: Path, split_path: Path | None = None
) -> dict[str, Any]:
    summary = {"manifest": validate_glitchbench_manifest(manifest_path)}
    if split_path is not None:
        summary["split"] = validate_glitchbench_split(manifest_path, split_path)
    summary["limitations"] = {
        "image_level_only": True,
        "temporal_labels_available": False,
        "synthetic_normal_used": True,
        "claim_boundary": (
            "GlitchBench subset rows are image-level and this repo constructs synthetic normal "
            "clips for a leakage-aware train-normal protocol. No temporal-localization claim is "
            "supported by this benchmark package."
        ),
    }
    return summary


def write_protocol_summary(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
