from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a qualitative temporal-spike figure from validated R5-XGame outputs."
    )
    parser.add_argument("--window-manifest", required=True, type=Path)
    parser.add_argument("--raw-scores", required=True, type=Path)
    parser.add_argument("--thresholds-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--seed", default="44")
    parser.add_argument("--window-scorer", default="lewm_l2_max")
    parser.add_argument("--episode-aggregation", default="mean")
    return parser


def _window_score(row: dict[str, str], window_scorer: str) -> float:
    if window_scorer == "lewm_l2_max":
        return max(float(row["l2_t1"]), float(row["l2_t2"]), float(row["l2_t3"]))
    if window_scorer == "lewm_mse_max":
        return max(float(row["mse_t1"]), float(row["mse_t2"]), float(row["mse_t3"]))
    raise ValueError(f"Unsupported window scorer for figure generation: {window_scorer}")


def _threshold_row(
    thresholds_json: Path,
    *,
    seed: str,
    window_scorer: str,
    episode_aggregation: str,
) -> dict[str, object]:
    payload = json.loads(thresholds_json.read_text(encoding="utf-8"))
    for row in payload["thresholds"]:
        if (
            str(row["seed"]) == str(seed)
            and row["window_scorer"] == window_scorer
            and row["episode_aggregation"] == episode_aggregation
        ):
            return row
    raise ValueError(
        f"No threshold row found for seed={seed}, window_scorer={window_scorer}, "
        f"episode_aggregation={episode_aggregation}"
    )


def _collect_episode_scores(
    window_manifest: Path, raw_scores: Path, *, window_scorer: str
) -> dict[str, dict[str, object]]:
    episodes: dict[str, dict[str, object]] = {}
    with window_manifest.open("r", newline="", encoding="utf-8-sig") as manifest_handle:
        manifest_rows = csv.DictReader(manifest_handle)
        with raw_scores.open("r", newline="", encoding="utf-8-sig") as score_handle:
            score_rows = csv.DictReader(score_handle)
            for row_index, (manifest_row, score_row) in enumerate(
                zip(manifest_rows, score_rows), start=1
            ):
                if manifest_row["window_id"] != score_row["window_id"]:
                    raise ValueError(
                        "Window-manifest/raw-score alignment mismatch at row "
                        f"{row_index}: {manifest_row['window_id']} != {score_row['window_id']}"
                    )
                if manifest_row.get("evaluation_role") != "evaluation":
                    continue
                episode_id = manifest_row["source_episode_id"]
                record = episodes.setdefault(
                    episode_id,
                    {
                        "label": manifest_row["label"],
                        "category": manifest_row["category"],
                        "source": manifest_row["source"],
                        "scores": [],
                    },
                )
                record["scores"].append(_window_score(score_row, window_scorer))
    if not episodes:
        raise ValueError("No evaluation-role episode windows were found in the manifest.")
    return episodes


def _pick_episodes(episodes: dict[str, dict[str, object]]) -> tuple[str, str]:
    buggy_rows = []
    normal_rows = []
    for episode_id, payload in episodes.items():
        scores = payload["scores"]
        mean_score = sum(scores) / len(scores)
        item = (mean_score, episode_id)
        if str(payload["label"]).lower() == "buggy":
            buggy_rows.append(item)
        elif str(payload["label"]).lower() == "normal":
            normal_rows.append(item)
    if not buggy_rows or not normal_rows:
        raise ValueError("Expected both buggy and normal evaluation episodes.")
    buggy_rows.sort(reverse=True)
    normal_rows.sort()
    return buggy_rows[0][1], normal_rows[0][1]


def _contiguous_spans(values: list[float], threshold: float) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(values):
        if value > threshold and start is None:
            start = index
        elif value <= threshold and start is not None:
            spans.append((start, index - 1))
            start = None
    if start is not None:
        spans.append((start, len(values) - 1))
    return spans


def generate_figure(
    *,
    window_manifest: Path,
    raw_scores: Path,
    thresholds_json: Path,
    output_dir: Path,
    seed: str,
    window_scorer: str,
    episode_aggregation: str,
) -> dict[str, object]:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required to generate the paper figure.") from exc

    threshold_row = _threshold_row(
        thresholds_json,
        seed=seed,
        window_scorer=window_scorer,
        episode_aggregation=episode_aggregation,
    )
    threshold = float(threshold_row["threshold"])
    episodes = _collect_episode_scores(window_manifest, raw_scores, window_scorer=window_scorer)
    buggy_episode, normal_episode = _pick_episodes(episodes)
    buggy_scores = [float(value) for value in episodes[buggy_episode]["scores"]]
    normal_scores = [float(value) for value in episodes[normal_episode]["scores"]]
    spans = _contiguous_spans(buggy_scores, threshold)

    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "fig_temporal_spike.png"
    pdf_path = output_dir / "fig_temporal_spike.pdf"
    receipt_path = output_dir / "fig_temporal_spike_receipt.json"

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    figure, axis_left = plt.subplots(figsize=(3.5, 2.4), constrained_layout=True)
    axis_right = axis_left.twinx()
    x_normal = list(range(len(normal_scores)))
    x_buggy = list(range(len(buggy_scores)))

    normal_line = axis_left.plot(
        x_normal,
        normal_scores,
        color="#2b6cb0",
        linewidth=1.05,
        label="Normal episode",
        zorder=3,
    )[0]
    buggy_line = axis_right.plot(
        x_buggy,
        buggy_scores,
        color="#c53030",
        linewidth=1.0,
        label="Buggy episode",
        zorder=4,
    )[0]
    axis_right.fill_between(
        x_buggy,
        threshold,
        buggy_scores,
        where=[value > threshold for value in buggy_scores],
        color="#d55c5a",
        alpha=0.16,
        interpolate=True,
        zorder=2,
    )
    threshold_left = axis_left.axhline(
        threshold,
        color="#4a5568",
        linestyle="--",
        linewidth=0.9,
        label=f"Threshold = {threshold:.3f}",
    )
    axis_right.axhline(
        threshold,
        color="#4a5568",
        linestyle="--",
        linewidth=0.9,
    )

    axis_left.set_xlabel("Window Index")
    axis_left.set_ylabel("Normal E(t)", color="#2b6cb0")
    axis_right.set_ylabel("Buggy E(t)", color="#c53030")
    axis_left.tick_params(axis="y", colors="#2b6cb0")
    axis_right.tick_params(axis="y", colors="#c53030")
    axis_left.set_xlim(0, max(len(normal_scores), len(buggy_scores)) - 1)
    axis_left.grid(axis="y", color="#d9d9d9", linewidth=0.5, alpha=0.85)
    figure.legend(
        [normal_line, buggy_line, threshold_left],
        [normal_line.get_label(), buggy_line.get_label(), threshold_left.get_label()],
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 1.02),
    )

    figure.savefig(png_path, dpi=300, bbox_inches="tight")
    figure.savefig(pdf_path, dpi=300, bbox_inches="tight")
    plt.close(figure)

    receipt = {
        "status": "paper_r5_xgame_temporal_spike_generated",
        "temporal_metrics_claimed": False,
        "ground_truth_spans_available": False,
        "locked_test_used": False,
        "source_script": "scripts/generate_r5_xgame_temporal_spike_figure.py",
        "selected_config": {
            "seed": str(seed),
            "window_scorer": window_scorer,
            "episode_aggregation": episode_aggregation,
            "threshold": threshold,
            "threshold_source": threshold_row["threshold_source"],
            "calibration_episode_ids": threshold_row["calibration_episode_ids"],
        },
        "selected_episodes": {
            "buggy": {
                "source_episode_id": buggy_episode,
                "category": episodes[buggy_episode]["category"],
                "label": episodes[buggy_episode]["label"],
                "window_count": len(buggy_scores),
                "mean_score": sum(buggy_scores) / len(buggy_scores),
                "max_score": max(buggy_scores),
            },
            "normal": {
                "source_episode_id": normal_episode,
                "category": episodes[normal_episode]["category"],
                "label": episodes[normal_episode]["label"],
                "window_count": len(normal_scores),
                "mean_score": sum(normal_scores) / len(normal_scores),
                "max_score": max(normal_scores),
            },
        },
        "threshold_exceedance_spans": spans,
        "claim_ids": ["C-083", "C-084", "C-088", "C-098", "C-115"],
        "generated_utc": datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "source_paths": {
            "window_manifest": str(window_manifest),
            "raw_scores": str(raw_scores),
            "thresholds_json": str(thresholds_json),
        },
        "source_hashes": {
            "window_manifest_sha256": sha256(window_manifest),
            "raw_scores_sha256": sha256(raw_scores),
            "thresholds_json_sha256": sha256(thresholds_json),
        },
        "outputs": {
            "fig_temporal_spike.png": None,
            "fig_temporal_spike.pdf": None,
        },
    }
    receipt["outputs"]["fig_temporal_spike.png"] = sha256(png_path)
    receipt["outputs"]["fig_temporal_spike.pdf"] = sha256(pdf_path)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    args = build_parser().parse_args()
    receipt = generate_figure(
        window_manifest=args.window_manifest,
        raw_scores=args.raw_scores,
        thresholds_json=args.thresholds_json,
        output_dir=args.output_dir,
        seed=str(args.seed),
        window_scorer=args.window_scorer,
        episode_aggregation=args.episode_aggregation,
    )
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
