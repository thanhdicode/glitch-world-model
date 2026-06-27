from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "paper" / "tables"

TEMPGLITCH_METRICS = Path("outputs/tempglitch_followup_pair_disjoint/followup_metrics.json")
K1_SUMMARY = Path("outputs/learned_baselines_k1/analysis/k1_followup_summary.json")
K2_SUMMARY = Path("outputs/glitchbench_k2_intake/k2_glitchbench_intake_summary.json")
K3_SUMMARY = Path("outputs/k3_ablation_intake/k3_ablation_intake_summary.json")
QUALITATIVE_TIMELINES = Path("outputs/demo_timelines/qualitative_timeline_receipt.json")


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_metric(value: str | float | int, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"


def fmt_signed(value: float, digits: int = 6) -> str:
    return f"{value:+.{digits}f}"


def latex_escape(text: str) -> str:
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
    )


def tt(text: str) -> str:
    return rf"\texttt{{{latex_escape(text)}}}"


def row_ci(row: dict[str, Any]) -> str:
    return (
        f"AUROC [{fmt_metric(row['auroc_ci_lower'])}, {fmt_metric(row['auroc_ci_upper'])}]; "
        f"F1 [{fmt_metric(row['f1_ci_lower'])}, {fmt_metric(row['f1_ci_upper'])}]"
    )


def best_by_auroc(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return max(rows, key=lambda row: float(row["auroc"]))


def find_method_row(
    rows_by_method: dict[str, dict[str, Any]],
    method_name: str,
) -> dict[str, Any]:
    try:
        return rows_by_method[method_name]
    except KeyError as exc:
        available = ", ".join(sorted(rows_by_method))
        raise KeyError(f"missing method '{method_name}' in summary; found: {available}") from exc


def render_tempglitch_table(root: Path) -> str:
    metrics = load_json(root / TEMPGLITCH_METRICS)
    assert isinstance(metrics, dict)
    results = metrics["results"]
    lewm_rows = [row for row in results if row["method_family"] == "lewm"]
    baseline_rows = [row for row in results if row["method_family"] == "baseline"]
    best_lewm = best_by_auroc(lewm_rows)
    best_baseline = best_by_auroc(baseline_rows)
    normal_count = metrics["manifest_summary"]["evaluation_normal_episode_count"]
    buggy_count = metrics["manifest_summary"]["evaluation_buggy_episode_count"]
    calibration_count = metrics["manifest_summary"]["calibration_episode_count"]

    return rf"""\begin{{table}}[t]
\caption{{Frozen pair-disjoint non-locked TempGlitch follow-up. Every row uses the same {normal_count}
normal-negative and {buggy_count} buggy-positive evaluation episodes; thresholds use {calibration_count}
calibration-normal episodes.}}
\label{{tab:r5-bounded-results}}
\centering
\scriptsize
\begin{{tabularx}}{{\textwidth}}{{@{{}}lXrrrrrrrX@{{}}}}
\toprule
Family & Configuration & AUROC & AUPRC & F1 & Prec. & Recall & Bal. acc. & FPR@95 & 95\% CI \\
\midrule
LeWM & seed{best_lewm["seed"]} {tt(best_lewm["window_scorer"])} + episode {tt(best_lewm["episode_aggregation"])} & {fmt_metric(best_lewm["auroc"])} & {fmt_metric(best_lewm["auprc"])} & {fmt_metric(best_lewm["f1"])} & {fmt_metric(best_lewm["precision"])} & {fmt_metric(best_lewm["recall"])} & {fmt_metric(best_lewm["balanced_accuracy"])} & {fmt_metric(best_lewm["fpr_at_95_tpr"])} & {row_ci(best_lewm)} \\
Baseline & {tt(best_baseline["method"])} + episode {tt(best_baseline["episode_aggregation"])} & {fmt_metric(best_baseline["auroc"])} & {fmt_metric(best_baseline["auprc"])} & {fmt_metric(best_baseline["f1"])} & {fmt_metric(best_baseline["precision"])} & {fmt_metric(best_baseline["recall"])} & {fmt_metric(best_baseline["balanced_accuracy"])} & {fmt_metric(best_baseline["fpr_at_95_tpr"])} & {row_ci(best_baseline)} \\
\bottomrule
\end{{tabularx}}
\end{{table}}
"""


def render_k1_table(root: Path) -> str:
    summary = load_json(root / K1_SUMMARY)
    assert isinstance(summary, dict)
    rows_by_method = summary["best_rows_by_method"]
    video_autoencoder = find_method_row(rows_by_method, "video_autoencoder")
    cnn_lstm = find_method_row(rows_by_method, "cnn_lstm")
    video_transformer = find_method_row(rows_by_method, "video_transformer")
    best_lewm = summary["best_lewm_row"]
    best_frame_diff = summary["best_frame_diff_row"]
    best_feature_distance = summary["best_feature_distance_row"]
    support = summary["canonical_support"]

    def learned_row(row: dict[str, Any]) -> str:
        return (
            f"Learned baseline & {tt(row['method'])} + episode "
            f"{tt(row['episode_aggregation'])} & {fmt_metric(row['auroc'])} & "
            f"{fmt_metric(row['auprc'])} & {fmt_metric(row['f1'])} & "
            f"{fmt_metric(row['precision'])} & {fmt_metric(row['recall'])} & "
            f"{fmt_metric(row['balanced_accuracy'])} & {fmt_metric(row['fpr_at_95_tpr'])} & "
            f"{row_ci(row)} \\\\"
        )

    return rf"""\begin{{table}}[t]
\caption{{K1 learned baselines on the frozen non-locked TempGlitch follow-up support. Every row
uses the same {support["calibration_episode_count"]} calibration-normal episodes and the same
{support["evaluation_normal_episode_count"]} normal-negative / {support["evaluation_buggy_episode_count"]}
buggy-positive evaluation episodes. Learned rows report the best aggregation per method over
\texttt{{mean}}, \texttt{{max}}, and \texttt{{top2\_mean}}.}}
\label{{tab:k1-learned-baselines}}
\centering
\scriptsize
\begin{{tabularx}}{{\textwidth}}{{@{{}}lXrrrrrrrX@{{}}}}
\toprule
Family & Configuration & AUROC & AUPRC & F1 & Prec. & Recall & Bal. acc. & FPR@95 & 95\% CI \\
\midrule
LeWM & seed{best_lewm["seed"]} {tt(best_lewm["window_scorer"])} + episode {tt(best_lewm["episode_aggregation"])} & {fmt_metric(best_lewm["auroc"])} & {fmt_metric(best_lewm["auprc"])} & {fmt_metric(best_lewm["f1"])} & {fmt_metric(best_lewm["precision"])} & {fmt_metric(best_lewm["recall"])} & {fmt_metric(best_lewm["balanced_accuracy"])} & {fmt_metric(best_lewm["fpr_at_95_tpr"])} & {row_ci(best_lewm)} \\
Simple baseline & {tt(best_frame_diff["method"])} + episode {tt(best_frame_diff["episode_aggregation"])} & {fmt_metric(best_frame_diff["auroc"])} & {fmt_metric(best_frame_diff["auprc"])} & {fmt_metric(best_frame_diff["f1"])} & {fmt_metric(best_frame_diff["precision"])} & {fmt_metric(best_frame_diff["recall"])} & {fmt_metric(best_frame_diff["balanced_accuracy"])} & {fmt_metric(best_frame_diff["fpr_at_95_tpr"])} & {row_ci(best_frame_diff)} \\
Simple baseline & {tt(best_feature_distance["method"])} + episode {tt(best_feature_distance["episode_aggregation"])} & {fmt_metric(best_feature_distance["auroc"])} & {fmt_metric(best_feature_distance["auprc"])} & {fmt_metric(best_feature_distance["f1"])} & {fmt_metric(best_feature_distance["precision"])} & {fmt_metric(best_feature_distance["recall"])} & {fmt_metric(best_feature_distance["balanced_accuracy"])} & {fmt_metric(best_feature_distance["fpr_at_95_tpr"])} & {row_ci(best_feature_distance)} \\
{learned_row(video_autoencoder)}
{learned_row(cnn_lstm)}
{learned_row(video_transformer)}
\bottomrule
\end{{tabularx}}
\end{{table}}
"""


def render_k2_table(root: Path) -> str:
    summary = load_json(root / K2_SUMMARY)
    assert isinstance(summary, dict)
    rows = summary["results"]

    desired_order = [
        ("frame_diff", ""),
        ("feature_distance", ""),
        ("video_autoencoder", ""),
        ("cnn_lstm", ""),
        ("video_transformer", ""),
    ]
    ordered_rows = []
    for method, aggregation in desired_order:
        ordered_rows.append(
            next(
                row
                for row in rows
                if row["method"] == method and row.get("aggregation", "") == aggregation
            )
        )

    best_lewm = summary["best_lewm_row"]
    validation_count = summary["bundle_validation"]["split_summary"]["validation_source_count"]

    body = "\n".join(
        (
            f"{tt(row['method'])} & {fmt_metric(row['auroc'], 3)} & {fmt_metric(row['auprc'], 3)} & "
            f"{fmt_metric(row['f1'], 3)} & {fmt_metric(row['balanced_accuracy'], 3)} & "
            f"{fmt_metric(row['fpr_at_95_tpr'], 3)} \\\\"
        )
        for row in ordered_rows
    )

    return rf"""\begin{{table}}[t]
\centering
\caption{{Validated K2 GlitchBench benchmark results on the frozen image-level synthetic-normal
split ({validation_count} validation clips).}}
\label{{tab:glitchbench-benchmark}}
\small
\begin{{tabular}}{{lccccc}}
\toprule
Method & AUROC & AUPRC & F1 & Balanced accuracy & FPR@95TPR \\
\midrule
{body}
{tt("lewm")} best row & {fmt_metric(best_lewm["auroc"], 3)} & {fmt_metric(best_lewm["auprc"], 3)} & {fmt_metric(best_lewm["f1"], 3)} & {fmt_metric(best_lewm["balanced_accuracy"], 3)} & {fmt_metric(best_lewm["fpr_at_95_tpr"], 3)} \\
\bottomrule
\end{{tabular}}
\end{{table}}
"""


def resolve_k3_bundle_root(root: Path, summary: dict[str, Any]) -> Path:
    bundle_root = Path(summary["bundle_root"])
    if bundle_root.exists():
        return bundle_root

    candidate = root / summary["bundle_root"]
    if candidate.exists():
        return candidate

    raise FileNotFoundError(
        f"K3 ablation bundle is unavailable. Expected either '{bundle_root}' or '{candidate}'."
    )


def k3_prediction_loss(history_path: Path) -> float:
    history = load_json(history_path)
    assert isinstance(history, list)
    prediction_means = []
    for record in history:
        batches = record["batches"]
        prediction_means.append(sum(batch["prediction_loss"] for batch in batches) / len(batches))
    return min(prediction_means)


def render_k3_table(root: Path) -> str:
    summary = load_json(root / K3_SUMMARY)
    assert isinstance(summary, dict)
    bundle_root = resolve_k3_bundle_root(root, summary)
    receipt = load_json(bundle_root / "r6_ablation_receipt.json")
    assert isinstance(receipt, dict)

    variants = {}
    grouped: dict[tuple[bool, str], list[tuple[float, float]]] = defaultdict(list)
    for variant in receipt["executed_variants"]:
        name = variant["variant_name"]
        training = variant["training_metadata"]
        prediction_loss = k3_prediction_loss(bundle_root / name / "validation_history.json")
        total_loss = float(training["best_validation_loss"])
        variants[name] = {
            "seed": variant["seed"],
            "sigreg_enabled": training["sigreg_enabled"],
            "action_mode": training["action_mode"],
            "best_total_loss": total_loss,
            "best_prediction_loss": prediction_loss,
        }
        grouped[(training["sigreg_enabled"], training["action_mode"])].append(
            (total_loss, prediction_loss)
        )

    sigreg_rows = []
    action_rows = []
    for pair in receipt["controlled_pairs"]:
        control = variants[pair["control_variant"]]
        treatment = variants[pair["treatment_variant"]]
        delta = treatment["best_prediction_loss"] - control["best_prediction_loss"]
        if pair["pair_type"] == "sigreg":
            sigreg_rows.append((pair["seed"], pair["action_mode"], delta))
        elif pair["pair_type"] == "action_conditioning":
            action_rows.append((pair["seed"], pair["sigreg_enabled"], delta))

    def mean_group(sigreg_enabled: bool, action_mode: str) -> tuple[float, float]:
        values = grouped[(sigreg_enabled, action_mode)]
        total = sum(value[0] for value in values) / len(values)
        prediction = sum(value[1] for value in values) / len(values)
        return total, prediction

    off_real = mean_group(False, "real")
    off_zero = mean_group(False, "zero_action")
    on_real = mean_group(True, "real")
    on_zero = mean_group(True, "zero_action")

    sigreg_rows.sort(key=lambda row: (row[0], row[1]))
    action_rows.sort(key=lambda row: (row[0], row[1]))

    sigreg_real = {seed: delta for seed, action_mode, delta in sigreg_rows if action_mode == "real"}
    sigreg_zero = {
        seed: delta for seed, action_mode, delta in sigreg_rows if action_mode == "zero_action"
    }
    action_on = {seed: delta for seed, enabled, delta in action_rows if enabled}
    action_off = {seed: delta for seed, enabled, delta in action_rows if not enabled}

    seed_rows = sorted({seed for seed, _, _ in sigreg_rows})

    group_panel = "\n".join(
        [
            f"off & real & {fmt_metric(off_real[0], 6)} & {fmt_metric(off_real[1], 6)} \\\\",
            f"off & zero\\_action & {fmt_metric(off_zero[0], 6)} & {fmt_metric(off_zero[1], 6)} \\\\",
            f"on & real & {fmt_metric(on_real[0], 6)} & {fmt_metric(on_real[1], 6)} \\\\",
            f"on & zero\\_action & {fmt_metric(on_zero[0], 6)} & {fmt_metric(on_zero[1], 6)} \\\\",
        ]
    )
    sigreg_panel = "\n".join(
        f"{seed} & {fmt_signed(sigreg_real[seed])} & {fmt_signed(sigreg_zero[seed])} \\\\"
        for seed in seed_rows
    )
    action_panel = "\n".join(
        f"{seed} & {fmt_signed(action_on[seed])} & {fmt_signed(action_off[seed])} \\\\"
        for seed in seed_rows
    )

    return rf"""\begin{{table}}[t]
\centering
\caption{{Validated K3 mechanistic ablation readout on the frozen validation-normal support. Lower
prediction loss is better; SIGReg and action comparisons remain bounded mechanistic diagnostics,
not detection metrics.}}
\label{{tab:k3-ablation-results}}
\small
\textbf{{Panel A: group means}}
\begin{{tabular}}{{llrr}}
\toprule
SIGReg & Action mode & Mean best total val. loss & Mean best prediction loss \\
\midrule
{group_panel}
\bottomrule
\end{{tabular}}

\medskip
\textbf{{Panel B: SIGReg-on minus SIGReg-off prediction-loss delta}}
\begin{{tabular}}{{lrr}}
\toprule
Seed & Real-action delta & Zero-action delta \\
\midrule
{sigreg_panel}
\bottomrule
\end{{tabular}}

\medskip
\textbf{{Panel C: real-action minus zero-action prediction-loss delta}}
\begin{{tabular}}{{lrr}}
\toprule
Seed & SIGReg-on delta & SIGReg-off delta \\
\midrule
{action_panel}
\bottomrule
\end{{tabular}}
\end{{table}}
"""


def render_qualitative_table(root: Path) -> str:
    receipt = load_json(root / QUALITATIVE_TIMELINES)
    assert isinstance(receipt, dict)
    selected = receipt["selected_config"]
    plots = receipt["plots"]
    plot_rows = "\n".join(
        (
            f"{plot['label']} & {latex_escape(plot['category'])} & "
            f"{latex_escape(plot['source_episode_id'])} & {plot['window_count']} & "
            f"{plot['episode_score']:.3f} \\\\"
        )
        for plot in plots
    )

    return rf"""\begin{{table}}[t]
\centering
\caption{{Qualitative-only P6 surprise timelines produced from the frozen non-locked TempGlitch
follow-up artifacts using seed{selected["seed"]} {tt(selected["window_scorer"])} with
{tt(selected["episode_aggregation"])} aggregation. No temporal-localization metric is claimed.}}
\label{{tab:qualitative-timelines}}
\scriptsize
\begin{{tabularx}}{{\textwidth}}{{@{{}}l l X r r@{{}}}}
\toprule
Label & Category & Source episode & Windows & Episode score \\
\midrule
{plot_rows}
\bottomrule
\end{{tabularx}}
\end{{table}}
"""


def write_tables(output_root: Path, root: Path = ROOT) -> list[Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    payloads = {
        "r5_bounded_results.tex": render_tempglitch_table(root),
        "k1_learned_baselines.tex": render_k1_table(root),
        "glitchbench_benchmark.tex": render_k2_table(root),
        "k3_ablation_results.tex": render_k3_table(root),
        "qualitative_timeline_summary.tex": render_qualitative_table(root),
    }
    written: list[Path] = []
    for name, content in payloads.items():
        path = output_root / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate paper tables from validated TempGlitch, K1, K2, K3, and P6 artifacts."
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root containing outputs/ and docs/.",
    )
    args = parser.parse_args(argv)
    for path in write_tables(args.output_root, root=args.root):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
