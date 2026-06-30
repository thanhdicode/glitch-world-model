from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = (
    "method_family",
    "method",
    "window_scorer",
    "seed",
    "episode_aggregation",
    "threshold_source",
    "auroc",
    "auprc",
    "f1",
    "evaluation_episode_count",
    "positive_episode_count",
    "negative_episode_count",
)
NUMERIC_COLUMNS = (
    "auroc",
    "auprc",
    "f1",
    "precision",
    "recall",
    "balanced_accuracy",
    "fpr_at_95_tpr",
    "auroc_ci_lower",
    "auroc_ci_upper",
    "f1_ci_lower",
    "f1_ci_upper",
)
INTEGER_COLUMNS = (
    "evaluation_episode_count",
    "positive_episode_count",
    "negative_episode_count",
)
REQUIRED_NUMERIC_COLUMNS = ("auroc", "auprc", "f1")
REQUIRED_INTEGER_COLUMNS = (
    "evaluation_episode_count",
    "positive_episode_count",
    "negative_episode_count",
)
SAFETY_FLAGS = (
    "validation_buggy_used_for_fit_select",
    "locked_test_materialized",
    "locked_test_scored",
)
AXIS_GUARDRAIL = (
    "window_scorer and episode_aggregation are separate axes; "
    "lewm_l2_max is a window scorer, not episode-level max aggregation."
)


class SelectionSummaryError(ValueError):
    """Raised when a comparison artifact is unsafe or malformed."""


def _parse_float(
    row: dict[str, str],
    column: str,
    row_number: int,
    *,
    required: bool = False,
) -> float | None:
    value = row.get(column, "")
    if value == "":
        if required:
            raise SelectionSummaryError(f"row {row_number}: blank required numeric field {column}")
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise SelectionSummaryError(
            f"row {row_number}: non-numeric metric {column}={value!r}"
        ) from exc
    if not math.isfinite(parsed):
        raise SelectionSummaryError(f"row {row_number}: non-finite metric {column}={value!r}")
    return parsed


def _parse_int(
    row: dict[str, str],
    column: str,
    row_number: int,
    *,
    required: bool = False,
) -> int | None:
    value = row.get(column, "")
    if value == "":
        if required:
            raise SelectionSummaryError(f"row {row_number}: blank required count field {column}")
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise SelectionSummaryError(
            f"row {row_number}: non-integer count {column}={value!r}"
        ) from exc


def load_comparison_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise SelectionSummaryError(f"missing required column(s): {', '.join(missing)}")
        rows: list[dict[str, Any]] = []
        for row_number, raw in enumerate(reader, start=2):
            parsed: dict[str, Any] = {key: raw.get(key, "") for key in fieldnames}
            for column in NUMERIC_COLUMNS:
                if column in fieldnames:
                    parsed[column] = _parse_float(
                        raw,
                        column,
                        row_number,
                        required=column in REQUIRED_NUMERIC_COLUMNS,
                    )
            for column in INTEGER_COLUMNS:
                if column in fieldnames:
                    parsed[column] = _parse_int(
                        raw,
                        column,
                        row_number,
                        required=column in REQUIRED_INTEGER_COLUMNS,
                    )
            rows.append(parsed)
    if not rows:
        raise SelectionSummaryError(f"comparison CSV has no rows: {path}")
    return rows


def _flag_is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def load_safety_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    metadata = json.loads(path.read_text(encoding="utf-8-sig"))
    parsed_flags = {
        flag: _flag_is_true(metadata.get(flag, False)) for flag in SAFETY_FLAGS if flag in metadata
    }
    for flag, is_true in parsed_flags.items():
        if is_true:
            raise SelectionSummaryError(f"{flag} must be false for reporting-safe summaries.")
    return parsed_flags


def _display_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "method_family",
        "method",
        "window_scorer",
        "seed",
        "episode_aggregation",
        "threshold_source",
        "auroc",
        "auprc",
        "f1",
        "precision",
        "recall",
        "balanced_accuracy",
        "fpr_at_95_tpr",
        "evaluation_episode_count",
        "positive_episode_count",
        "negative_episode_count",
        "auroc_ci_lower",
        "auroc_ci_upper",
        "f1_ci_lower",
        "f1_ci_upper",
    )
    return {key: row.get(key) for key in keys if key in row}


def summarize_selection(
    rows: list[dict[str, Any]],
    *,
    top_k: int = 5,
    safety_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if top_k < 1:
        raise SelectionSummaryError("top_k must be positive.")
    metrics = ("auroc", "auprc", "f1")
    top_by_metric: dict[str, list[dict[str, Any]]] = {}
    for metric in metrics:
        top_rows = sorted(rows, key=lambda row: float(row[metric]), reverse=True)[:top_k]
        top_by_metric[metric] = [_display_row(row) for row in top_rows]
    return {
        "status": "selection_summary_complete",
        "row_count": len(rows),
        "axis_guardrail": AXIS_GUARDRAIL,
        "safety_metadata": safety_metadata or {},
        "best_by_metric": {metric: values[0] for metric, values in top_by_metric.items()},
        "top_by_metric": top_by_metric,
    }


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if value is None:
        return ""
    return str(value)


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    best = summary["best_by_metric"]["auroc"]
    lines = [
        f"# {title}",
        "",
        "## Guardrail",
        "",
        summary["axis_guardrail"],
        "",
        "## Best AUROC Row",
        "",
        (
            f"- Method: `{best['method']}`"
            f" seed `{best.get('seed') or 'n/a'}`"
            f" window scorer `{best['window_scorer']}`"
            f" episode `{best['episode_aggregation']}`"
        ),
        f"- AUROC: `{_fmt(best['auroc'])}`",
        f"- AUPRC: `{_fmt(best.get('auprc'))}`",
        f"- F1: `{_fmt(best.get('f1'))}`",
        f"- FPR@95TPR: `{_fmt(best.get('fpr_at_95_tpr'))}`",
        f"- Evaluation support: `{best.get('negative_episode_count')}` "
        "normal-negative / "
        f"`{best.get('positive_episode_count')}` buggy-positive episodes",
        "",
        "## Top Rows By Metric",
        "",
    ]
    for metric, rows in summary["top_by_metric"].items():
        lines.extend(
            [
                f"### {metric.upper()}",
                "",
                "| Rank | Method | Seed | Window scorer | Episode aggregation | Value |",
                "| ---: | --- | --- | --- | --- | ---: |",
            ]
        )
        for index, row in enumerate(rows, start=1):
            lines.append(
                f"| {index} | `{row['method']}` | `{row.get('seed') or 'n/a'}` | "
                f"`{row['window_scorer']}` | `{row['episode_aggregation']}` | "
                f"{_fmt(row[metric])} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize validated TempGlitch comparison row selection."
    )
    parser.add_argument("--comparison-csv", required=True, type=Path)
    parser.add_argument("--metadata-json", type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--title", default="TempGlitch Selection Reporting Audit")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    safety_metadata = load_safety_metadata(args.metadata_json)
    summary = summarize_selection(
        load_comparison_rows(args.comparison_csv),
        top_k=args.top_k,
        safety_metadata=safety_metadata,
    )
    if args.format == "markdown":
        rendered = render_markdown(summary, title=args.title)
    else:
        rendered = json.dumps(summary, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
