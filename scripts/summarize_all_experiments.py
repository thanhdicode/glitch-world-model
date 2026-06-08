from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


EXPERIMENTS = [
    {
        "dataset": "Visual Toy",
        "scorer": "FrameDiff",
        "metrics": "outputs/my_experiment_metrics.json",
        "plot": "outputs/my_experiment_scores.png",
        "note": "Color/intensity jump toy glitch.",
    },
    {
        "dataset": "Visual Toy",
        "scorer": "FeatureDistance",
        "metrics": "outputs/my_experiment_feature_metrics.json",
        "plot": "outputs/my_experiment_feature_scores.png",
        "note": "Color feature distance from normal clips.",
    },
    {
        "dataset": "Visual Toy",
        "scorer": "MiniLatent",
        "metrics": "outputs/my_mini_latent_experiment_metrics.json",
        "plot": "outputs/my_mini_latent_experiment_scores.png",
        "note": "Velocity-aware PCA latent transition baseline.",
    },
    {
        "dataset": "Dynamics Easy",
        "scorer": "FrameDiff",
        "metrics": "outputs/dynamics_frame_diff_metrics.json",
        "plot": "outputs/dynamics_frame_diff_scores.png",
        "note": "Clear teleport/wall-crossing dynamics glitch.",
    },
    {
        "dataset": "Dynamics Easy",
        "scorer": "FeatureDistance",
        "metrics": "outputs/dynamics_feature_distance_metrics.json",
        "plot": "outputs/dynamics_feature_distance_scores.png",
        "note": "Clear visual and positional change.",
    },
    {
        "dataset": "Dynamics Easy",
        "scorer": "MiniLatent",
        "metrics": "outputs/dynamics_mini_latent_metrics.json",
        "plot": "outputs/dynamics_mini_latent_scores.png",
        "note": "Latent transition catches obvious dynamics violation.",
    },
    {
        "dataset": "Hard Dynamics",
        "scorer": "FrameDiff",
        "metrics": "outputs/hard_frame_diff_metrics.json",
        "plot": "outputs/hard_frame_diff_scores.png",
        "note": "Noisier normal motion with short teleport glitches.",
    },
    {
        "dataset": "Hard Dynamics",
        "scorer": "FeatureDistance",
        "metrics": "outputs/hard_feature_distance_metrics.json",
        "plot": "outputs/hard_feature_distance_scores.png",
        "note": "Still strong because generated glitch includes visible state shift.",
    },
    {
        "dataset": "Hard Dynamics",
        "scorer": "MiniLatent",
        "metrics": "outputs/hard_mini_latent_metrics.json",
        "plot": "outputs/hard_mini_latent_scores.png",
        "note": "Best proxy for LeWM hypothesis; velocity-aware transition reduces false positives.",
    },
    {
        "dataset": "GlitchBench Subset",
        "scorer": "FrameDiff",
        "metrics": "outputs/glitchbench_subset_frame_diff_metrics.json",
        "plot": "outputs/glitchbench_subset_frame_diff_scores.png",
        "note": "Static repeated image clips; frame difference is weak by design.",
    },
    {
        "dataset": "GlitchBench Subset",
        "scorer": "FeatureDistance",
        "metrics": "outputs/glitchbench_subset_feature_distance_metrics.json",
        "plot": "outputs/glitchbench_subset_feature_distance_scores.png",
        "note": "Lightweight real-world GlitchBench image subset via dataset viewer API.",
    },
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def row_for(entry: dict[str, str]) -> list[str]:
    metrics_path = ROOT / entry["metrics"]
    if not metrics_path.exists():
        return [
            entry["dataset"],
            entry["scorer"],
            "missing",
            "missing",
            "missing",
            "missing",
            "missing",
            entry["note"],
        ]
    metrics = read_json(metrics_path)
    return [
        entry["dataset"],
        entry["scorer"],
        fmt(metrics.get("precision")),
        fmt(metrics.get("recall")),
        fmt(metrics.get("f1")),
        fmt(metrics.get("auroc")),
        fmt(metrics.get("threshold")),
        entry["note"],
    ]


def main() -> None:
    output_path = ROOT / "outputs" / "summary_all_experiments.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Summary: Preliminary Glitch Detection Experiments",
        "",
        "This table summarizes lightweight baselines before integrating a full LeWorldModel checkpoint.",
        "",
        "| Dataset | Scorer | Precision | Recall | F1 | AUROC | Threshold | Note |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for entry in EXPERIMENTS:
        lines.append("| " + " | ".join(row_for(entry)) + " |")

    lines.extend(
        [
            "",
            "## Takeaways",
            "",
            "- FrameDiff and FeatureDistance are strong on the generated toy datasets because glitches are visually salient.",
            "- MiniLatent is the most relevant proxy for the LeWM hypothesis because it scores latent transition errors.",
            "- The velocity-aware MiniLatent update improves dynamics modeling by predicting from both latent state and latent velocity.",
            "- On Hard Dynamics, MiniLatent now matches the simpler visual baselines on generated data, supporting the latent-dynamics hypothesis before full LeWM integration.",
            "- On the lightweight GlitchBench image subset, FrameDiff is weak because repeated static images contain no temporal motion, while FeatureDistance provides a useful image-level baseline.",
            "- The next research step is to replace MiniLatent with LeWM latent prediction error while keeping the same preprocessing, scoring, evaluation, and reporting pipeline.",
            "",
            "## Plot Files",
            "",
        ]
    )
    for entry in EXPERIMENTS:
        plot_path = ROOT / entry["plot"]
        if plot_path.exists():
            lines.append(f"- {entry['dataset']} / {entry['scorer']}: `{entry['plot']}`")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote summary: {output_path}")


if __name__ == "__main__":
    main()
