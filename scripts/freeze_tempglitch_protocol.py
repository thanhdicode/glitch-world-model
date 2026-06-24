from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from glitch_detection.dataset_protocols import freeze_tempglitch_split, write_frozen_split
from glitch_detection.pairs import infer_tempglitch_pair_id
from glitch_detection.tempglitch import (
    DATASET_ID,
    DATASET_PAGE_URL,
    fetch_all_tempglitch_metadata,
    fetch_tempglitch_dataset_info,
    read_tempglitch_metadata,
    write_tempglitch_metadata,
)

ROOT = Path(__file__).resolve().parents[1]
PHASE_P1_FOLLOWUP_CALIBRATION_EPISODE_IDS = (
    "Godot_Blinking_Normal_106",
    "Godot_Frozen_Animation_Platformer_Normal_107",
    "Godot_Shooting_Error_Normal_101",
    "Godot_Teleportation_TPS_Normal_1",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _exposed_groups(paths: list[Path]) -> tuple[set[str], list[dict[str, str]]]:
    groups: set[str] = set()
    evidence: list[dict[str, str]] = []
    for path in paths:
        for row in read_tempglitch_metadata(path):
            groups.add(f"{row['category']}/{infer_tempglitch_pair_id(row['source'])}")
        evidence.append({"path": str(path), "sha256": _sha256(path)})
    return groups, evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Freeze the full metadata-only TempGlitch split.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "gate3" / "tempglitch",
    )
    parser.add_argument("--exposed-metadata", type=Path, nargs="*", default=[])
    parser.add_argument("--expected-video-count", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    info = fetch_tempglitch_dataset_info()
    samples = fetch_all_tempglitch_metadata()
    if len(samples) != args.expected_video_count:
        raise RuntimeError(
            f"Expected {args.expected_video_count} TempGlitch videos, found {len(samples)}."
        )
    revisions = {sample.dataset_revision for sample in samples}
    if len(revisions) != 1:
        raise RuntimeError(f"TempGlitch rows span multiple revisions: {sorted(revisions)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = write_tempglitch_metadata(args.output_dir, samples)
    exposed, exposed_evidence = _exposed_groups(args.exposed_metadata)
    rows = [
        {
            "source": sample.source_name,
            "episode_id": sample.source_name,
            "pair_id": f"{sample.category}/{infer_tempglitch_pair_id(sample.source_name)}",
            "category": sample.category,
            "label": sample.public_label,
        }
        for sample in samples
    ]
    records = freeze_tempglitch_split(rows, exposed_groups=exposed, seed=args.seed)
    split_path, audit_path, provenance_path = write_frozen_split(
        args.output_dir / "split.csv",
        records,
        seed=args.seed,
        exposed_groups=exposed,
        provenance={
            "dataset_id": DATASET_ID,
            "source_url": DATASET_PAGE_URL,
            "access_date": date.today().isoformat(),
            "dataset_revision": next(iter(revisions)),
            "api_revision": info.get("sha"),
            "license": info.get("cardData", {}).get("license", "unknown"),
            "video_count": len(samples),
            "metadata_sha256": _sha256(metadata_path),
            "exposed_group_count": len(exposed),
            "exposed_metadata_evidence": exposed_evidence,
            "raw_video_materialized_locally": False,
            "phase_p1_followup_calibration_episode_ids": list(
                PHASE_P1_FOLLOWUP_CALIBRATION_EPISODE_IDS
            ),
            "phase_p1_followup_calibration_episode_count": len(
                PHASE_P1_FOLLOWUP_CALIBRATION_EPISODE_IDS
            ),
            "phase_p1_followup_validation_normal_episode_count": 14,
            "phase_p1_followup_evaluation_normal_episode_count": 10,
        },
    )
    print(
        json.dumps(
            {
                "metadata": str(metadata_path),
                "split": str(split_path),
                "audit": str(audit_path),
                "provenance": str(provenance_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
