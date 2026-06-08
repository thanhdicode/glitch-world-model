from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

METRIC_KEYS = ["precision", "recall", "f1", "accuracy", "auroc", "threshold"]


def read_metrics(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_comparison_rows(named_metrics: list[tuple[str, Path]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, path in named_metrics:
        metrics = read_metrics(path)
        row: dict[str, Any] = {"name": name, "metrics_path": str(path)}
        for key in METRIC_KEYS:
            row[key] = metrics.get(key)
        rows.append(row)
    return rows


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if value is None:
        return "n/a"
    return str(value)


def write_comparison_markdown(rows: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Experiment Comparison",
        "",
        "| Experiment | Precision | Recall | F1 | Accuracy | AUROC | Threshold |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["name"]),
                    _format_value(row.get("precision")),
                    _format_value(row.get("recall")),
                    _format_value(row.get("f1")),
                    _format_value(row.get("accuracy")),
                    _format_value(row.get("auroc")),
                    _format_value(row.get("threshold")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Source Files", ""])
    for row in rows:
        lines.append(f"- {row['name']}: `{row.get('metrics_path', 'n/a')}`")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def parse_metric_args(values: list[str]) -> list[tuple[str, Path]]:
    named_metrics: list[tuple[str, Path]] = []
    for value in values:
        if "=" not in value:
            raise ValueError(f"Metric input must use NAME=PATH format: {value}")
        name, path = value.split("=", 1)
        named_metrics.append((name, Path(path)))
    return named_metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare experiment metrics in one Markdown table."
    )
    parser.add_argument(
        "--metric",
        action="append",
        required=True,
        help="Metric entry in NAME=PATH format. Repeat for multiple experiments.",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output Markdown path.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    rows = build_comparison_rows(parse_metric_args(args.metric))
    output_path = write_comparison_markdown(rows, args.output)
    print(f"Wrote comparison: {output_path}")


if __name__ == "__main__":
    main()
