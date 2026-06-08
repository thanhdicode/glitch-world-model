from __future__ import annotations

from pathlib import Path

from create_hard_dynamics_dataset import main as create_hard_dynamics_dataset

from glitch_detection.compare_experiments import build_comparison_rows, write_comparison_markdown
from glitch_detection.dataset_report import build_report, write_markdown_report
from glitch_detection.run_baseline import run_baseline

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    create_hard_dynamics_dataset()
    input_path = ROOT / "data" / "raw" / "hard_dynamics_frames"
    labels_path = ROOT / "data" / "raw" / "hard_dynamics_labels.csv"

    experiments = [
        ("HardFrameDiff", "hard_frame_diff", "frame_diff"),
        ("HardFeatureDistance", "hard_feature_distance", "feature_distance"),
        ("HardMiniLatent", "hard_mini_latent", "mini_latent"),
    ]

    metric_entries: list[tuple[str, Path]] = []
    for display_name, experiment_name, scorer in experiments:
        outputs = run_baseline(
            input_path=input_path,
            labels_path=labels_path,
            experiment_name=experiment_name,
            clip_length=16,
            stride=4,
            size=128,
            fps=30.0,
            data_dir=ROOT / "data" / "processed",
            outputs_dir=ROOT / "outputs",
            scorer_name=scorer,
        )
        report = build_report(
            name=experiment_name,
            manifest_path=outputs["manifest"],
            labels_path=labels_path,
            scores_path=outputs["scores"],
            metrics_path=outputs["metrics"],
        )
        write_markdown_report(report, ROOT / "outputs" / f"{experiment_name}_report.md")
        metric_entries.append((display_name, outputs["metrics"]))

    rows = build_comparison_rows(metric_entries)
    comparison_path = ROOT / "outputs" / "hard_dynamics_comparison.md"
    write_comparison_markdown(rows, comparison_path)

    print(f"Comparison: {comparison_path}")
    for row in rows:
        print(
            f"{row['name']}: F1={row.get('f1'):.3f}, "
            f"AUROC={row.get('auroc'):.3f}, Precision={row.get('precision'):.3f}, "
            f"Recall={row.get('recall'):.3f}"
        )


if __name__ == "__main__":
    main()
