# ruff: noqa: E402

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from statistics import mean
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from glitch_detection.lewm_adapter import sha256_file

try:
    from scripts.plot_lewm_surprise_timeline import plot_series
except ModuleNotFoundError:
    from plot_lewm_surprise_timeline import plot_series


DEFAULT_COMPARISON_CSV = (
    REPO_ROOT / "outputs" / "tempglitch_followup_pair_disjoint" / "followup_comparison.csv"
)
DEFAULT_EPISODE_SCORES_CSV = (
    REPO_ROOT / "outputs" / "tempglitch_followup_pair_disjoint" / "followup_episode_scores.csv"
)
DEFAULT_MANIFEST_CSV = (
    REPO_ROOT / "outputs" / "tempglitch_followup_pair_disjoint" / "followup_manifest.csv"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "qualitative_surprise_timelines"
DEFAULT_RECEIPT_PATH = DEFAULT_OUTPUT_DIR / "qualitative_timeline_receipt.json"
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class EpisodeTimeline:
    source_episode_id: str
    label: str
    evaluation_role: str
    category: str
    source: str
    window_indices: tuple[int, ...]
    scores: tuple[float, ...]


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _resolve_repo_path(path_text: str, *, base_dir: Path | None = None) -> Path:
    raw = path_text.strip()
    if not raw:
        raise ValueError("Expected a non-empty artifact path.")
    if "\\" in raw:
        candidate = PureWindowsPath(raw)
        if candidate.is_absolute():
            return Path(candidate)
        relative_path = Path(*candidate.parts)
    else:
        candidate = PurePosixPath(raw)
        if candidate.is_absolute():
            return Path(candidate)
        relative_path = Path(*candidate.parts)
    if base_dir is not None:
        base_candidate = base_dir / relative_path
        if base_candidate.exists():
            return base_candidate
    repo_candidate = REPO_ROOT / relative_path
    if repo_candidate.exists():
        return repo_candidate
    return (base_dir / relative_path) if base_dir is not None else repo_candidate


def _float_key(row: dict[str, str], field: str) -> float:
    value = row.get(field, "").strip()
    return float(value) if value else float("-inf")


def select_best_comparison_row(
    comparison_rows: list[dict[str, str]],
    *,
    method_family: str = "lewm",
) -> dict[str, str]:
    matching = [row for row in comparison_rows if row.get("method_family") == method_family]
    if not matching:
        raise ValueError(f"No comparison rows found for method_family={method_family!r}.")
    return max(
        matching,
        key=lambda row: (
            _float_key(row, "auroc"),
            _float_key(row, "auprc"),
            -int(row.get("seed") or 0),
            row.get("window_scorer", ""),
            row.get("episode_aggregation", ""),
        ),
    )


def lewm_window_score_from_row(raw_row: dict[str, str], window_scorer: str) -> float:
    mse = [float(raw_row[field]) for field in ("mse_t1", "mse_t2", "mse_t3")]
    l2 = [float(raw_row[field]) for field in ("l2_t1", "l2_t2", "l2_t3")]
    scores = {
        "lewm_mse_mean": float(mean(mse)),
        "lewm_mse_max": float(max(mse)),
        "lewm_mse_top2_mean": float(mean(sorted(mse, reverse=True)[:2])),
        "lewm_l2_mean": float(mean(l2)),
        "lewm_l2_max": float(max(l2)),
        "lewm_l2_top2_mean": float(mean(sorted(l2, reverse=True)[:2])),
    }
    try:
        return scores[window_scorer]
    except KeyError as exc:
        raise ValueError(
            f"Qualitative LeWM timelines do not support window_scorer={window_scorer!r}."
        ) from exc


def build_episode_timelines(
    manifest_rows: list[dict[str, str]],
    raw_score_rows: list[dict[str, str]],
    *,
    window_scorer: str,
) -> dict[str, EpisodeTimeline]:
    raw_by_window_id = {row["window_id"]: row for row in raw_score_rows}
    timelines: dict[str, list[tuple[int, dict[str, str], float]]] = {}
    for manifest_row in manifest_rows:
        window_id = manifest_row["window_id"]
        raw_row = raw_by_window_id.get(window_id)
        if raw_row is None:
            raise ValueError(f"Missing raw score row for window_id={window_id!r}.")
        episode_id = manifest_row["source_episode_id"]
        timelines.setdefault(episode_id, []).append(
            (
                int(manifest_row["dataset_window_index"]),
                manifest_row,
                lewm_window_score_from_row(raw_row, window_scorer),
            )
        )

    output: dict[str, EpisodeTimeline] = {}
    for episode_id, rows in timelines.items():
        ordered = sorted(rows, key=lambda item: item[0])
        first = ordered[0][1]
        output[episode_id] = EpisodeTimeline(
            source_episode_id=episode_id,
            label=first["label"],
            evaluation_role=first["evaluation_role"],
            category=first["category"],
            source=first["source"],
            window_indices=tuple(index for index, _row, _score in ordered),
            scores=tuple(score for _index, _row, score in ordered),
        )
    return output


def select_qualitative_episode_rows(
    episode_score_rows: list[dict[str, str]],
    *,
    selected_config: dict[str, str],
    max_buggy: int,
    max_normal: int,
) -> list[dict[str, str]]:
    filtered = [
        row
        for row in episode_score_rows
        if row.get("method_family") == selected_config.get("method_family")
        and row.get("window_scorer") == selected_config.get("window_scorer")
        and row.get("seed") == selected_config.get("seed")
        and row.get("episode_aggregation") == selected_config.get("episode_aggregation")
    ]
    if not filtered:
        raise ValueError("No episode-score rows match the selected qualitative configuration.")

    def _score_sort_key(row: dict[str, str]) -> tuple[int, float, str]:
        role_priority = 0 if row.get("evaluation_role") == "evaluation" else 1
        return (role_priority, -float(row["score"]), row["source_episode_id"])

    buggy = sorted(
        [row for row in filtered if row.get("label") == "Buggy"],
        key=_score_sort_key,
    )[:max_buggy]
    normal = sorted(
        [row for row in filtered if row.get("label") == "Normal"],
        key=_score_sort_key,
    )[:max_normal]
    return buggy + normal


def _safe_name(text: str) -> str:
    return SAFE_NAME_RE.sub("_", text).strip("_") or "timeline"


def generate_qualitative_surprise_timelines(
    *,
    comparison_csv: Path = DEFAULT_COMPARISON_CSV,
    episode_scores_csv: Path = DEFAULT_EPISODE_SCORES_CSV,
    manifest_csv: Path = DEFAULT_MANIFEST_CSV,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    receipt_path: Path = DEFAULT_RECEIPT_PATH,
    max_buggy: int = 2,
    max_normal: int = 2,
    method_family: str = "lewm",
) -> dict[str, Any]:
    comparison_rows = _read_csv_rows(comparison_csv)
    episode_score_rows = _read_csv_rows(episode_scores_csv)
    manifest_rows = _read_csv_rows(manifest_csv)
    selected_config = select_best_comparison_row(comparison_rows, method_family=method_family)
    raw_score_path = _resolve_repo_path(
        selected_config["raw_score_path"],
        base_dir=comparison_csv.parent,
    )
    raw_score_rows = _read_csv_rows(raw_score_path)
    timelines = build_episode_timelines(
        manifest_rows,
        raw_score_rows,
        window_scorer=selected_config["window_scorer"],
    )
    selected_episode_rows = select_qualitative_episode_rows(
        episode_score_rows,
        selected_config=selected_config,
        max_buggy=max_buggy,
        max_normal=max_normal,
    )

    threshold = float(selected_config["threshold"])
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_records: list[dict[str, Any]] = []
    for episode_row in selected_episode_rows:
        episode_id = episode_row["source_episode_id"]
        timeline = timelines.get(episode_id)
        if timeline is None:
            raise ValueError(f"Missing timeline data for source_episode_id={episode_id!r}.")
        file_name = f"{episode_row['label'].lower()}_{_safe_name(timeline.category)}_{_safe_name(episode_id)}.png"
        plot_path = output_dir / file_name
        note = (
            "Qualitative only. No ground-truth temporal spans are available, "
            "so this figure does not claim temporal localization."
        )
        plot_series(
            list(timeline.scores),
            plot_path,
            x_values=list(timeline.window_indices),
            threshold=threshold,
            title=(
                "LeWM surprise timeline "
                f"({timeline.label}, {timeline.category}, seed {selected_config['seed']})"
            ),
            x_label="Window index",
            y_label=selected_config["window_scorer"],
            qualitative_note=note,
        )
        plot_records.append(
            {
                "source_episode_id": episode_id,
                "label": timeline.label,
                "evaluation_role": timeline.evaluation_role,
                "category": timeline.category,
                "source": timeline.source,
                "episode_score": float(episode_row["score"]),
                "window_count": len(timeline.scores),
                "plot_path": str(plot_path),
                "plot_sha256": sha256_file(plot_path),
            }
        )

    receipt = {
        "status": "qualitative_timelines_generated",
        "temporal_metrics_claimed": False,
        "ground_truth_spans_available": False,
        "locked_test_used": False,
        "k4_required": False,
        "comparison_csv": str(comparison_csv),
        "episode_scores_csv": str(episode_scores_csv),
        "manifest_csv": str(manifest_csv),
        "selected_config": {
            "method_family": selected_config["method_family"],
            "method": selected_config["method"],
            "window_scorer": selected_config["window_scorer"],
            "seed": selected_config["seed"],
            "episode_aggregation": selected_config["episode_aggregation"],
            "threshold": selected_config["threshold"],
            "threshold_source": selected_config["threshold_source"],
            "raw_score_path": str(raw_score_path),
            "raw_score_sha256": sha256_file(raw_score_path),
        },
        "plot_count": len(plot_records),
        "plots": plot_records,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate qualitative LeWM surprise timelines from existing non-locked artifacts "
            "without claiming temporal localization metrics."
        )
    )
    parser.add_argument("--comparison-csv", type=Path, default=DEFAULT_COMPARISON_CSV)
    parser.add_argument("--episode-scores-csv", type=Path, default=DEFAULT_EPISODE_SCORES_CSV)
    parser.add_argument("--manifest-csv", type=Path, default=DEFAULT_MANIFEST_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--receipt-path", type=Path, default=DEFAULT_RECEIPT_PATH)
    parser.add_argument("--max-buggy", type=int, default=2)
    parser.add_argument("--max-normal", type=int, default=2)
    parser.add_argument("--method-family", default="lewm")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    receipt = generate_qualitative_surprise_timelines(
        comparison_csv=args.comparison_csv,
        episode_scores_csv=args.episode_scores_csv,
        manifest_csv=args.manifest_csv,
        output_dir=args.output_dir,
        receipt_path=args.receipt_path,
        max_buggy=args.max_buggy,
        max_normal=args.max_normal,
        method_family=args.method_family,
    )
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
