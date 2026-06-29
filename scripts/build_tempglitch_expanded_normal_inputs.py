"""Build EXPANDED-support TempGlitch Lance inputs for the K-A re-evaluation.

The frozen TempGlitch follow-up uses only ~14 normal episodes total (2 calibration +
12 evaluation). To shrink the wide/overlapping AUROC confidence intervals, this
orchestrator downloads MORE normal (and matching buggy) episodes from the public
TempGlitch dataset and materializes three Lance datasets that the existing R5 and
follow-up runners consume unchanged:

  - tempglitch_train_normal_all_local.lance       (train-normal fit pool)
  - tempglitch_validation_normal_all_local.lance  (calibration + normal-negative eval)
  - tempglitch_validation_buggy_all_local.lance   (buggy-positive eval)

It is a thin, deterministic wrapper around three existing, validated utilities:
  1. download_tempglitch_subset(...)  -> pulls videos + writes metadata.csv
  2. freeze_tempglitch_split(...)     -> assigns train/validation, pair-disjoint
  3. build_tempglitch_lewm_lance      -> materializes each Lance partition

It NEVER touches locked test, never trains, and keeps pair-disjoint leakage = 0 by
delegating the split to the frozen-split logic. Designed to run on Kaggle with
internet ON. Raw videos are written under <output_dir>/videos and the three Lance
datasets under <output_dir>/lance.

Example (target >= 30 normal-negative evaluation episodes -> 5 categories x 35 per group):

    python scripts/build_tempglitch_expanded_normal_inputs.py \
        --output-dir /kaggle/working/tempglitch_expanded \
        --limit-per-group 35 \
        --target-validation-normal-count 34 \
        --target-validation-buggy-count 34 \
        --target-evaluation-normal-count 30 \
        --image-size 112 --frame-stride 4 --max-steps-per-episode 512

The resulting Lance paths are printed as JSON for the K-A run cells to consume.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from glitch_detection.dataset_protocols import (
    FrozenSplitRecord,
    freeze_tempglitch_split,
    write_frozen_split,
)
from glitch_detection.pairs import infer_tempglitch_pair_id
from glitch_detection.tempglitch import (
    DATASET_ID,
    DATASET_PAGE_URL,
    DEFAULT_CATEGORIES,
    download_tempglitch_subset,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _build_split_rows(metadata_path: Path) -> list[dict[str, str]]:
    """Read the downloaded metadata.csv and produce freeze-split input rows."""
    import csv

    rows: list[dict[str, str]] = []
    with metadata_path.open("r", newline="", encoding="utf-8-sig") as handle:
        for record in csv.DictReader(handle):
            source = record["source"]
            category = record.get("category", "")
            label = record.get("public_label") or record.get("label") or ""
            rows.append(
                {
                    "source": source,
                    "episode_id": source,
                    "pair_id": f"{category}/{infer_tempglitch_pair_id(source)}",
                    "category": category,
                    "label": label,
                }
            )
    if not rows:
        raise ValueError(f"No TempGlitch metadata rows parsed from {metadata_path}.")
    return rows


def _split_support_counts(records: list[FrozenSplitRecord]) -> dict[str, int]:
    train_normal = {
        record.episode_id
        for record in records
        if record.split == "train" and record.label == "Normal"
    }
    validation_normal = {
        record.episode_id
        for record in records
        if record.split == "validation" and record.label == "Normal"
    }
    validation_buggy = {
        record.episode_id
        for record in records
        if record.split == "validation" and record.label == "Buggy"
    }
    test_normal = {
        record.episode_id
        for record in records
        if record.split == "test" and record.label == "Normal"
    }
    test_buggy = {
        record.episode_id
        for record in records
        if record.split == "test" and record.label == "Buggy"
    }
    return {
        "train_normal_episode_count": len(train_normal),
        "validation_normal_episode_count": len(validation_normal),
        "validation_buggy_episode_count": len(validation_buggy),
        "test_normal_episode_count": len(test_normal),
        "test_buggy_episode_count": len(test_buggy),
    }


def _raise_if_under_target_support(
    support: dict[str, int],
    *,
    target_validation_normal_count: int,
    target_validation_buggy_count: int,
    target_evaluation_normal_count: int,
    minimum_calibration_normal_count: int,
    allow_under_target_support: bool,
) -> None:
    if allow_under_target_support:
        return
    actual_normal = support["validation_normal_episode_count"]
    actual_buggy = support["validation_buggy_episode_count"]
    normal_support_is_usable = actual_normal >= target_validation_normal_count or (
        actual_normal >= target_evaluation_normal_count + minimum_calibration_normal_count
    )
    if not normal_support_is_usable or actual_buggy < target_validation_buggy_count:
        raise ValueError(
            "Expanded TempGlitch split is below K-A target support: "
            f"validation_normal={actual_normal}/{target_validation_normal_count}, "
            f"validation_buggy={actual_buggy}/{target_validation_buggy_count}, "
            f"evaluation_normal_target={target_evaluation_normal_count} with "
            f"minimum_calibration={minimum_calibration_normal_count}. "
            "Increase --limit-per-group or pass --allow-under-target-support only "
            "when documenting maximum public support."
        )


def _recommended_calibration_normal_count(
    support: dict[str, int],
    *,
    target_evaluation_normal_count: int,
    preferred_calibration_normal_count: int = 4,
) -> int:
    available_for_calibration = (
        support["validation_normal_episode_count"] - target_evaluation_normal_count
    )
    if available_for_calibration < 1:
        return 0
    return min(preferred_calibration_normal_count, available_for_calibration)


def _materialize_lance(
    *,
    metadata: Path,
    split: Path,
    video_root: Path,
    output: Path,
    partition: str,
    label_filter: str | None,
    image_size: int,
    frame_stride: int,
    max_steps: int | None,
    max_episodes: int | None,
    seed: int,
) -> None:
    argv = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "build_tempglitch_lewm_lance.py"),
        "--metadata",
        str(metadata),
        "--split",
        str(split),
        "--video-root",
        str(video_root),
        "--output",
        str(output),
        "--partition",
        partition,
        "--image-size",
        str(image_size),
        "--frame-stride",
        str(frame_stride),
        "--seed",
        str(seed),
    ]
    if max_steps is not None:
        argv += ["--max-steps", str(max_steps)]
    if label_filter is not None:
        argv += ["--label-filter", label_filter]
    if max_episodes is not None:
        argv += ["--max-episodes", str(max_episodes)]
    subprocess.run(argv, check=True)


def build_expanded_inputs(
    *,
    output_dir: Path,
    limit_per_group: int,
    categories: list[str] | None = None,
    image_size: int = 112,
    frame_stride: int = 1,
    max_steps_per_episode: int | None = None,
    train_max_episodes: int | None = None,
    seed: int = 42,
    target_validation_normal_count: int = 34,
    target_validation_buggy_count: int = 34,
    target_evaluation_normal_count: int = 30,
    minimum_calibration_normal_count: int = 1,
    allow_under_target_support: bool = False,
) -> dict[str, object]:
    if limit_per_group < 1:
        raise ValueError("limit_per_group must be >= 1.")
    if (
        target_validation_normal_count < 1
        or target_validation_buggy_count < 1
        or target_evaluation_normal_count < 1
        or minimum_calibration_normal_count < 1
    ):
        raise ValueError("Target support counts must be >= 1.")
    if max_steps_per_episode is not None and max_steps_per_episode < 2:
        raise ValueError("max_steps_per_episode must be >= 2 when provided.")
    if train_max_episodes is not None and train_max_episodes < 1:
        raise ValueError("train_max_episodes must be >= 1 when provided.")
    categories = categories or list(DEFAULT_CATEGORIES)
    output_dir = output_dir.resolve()
    video_dir = output_dir / "videos"
    lance_dir = output_dir / "lance"
    split_dir = output_dir / "split"
    for path in (video_dir, lance_dir, split_dir):
        path.mkdir(parents=True, exist_ok=True)

    # 1) Download an expanded, stratified subset (both labels, all categories).
    samples, metadata_path, _readme = download_tempglitch_subset(
        output_dir=video_dir,
        categories=categories,
        limit_per_group=limit_per_group,
        sample_mode="random-stratified",
        seed=seed,
    )
    normal_count = sum(1 for s in samples if s.public_label.lower() == "normal")
    buggy_count = sum(1 for s in samples if s.public_label.lower() == "buggy")

    # 2) Freeze a pair-disjoint train/validation split (no exposed groups).
    split_rows = _build_split_rows(metadata_path)
    records = freeze_tempglitch_split(split_rows, exposed_groups=set(), seed=seed)
    support = _split_support_counts(records)
    _raise_if_under_target_support(
        support,
        target_validation_normal_count=target_validation_normal_count,
        target_validation_buggy_count=target_validation_buggy_count,
        target_evaluation_normal_count=target_evaluation_normal_count,
        minimum_calibration_normal_count=minimum_calibration_normal_count,
        allow_under_target_support=allow_under_target_support,
    )
    recommended_calibration_normal_count = _recommended_calibration_normal_count(
        support,
        target_evaluation_normal_count=target_evaluation_normal_count,
    )
    split_path, _audit_path, _prov_path = write_frozen_split(
        split_dir / "split.csv",
        records,
        seed=seed,
        exposed_groups=set(),
        provenance={
            "dataset_id": DATASET_ID,
            "source_url": DATASET_PAGE_URL,
            "access_date": date.today().isoformat(),
            "limit_per_group": limit_per_group,
            "categories": categories,
            "expanded_support": True,
            "target_validation_normal_count": target_validation_normal_count,
            "target_validation_buggy_count": target_validation_buggy_count,
            "target_evaluation_normal_count": target_evaluation_normal_count,
            "minimum_calibration_normal_count": minimum_calibration_normal_count,
            "frame_stride": frame_stride,
            "max_steps_per_episode": max_steps_per_episode,
            "train_max_episodes": train_max_episodes,
            "recommended_calibration_normal_count": recommended_calibration_normal_count,
            "allow_under_target_support": allow_under_target_support,
            "split_support": support,
        },
    )

    # 3) Materialize the three Lance datasets the runners expect.
    train_lance = lance_dir / "tempglitch_train_normal_all_local.lance"
    val_normal_lance = lance_dir / "tempglitch_validation_normal_all_local.lance"
    val_buggy_lance = lance_dir / "tempglitch_validation_buggy_all_local.lance"

    _materialize_lance(
        metadata=metadata_path,
        split=split_path,
        video_root=video_dir,
        output=train_lance,
        partition="train",
        label_filter="Normal",
        image_size=image_size,
        frame_stride=frame_stride,
        max_steps=max_steps_per_episode,
        max_episodes=train_max_episodes,
        seed=seed,
    )
    _materialize_lance(
        metadata=metadata_path,
        split=split_path,
        video_root=video_dir,
        output=val_normal_lance,
        partition="validation",
        label_filter="Normal",
        image_size=image_size,
        frame_stride=frame_stride,
        max_steps=max_steps_per_episode,
        max_episodes=None,
        seed=seed,
    )
    _materialize_lance(
        metadata=metadata_path,
        split=split_path,
        video_root=video_dir,
        output=val_buggy_lance,
        partition="validation",
        label_filter="Buggy",
        image_size=image_size,
        frame_stride=frame_stride,
        max_steps=max_steps_per_episode,
        max_episodes=None,
        seed=seed,
    )

    summary = {
        "status": "expanded_inputs_ready",
        "downloaded_normal_episodes": normal_count,
        "downloaded_buggy_episodes": buggy_count,
        "limit_per_group": limit_per_group,
        "categories": categories,
        "target_validation_normal_count": target_validation_normal_count,
        "target_validation_buggy_count": target_validation_buggy_count,
        "target_evaluation_normal_count": target_evaluation_normal_count,
        "minimum_calibration_normal_count": minimum_calibration_normal_count,
        "frame_stride": frame_stride,
        "max_steps_per_episode": max_steps_per_episode,
        "train_max_episodes": train_max_episodes,
        "recommended_calibration_normal_count": recommended_calibration_normal_count,
        "validation_normal_target_met": (
            support["validation_normal_episode_count"] >= target_validation_normal_count
        ),
        "evaluation_normal_target_met": (
            support["validation_normal_episode_count"]
            >= target_evaluation_normal_count + minimum_calibration_normal_count
        ),
        "allow_under_target_support": allow_under_target_support,
        "split_support": support,
        "metadata_path": str(metadata_path),
        "split_path": str(split_path),
        "train_lance": str(train_lance),
        "validation_normal_lance": str(val_normal_lance),
        "validation_buggy_lance": str(val_buggy_lance),
        "locked_test_materialized": False,
        "note": (
            "Pass the three lance paths to "
            "run_r5_tempglitch_identical_episode_evaluation.py and then "
            "run_tempglitch_followup_pair_disjoint.py."
        ),
    }
    (output_dir / "expanded_inputs_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build expanded-support TempGlitch Lance inputs (download + freeze + materialize)."
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--limit-per-group",
        type=int,
        default=35,
        help=(
            "Videos per (category, label) group. With five categories and the default "
            "20%% validation split, 35 targets about 35 validation normals."
        ),
    )
    parser.add_argument("--categories", nargs="+", default=None)
    parser.add_argument("--image-size", type=int, default=112)
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument(
        "--max-steps-per-episode",
        type=int,
        default=None,
        help=(
            "Optional cap on decoded frames per episode after frame stride. Use this on Kaggle "
            "expanded runs to keep Lance output below the working-disk quota."
        ),
    )
    parser.add_argument(
        "--train-max-episodes",
        type=int,
        default=None,
        help=(
            "Optional cap on train-normal episodes materialized into the train Lance. "
            "Validation support is never capped by this flag."
        ),
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-validation-normal-count", type=int, default=34)
    parser.add_argument("--target-validation-buggy-count", type=int, default=34)
    parser.add_argument("--target-evaluation-normal-count", type=int, default=30)
    parser.add_argument("--minimum-calibration-normal-count", type=int, default=1)
    parser.add_argument("--allow-under-target-support", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = build_expanded_inputs(
        output_dir=args.output_dir,
        limit_per_group=args.limit_per_group,
        categories=args.categories,
        image_size=args.image_size,
        frame_stride=args.frame_stride,
        max_steps_per_episode=args.max_steps_per_episode,
        train_max_episodes=args.train_max_episodes,
        seed=args.seed,
        target_validation_normal_count=args.target_validation_normal_count,
        target_validation_buggy_count=args.target_validation_buggy_count,
        target_evaluation_normal_count=args.target_evaluation_normal_count,
        minimum_calibration_normal_count=args.minimum_calibration_normal_count,
        allow_under_target_support=args.allow_under_target_support,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
