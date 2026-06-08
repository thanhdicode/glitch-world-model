from __future__ import annotations

from pathlib import Path

from PIL import Image

from glitch_detection.evaluate import evaluate_scores
from glitch_detection.frame_diff import score_manifest
from glitch_detection.plot_scores import plot_scores
from glitch_detection.preprocess import preprocess_input

ROOT = Path(__file__).resolve().parents[1]


def write_synthetic_frames(frame_dir: Path) -> None:
    frame_dir.mkdir(parents=True, exist_ok=True)
    for index in range(40):
        value = 220 if 16 <= index <= 23 else 30
        Image.new("RGB", (64, 64), color=(value, value, value)).save(
            frame_dir / f"frame_{index:06d}.png"
        )


def write_synthetic_labels(labels_path: Path) -> None:
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    labels_path.write_text(
        "source,start_frame,end_frame,label\nsynthetic_frames,16,23,1\n",
        encoding="utf-8",
    )


def main() -> None:
    frame_dir = ROOT / "data" / "raw" / "synthetic_frames"
    labels_path = ROOT / "data" / "raw" / "synthetic_labels.csv"
    processed_dir = ROOT / "data" / "processed" / "synthetic"
    scores_path = ROOT / "outputs" / "synthetic_scores.csv"
    metrics_path = ROOT / "outputs" / "synthetic_metrics.json"
    plot_path = ROOT / "outputs" / "synthetic_scores.png"

    write_synthetic_frames(frame_dir)
    write_synthetic_labels(labels_path)
    manifest_path = preprocess_input(
        input_path=frame_dir,
        output_dir=processed_dir,
        clip_length=8,
        stride=4,
        size=64,
        fps=30.0,
    )
    score_manifest(manifest_path, scores_path)
    metrics = evaluate_scores(scores_path, labels_path, metrics_path)
    plot_scores(scores_path, plot_path)

    print(f"Manifest: {manifest_path}")
    print(f"Scores:   {scores_path}")
    print(f"Metrics:  {metrics_path}")
    print(f"Plot:     {plot_path}")
    print(f"F1:       {metrics['f1']:.3f}")
    print(f"AUROC:    {metrics['auroc']:.3f}")


if __name__ == "__main__":
    main()
