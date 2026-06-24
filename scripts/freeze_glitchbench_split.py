from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from glitch_detection.glitchbench_protocol import (
    GlitchBenchRecord,
    read_glitchbench_manifest,
    summarize_glitchbench_protocol,
    write_protocol_summary,
)
from glitch_detection.manifest import ClipRecord, write_manifest
from glitch_detection.splits import GroupedSplitRecord, write_grouped_split_csv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_ROOT = ROOT / "data" / "raw" / "glitchbench_subset"


def _hash_fraction(seed: int, stratum: str, group_key: str) -> float:
    payload = f"{seed}\0{stratum}\0{group_key}".encode("utf-8")
    return int(hashlib.sha256(payload).hexdigest(), 16) / float(2**256)


def _group_records(records: list[GlitchBenchRecord]) -> dict[str, list[GlitchBenchRecord]]:
    grouped: dict[str, list[GlitchBenchRecord]] = defaultdict(list)
    for record in records:
        grouped[record.group_key].append(record)
    return grouped


def _to_clip_records(records: list[GlitchBenchRecord]) -> list[ClipRecord]:
    return [
        ClipRecord(
            clip_id=record.clip_id,
            source=record.source,
            clip_dir=record.clip_dir,
            start_frame=0,
            end_frame=7,
            frame_count=8,
            fps=1.0,
        )
        for record in records
    ]


def freeze_glitchbench_support(
    records: list[GlitchBenchRecord], *, seed: int, validation_ratio: float
) -> tuple[list[GlitchBenchRecord], list[GroupedSplitRecord], dict[str, Any]]:
    if not 0 < validation_ratio < 1:
        raise ValueError("validation_ratio must be between zero and one.")
    grouped = _group_records(records)
    grouped_by_category: dict[str, list[str]] = defaultdict(list)
    for group_key, group_records in grouped.items():
        labels = {record.mapped_label for record in group_records}
        if labels != {"Normal", "Buggy"}:
            raise ValueError(
                f"GlitchBench group {group_key!r} must contain one Normal and one Buggy row."
            )
        categories = {record.glitch_type for record in group_records}
        if len(categories) != 1:
            raise ValueError(f"GlitchBench group {group_key!r} must stay within one glitch type.")
        grouped_by_category[next(iter(categories))].append(group_key)

    selected_records: list[GlitchBenchRecord] = []
    split_records: list[GroupedSplitRecord] = []
    split_assignments: dict[str, str] = {}
    for category, group_keys in sorted(grouped_by_category.items()):
        ordered = sorted(group_keys, key=lambda key: _hash_fraction(seed, category, key))
        validation_count = max(1, round(len(ordered) * validation_ratio))
        validation_count = min(validation_count, max(1, len(ordered) - 1))
        validation_groups = set(ordered[:validation_count])
        for group_key in ordered:
            split = "validation" if group_key in validation_groups else "train"
            split_assignments[group_key] = split
            for record in grouped[group_key]:
                if split == "train" and record.mapped_label != "Normal":
                    continue
                selected_records.append(record)
                split_records.append(
                    GroupedSplitRecord(
                        source=record.source,
                        category=record.glitch_type,
                        label=record.mapped_label,
                        split=split,
                        pair_id_heuristic=record.group_key,
                    )
                )

    counts = Counter((record.split, record.label) for record in split_records)
    if counts[("train", "Normal")] == 0:
        raise ValueError("GlitchBench freeze requires at least one train Normal source.")
    if counts[("validation", "Normal")] == 0 or counts[("validation", "Buggy")] == 0:
        raise ValueError("GlitchBench validation split must contain both Normal and Buggy rows.")
    audit = {
        "seed": seed,
        "validation_ratio": validation_ratio,
        "selected_source_count": len(split_records),
        "group_count": len(grouped),
        "train_normal_source_count": counts[("train", "Normal")],
        "validation_normal_source_count": counts[("validation", "Normal")],
        "validation_buggy_source_count": counts[("validation", "Buggy")],
        "split_assignments": split_assignments,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    return selected_records, split_records, audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Freeze a deterministic leakage-aware GlitchBench subset split."
    )
    parser.add_argument(
        "--records",
        type=Path,
        default=DEFAULT_INPUT_ROOT / "glitchbench_records.csv",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "outputs" / "glitchbench_k2_freeze",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--validation-ratio", type=float, default=0.4)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    records = read_glitchbench_manifest(args.records)
    selected_records, split_records, freeze_audit = freeze_glitchbench_support(
        records,
        seed=args.seed,
        validation_ratio=args.validation_ratio,
    )
    output_root = args.output_root
    output_root.mkdir(parents=True, exist_ok=True)
    combined_manifest_path = output_root / "combined_manifest.csv"
    grouped_split_path = output_root / "grouped_split.csv"
    protocol_audit_path = output_root / "glitchbench_protocol_audit.json"
    write_manifest(combined_manifest_path, _to_clip_records(selected_records))
    write_grouped_split_csv(grouped_split_path, split_records, seed=args.seed)
    summary = summarize_glitchbench_protocol(args.records, grouped_split_path)
    summary["freeze"] = freeze_audit
    summary["paths"] = {
        "records_path": str(args.records),
        "combined_manifest_path": str(combined_manifest_path),
        "grouped_split_path": str(grouped_split_path),
    }
    write_protocol_summary(protocol_audit_path, summary)
    print(
        json.dumps(
            {
                "combined_manifest": str(combined_manifest_path),
                "grouped_split": str(grouped_split_path),
                "protocol_audit": str(protocol_audit_path),
                **freeze_audit,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
