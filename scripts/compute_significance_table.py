"""Compute DeLong and paired-bootstrap significance between LeWM and a baseline.

This is a Phase P1 statistical-hardening utility. Given two episode-score CSVs
that share the SAME evaluation episodes (one for LeWM, one for a baseline) plus a
binary label column, it reports:

- AUROC for each method,
- paired bootstrap delta-AUROC with a 95% CI (pair-grouped),
- a DeLong test p-value for the AUROC difference.

It is intentionally read-only and artifact-driven: it never trains, never scores,
never touches locked test. It only consumes already-validated raw score rows and
emits a JSON summary plus an optional LaTeX significance row, ready to paste into
the paper. Wording remains "stronger observed separation" unless the DeLong
p-value is below the chosen alpha AND the bootstrap CI excludes zero.

CSV schema (both files): columns `source` (or another group key), `score`, and a
label column (`label` by default; 0/1 or Normal/Buggy). The two files must
contain the same set of (group_key, label) rows so the comparison is paired on
identical support. Combined score files can be narrowed with the
`--lewm-*` and `--baseline-*` filter flags.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from glitch_detection.statistics import delong_auroc_test, paired_bootstrap_delta


def _parse_label(value: str) -> int:
    text = value.strip().lower()
    if text in {"1", "1.0", "buggy", "positive", "pos", "true"}:
        return 1
    if text in {"0", "0.0", "normal", "negative", "neg", "false"}:
        return 0
    return int(float(value))


def _row_matches_filters(raw: dict[str, str], filters: dict[str, str | None]) -> bool:
    for column, expected in filters.items():
        if expected is not None and raw.get(column, "") != expected:
            return False
    return True


def _read_rows(
    path: Path,
    label_column: str,
    group_key: str,
    *,
    filters: dict[str, str | None] | None = None,
) -> list[dict[str, Any]]:
    filters = filters or {}
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, Any]] = []
        for raw in reader:
            if not _row_matches_filters(raw, filters):
                continue
            if label_column not in raw or "score" not in raw or group_key not in raw:
                raise ValueError(
                    f"{path} must contain '{group_key}', 'score', and '{label_column}' columns."
                )
            rows.append(
                {
                    group_key: raw[group_key],
                    "score": float(raw["score"]),
                    "label": _parse_label(raw[label_column]),
                }
            )
    if not rows:
        filter_text = ", ".join(f"{key}={value}" for key, value in filters.items() if value)
        suffix = f" matching filters ({filter_text})" if filter_text else ""
        raise ValueError(f"{path} contains no rows{suffix}.")
    return rows


def _aligned_labels(
    rows_a: list[dict[str, Any]],
    rows_b: list[dict[str, Any]],
    group_key: str,
) -> tuple[list[int], list[float], list[float]]:
    """Align two row lists on (group_key) and return labels, scores_a, scores_b."""
    index_b = {row[group_key]: row for row in rows_b}
    if len(index_b) != len(rows_b):
        raise ValueError("Baseline rows contain duplicate group keys; cannot align pairs.")
    labels: list[int] = []
    scores_a: list[float] = []
    scores_b: list[float] = []
    for row in rows_a:
        key = row[group_key]
        if key not in index_b:
            raise ValueError(f"Group {key!r} present in method A but missing in baseline.")
        partner = index_b[key]
        if partner["label"] != row["label"]:
            raise ValueError(f"Label mismatch for group {key!r} between the two files.")
        labels.append(row["label"])
        scores_a.append(row["score"])
        scores_b.append(partner["score"])
    return labels, scores_a, scores_b


def compute_significance(
    lewm_csv: Path,
    baseline_csv: Path,
    *,
    label_column: str = "label",
    group_key: str = "source",
    n_bootstrap: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
    lewm_filters: dict[str, str | None] | None = None,
    baseline_filters: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    rows_a = _read_rows(lewm_csv, label_column, group_key, filters=lewm_filters)
    rows_b = _read_rows(baseline_csv, label_column, group_key, filters=baseline_filters)
    labels, scores_a, scores_b = _aligned_labels(rows_a, rows_b, group_key)

    delong = delong_auroc_test(labels, scores_a, scores_b)
    boot = paired_bootstrap_delta(
        rows_a,
        rows_b,
        metric_name="auroc",
        group_key=group_key,
        n_bootstrap=n_bootstrap,
        seed=seed,
    )

    ci_excludes_zero = (
        boot["lower"] is not None
        and boot["upper"] is not None
        and (boot["lower"] > 0.0 or boot["upper"] < 0.0)
    )
    delong_significant = delong["p_value"] is not None and delong["p_value"] < alpha
    significant = bool(ci_excludes_zero and delong_significant)

    return {
        "auroc_lewm": delong["auroc_a"],
        "auroc_baseline": delong["auroc_b"],
        "delta_auroc_point": boot["point_delta"],
        "delta_auroc_ci_lower": boot["lower"],
        "delta_auroc_ci_upper": boot["upper"],
        "delong_z": delong["z"],
        "delong_p_value": delong["p_value"],
        "alpha": alpha,
        "ci_excludes_zero": ci_excludes_zero,
        "delong_significant": delong_significant,
        "significant": significant,
        "n_evaluation_episodes": len(labels),
        "n_bootstrap": n_bootstrap,
        "seed": seed,
        "group_key": group_key,
        "safe_wording": (
            "significantly outperforms"
            if significant
            else "shows stronger observed same-support separation than"
        ),
    }


def render_latex_row(summary: dict[str, Any], method_label: str, baseline_label: str) -> str:
    def f(value: float | None, digits: int = 4) -> str:
        return "---" if value is None else f"{value:.{digits}f}"

    delta = f(summary["delta_auroc_point"])
    lower = f(summary["delta_auroc_ci_lower"])
    upper = f(summary["delta_auroc_ci_upper"])
    p_value = f(summary["delong_p_value"])
    sig = "yes" if summary["significant"] else "no"
    return (
        f"{method_label} vs {baseline_label} & {f(summary['auroc_lewm'])} & "
        f"{f(summary['auroc_baseline'])} & {delta} & [{lower}, {upper}] & "
        f"{p_value} & {sig} \\\\"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute DeLong + paired-bootstrap significance between LeWM and a baseline."
    )
    parser.add_argument("--lewm-scores", required=True, type=Path)
    parser.add_argument("--baseline-scores", required=True, type=Path)
    parser.add_argument("--label-column", default="label")
    parser.add_argument("--group-key", default="source")
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--method-label", default="LeWM")
    parser.add_argument("--baseline-label", default="baseline")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    parser.add_argument("--lewm-method-family", default=None)
    parser.add_argument("--lewm-method", default=None)
    parser.add_argument("--lewm-window-scorer", default=None)
    parser.add_argument("--lewm-seed", default=None)
    parser.add_argument("--lewm-episode-aggregation", default=None)
    parser.add_argument("--baseline-method-family", default=None)
    parser.add_argument("--baseline-method", default=None)
    parser.add_argument("--baseline-window-scorer", default=None)
    parser.add_argument("--baseline-seed", default=None)
    parser.add_argument("--baseline-episode-aggregation", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = compute_significance(
        args.lewm_scores,
        args.baseline_scores,
        label_column=args.label_column,
        group_key=args.group_key,
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
        alpha=args.alpha,
        lewm_filters={
            "method_family": args.lewm_method_family,
            "method": args.lewm_method,
            "window_scorer": args.lewm_window_scorer,
            "seed": args.lewm_seed,
            "episode_aggregation": args.lewm_episode_aggregation,
        },
        baseline_filters={
            "method_family": args.baseline_method_family,
            "method": args.baseline_method,
            "window_scorer": args.baseline_window_scorer,
            "seed": args.baseline_seed,
            "episode_aggregation": args.baseline_episode_aggregation,
        },
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("LaTeX significance row:")
    print(render_latex_row(summary, args.method_label, args.baseline_label))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
