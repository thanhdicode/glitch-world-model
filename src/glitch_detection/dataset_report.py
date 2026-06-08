from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from .manifest import clip_has_glitch, read_labels, read_manifest


def read_score_values(scores_path: Path) -> list[float]:
    with scores_path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [float(row["score"]) for row in csv.DictReader(handle)]


def build_report(
    name: str,
    manifest_path: Path,
    labels_path: Path | None,
    scores_path: Path,
    metrics_path: Path | None,
) -> dict[str, Any]:
    records = read_manifest(manifest_path)
    labels = read_labels(labels_path)
    scores = read_score_values(scores_path)
    metrics: dict[str, Any] = {}
    if metrics_path is not None and metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    positive_clip_count = sum(
        int(clip_has_glitch(record.source, record.start_frame, record.end_frame, labels))
        for record in records
    )

    return {
        "name": name,
        "manifest_path": str(manifest_path),
        "labels_path": str(labels_path) if labels_path else None,
        "scores_path": str(scores_path),
        "metrics_path": str(metrics_path) if metrics_path else None,
        "clip_count": len(records),
        "source_count": len({record.source for record in records}),
        "positive_clip_count": positive_clip_count,
        "score_min": min(scores) if scores else None,
        "score_mean": mean(scores) if scores else None,
        "score_max": max(scores) if scores else None,
        "metrics": metrics,
    }


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if value is None:
        return "n/a"
    return str(value)


def write_markdown_report(report: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics = report.get("metrics", {})
    lines = [
        f"# Experiment Report: {report['name']}",
        "",
        "## Dataset",
        "",
        f"- Clips: {report['clip_count']}",
        f"- Sources: {report.get('source_count', 'n/a')}",
        f"- Positive/glitch clips: {report['positive_clip_count']}",
        "",
        "## Scores",
        "",
        "| Statistic | Value |",
        "| --- | ---: |",
        f"| Min | {_format_value(report['score_min'])} |",
        f"| Mean | {_format_value(report['score_mean'])} |",
        f"| Max | {_format_value(report['score_max'])} |",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in ["precision", "recall", "f1", "accuracy", "auroc", "threshold"]:
        if key in metrics:
            lines.append(
                f"| {key.upper() if key != 'f1' else 'F1'} | {_format_value(metrics[key])} |"
            )
    lines.extend(
        [
            "",
            "## Files",
            "",
            f"- Manifest: `{report.get('manifest_path', 'n/a')}`",
            f"- Labels: `{report.get('labels_path', 'n/a')}`",
            f"- Scores: `{report.get('scores_path', 'n/a')}`",
            f"- Metrics: `{report.get('metrics_path', 'n/a')}`",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a compact Markdown report for an experiment."
    )
    parser.add_argument("--name", required=True, help="Experiment name.")
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest.csv.")
    parser.add_argument("--labels", type=Path, default=None, help="Optional labels CSV.")
    parser.add_argument("--scores", required=True, type=Path, help="Path to scores.csv.")
    parser.add_argument("--metrics", type=Path, default=None, help="Optional metrics JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Output Markdown report path.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    report = build_report(args.name, args.manifest, args.labels, args.scores, args.metrics)
    output_path = write_markdown_report(report, args.output)
    print(f"Wrote report: {output_path}")


if __name__ == "__main__":
    main()
