from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPLIT_PATH = ROOT / "outputs" / "gate3" / "world_of_bugs" / "split.csv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "wob_kaggle_listing"
NORMAL_SLUG = "benedictwilkinsai/world-of-bugs-normal"
TEST_SLUG = "benedictwilkinsai/world-of-bugs-test"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify that non-locked WOB split rows exist in the official Kaggle listings."
    )
    parser.add_argument("--split-path", type=Path, default=DEFAULT_SPLIT_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def load_nonlocked_rows(split_path: Path) -> list[dict[str, str]]:
    with split_path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.DictReader(handle) if row["split"] != "test"]
    if not rows:
        raise ValueError("No non-locked WOB rows found in split metadata.")
    return rows


def dataset_slug_for_source(source: str) -> str:
    if source.startswith("NORMAL-TRAIN/"):
        return NORMAL_SLUG
    if source.startswith("TEST/"):
        return TEST_SLUG
    raise ValueError(f"Unsupported WOB source path: {source}")


def parse_kaggle_files_csv(stdout: str) -> list[dict[str, str]]:
    lines = [
        line for line in stdout.splitlines() if line and not line.startswith("Next Page Token")
    ]
    return list(csv.DictReader(io.StringIO("\n".join(lines))))


def kaggle_files(slug: str) -> list[dict[str, str]]:
    result = subprocess.run(
        [sys.executable, "-m", "kaggle", "datasets", "files", slug, "--page-size", "200", "-v"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return parse_kaggle_files_csv(result.stdout)


def human_kaggle_setup_instructions() -> list[str]:
    return [
        "Ensure the Kaggle Python package is installed in the active environment.",
        "Place kaggle.json under %USERPROFILE%/.kaggle/kaggle.json or the platform-equivalent Kaggle config directory.",
        f"Verify listings with: python -m kaggle datasets files {NORMAL_SLUG} -v",
        f"Verify listings with: python -m kaggle datasets files {TEST_SLUG} -v",
        "Do not expose kaggle.json contents in chat or commit it.",
    ]


def compute_listing_report(
    rows: list[dict[str, str]],
    *,
    normal_listing: list[dict[str, str]],
    test_listing: list[dict[str, str]],
    locked_rows_in_split_csv: int | None,
) -> dict[str, Any]:
    listing_index = {
        NORMAL_SLUG: {row["name"]: int(row["size"]) for row in normal_listing},
        TEST_SLUG: {row["name"]: int(row["size"]) for row in test_listing},
    }
    missing_by_slug: dict[str, list[str]] = {NORMAL_SLUG: [], TEST_SLUG: []}
    total_bytes = 0
    for row in rows:
        slug = dataset_slug_for_source(row["source"])
        if row["source"] not in listing_index[slug]:
            missing_by_slug[slug].append(row["source"])
            continue
        total_bytes += listing_index[slug][row["source"]]

    missing = missing_by_slug[NORMAL_SLUG] + missing_by_slug[TEST_SLUG]
    return {
        "official_sources": {
            "normal_dataset": NORMAL_SLUG,
            "test_dataset": TEST_SLUG,
        },
        "expected_nonlocked_rows": len(rows),
        "resolved_nonlocked_rows": len(rows) - len(missing),
        "missing_nonlocked_rows": len(missing),
        "missing_sources": missing,
        "total_nonlocked_bytes": total_bytes,
        "total_nonlocked_gib": round(total_bytes / (1024**3), 3),
        "locked_rows_in_split_csv": locked_rows_in_split_csv,
        "local_wob_p0_status": "BLOCKED_MISSING_INPUTS",
        "kaggle_native_status": "READY_FOR_KAGGLE_WOB_P0"
        if not missing
        else "BLOCKED_KAGGLE_INPUT_SETUP",
        "wob_p1_training_status": "NOT_STARTED",
        "normal_listing_count": len(normal_listing),
        "test_listing_count": len(test_listing),
    }


def render_markdown(report: dict[str, Any]) -> str:
    return (
        "\n".join(
            [
                "# WOB Kaggle Listing Report",
                "",
                f"- Official normal dataset: `{report['official_sources']['normal_dataset']}`",
                f"- Official test dataset: `{report['official_sources']['test_dataset']}`",
                f"- Expected non-locked rows: `{report['expected_nonlocked_rows']}`",
                f"- Resolved non-locked rows: `{report['resolved_nonlocked_rows']}`",
                f"- Missing non-locked rows: `{report['missing_nonlocked_rows']}`",
                f"- Total non-locked bytes: `{report['total_nonlocked_bytes']}`",
                f"- Total non-locked GiB: `{report['total_nonlocked_gib']}`",
                f"- Kaggle-native status: `{report['kaggle_native_status']}`",
                f"- WOB-P1 training status: `{report['wob_p1_training_status']}`",
            ]
        )
        + "\n"
    )


def main() -> None:
    args = build_parser().parse_args()
    with args.split_path.open("r", newline="", encoding="utf-8-sig") as handle:
        all_rows = list(csv.DictReader(handle))
    rows = [row for row in all_rows if row["split"] != "test"]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        normal_listing = kaggle_files(NORMAL_SLUG)
        test_listing = kaggle_files(TEST_SLUG)
        report = compute_listing_report(
            rows,
            normal_listing=normal_listing,
            test_listing=test_listing,
            locked_rows_in_split_csv=sum(1 for row in all_rows if row["split"] == "test"),
        )
    except Exception as exc:
        report = {
            "official_sources": {
                "normal_dataset": NORMAL_SLUG,
                "test_dataset": TEST_SLUG,
            },
            "kaggle_native_status": "BLOCKED_KAGGLE_INPUT_SETUP",
            "local_wob_p0_status": "BLOCKED_MISSING_INPUTS",
            "wob_p1_training_status": "NOT_STARTED",
            "error": str(exc),
            "human_setup_instructions": human_kaggle_setup_instructions(),
        }

    (args.output_dir / "wob_kaggle_listing.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "wob_kaggle_listing.md").write_text(
        render_markdown(report),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
