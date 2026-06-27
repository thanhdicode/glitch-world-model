# ruff: noqa: E402

"""P6 qualitative glitch surprise timeline demo."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.generate_qualitative_surprise_timelines import (
    generate_qualitative_surprise_timelines,
)

_RECEIPT_STATIC: dict[str, object] = {
    "temporal_metrics_claimed": False,
    "locked_test_used": False,
    "ground_truth_spans_available": False,
    "kaggle_required": False,
    "claim_boundary": (
        "qualitative only - no temporal-localization metric, "
        "no locked test, no broad LeWM superiority claim"
    ),
    "demo_phase": "P6",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the P6 qualitative glitch demo without Kaggle or locked test."
    )
    default_base = REPO_ROOT / "outputs" / "tempglitch_followup_pair_disjoint"
    parser.add_argument(
        "--comparison-csv",
        type=Path,
        default=default_base / "followup_comparison.csv",
        help="Path to the non-locked follow-up comparison CSV.",
    )
    parser.add_argument(
        "--episode-scores-csv",
        type=Path,
        default=default_base / "followup_episode_scores.csv",
        help="Path to the non-locked follow-up episode score CSV.",
    )
    parser.add_argument(
        "--manifest-csv",
        type=Path,
        default=default_base / "followup_manifest.csv",
        help="Path to the non-locked follow-up manifest CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "outputs" / "demo_timelines",
        help="Directory for demo plots and the demo receipt.",
    )
    parser.add_argument(
        "--max-episodes",
        type=int,
        default=6,
        help="Maximum number of episode timelines to emit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the demo receipt and validate inputs without plotting.",
    )
    return parser


def _check_inputs_exist(
    comparison_csv: Path,
    episode_scores_csv: Path,
    manifest_csv: Path,
) -> list[str]:
    missing: list[str] = []
    for label, path in (
        ("comparison CSV", comparison_csv),
        ("episode scores CSV", episode_scores_csv),
        ("manifest CSV", manifest_csv),
    ):
        if not path.is_file():
            missing.append(f"  {label}: {path}")
    return missing


def _receipt_path(output_dir: Path) -> Path:
    return output_dir / "demo_receipt.json"


def _write_receipt(output_dir: Path, extra: dict[str, object]) -> Path:
    receipt_path = _receipt_path(output_dir)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {**_RECEIPT_STATIC, **extra}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt_path


def _split_episode_budget(max_episodes: int) -> tuple[int, int]:
    if max_episodes < 1:
        raise ValueError("--max-episodes must be >= 1.")
    max_buggy = (max_episodes + 1) // 2
    max_normal = max_episodes // 2
    if max_normal == 0:
        max_normal = 1
    return max_buggy, max_normal


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    print("=" * 70)
    print("P6 Qualitative Glitch Demo Lane")
    print("  temporal_metrics_claimed : False")
    print("  locked_test_used         : False")
    print("  kaggle_required          : False")
    print("=" * 70)

    missing = _check_inputs_exist(
        args.comparison_csv,
        args.episode_scores_csv,
        args.manifest_csv,
    )
    if args.dry_run:
        receipt_path = _write_receipt(
            args.output_dir,
            {
                "mode": "dry_run",
                "inputs_found": len(missing) == 0,
                "missing_inputs": missing,
                "plots_generated": [],
            },
        )
        print(f"[dry-run] Receipt written: {receipt_path}")
        if missing:
            print("[dry-run] Missing input files (expected when artifacts are absent):")
            for item in missing:
                print(item)
        print("[dry-run] Done.")
        return 0

    if missing:
        print("ERROR: Required input files not found:", file=sys.stderr)
        for item in missing:
            print(item, file=sys.stderr)
        print(
            "Hint: provide the non-locked follow-up CSVs or use --dry-run.",
            file=sys.stderr,
        )
        return 1

    try:
        max_buggy, max_normal = _split_episode_budget(args.max_episodes)
        qualitative_receipt = generate_qualitative_surprise_timelines(
            comparison_csv=args.comparison_csv,
            episode_scores_csv=args.episode_scores_csv,
            manifest_csv=args.manifest_csv,
            output_dir=args.output_dir,
            receipt_path=args.output_dir / "qualitative_timeline_receipt.json",
            max_buggy=max_buggy,
            max_normal=max_normal,
        )
        plots_generated = sorted(
            str(path) for path in args.output_dir.glob("*.png") if path.is_file()
        )
        receipt_path = _write_receipt(
            args.output_dir,
            {
                "mode": "full",
                "inputs_found": True,
                "missing_inputs": [],
                "plots_generated": plots_generated,
                "comparison_csv": str(args.comparison_csv),
                "episode_scores_csv": str(args.episode_scores_csv),
                "manifest_csv": str(args.manifest_csv),
                "qualitative_receipt_path": str(
                    args.output_dir / "qualitative_timeline_receipt.json"
                ),
                "selected_config": qualitative_receipt.get("selected_config", {}),
            },
        )
        print(f"Receipt : {receipt_path}")
        print(f"Plots   : {args.output_dir}")
        print("Done.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR during demo generation: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
