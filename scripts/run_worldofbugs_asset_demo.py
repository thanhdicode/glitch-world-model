from __future__ import annotations

from pathlib import Path

from PIL import Image

from glitch_detection.evaluate import evaluate_scores
from glitch_detection.frame_diff import score_manifest
from glitch_detection.plot_scores import plot_scores
from glitch_detection.preprocess import preprocess_input

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "external" / "world-of-bugs" / "docs" / "Reference" / "Examples" / "imgs"


def first_existing(paths: list[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError("None of the expected World of Bugs example images were found.")


def write_repeated_frames(frame_dir: Path, normal_image: Path, glitch_image: Path) -> None:
    frame_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(normal_image) as normal, Image.open(glitch_image) as glitch:
        normal_frame = normal.convert("RGB").resize((128, 128), Image.Resampling.BILINEAR)
        glitch_frame = glitch.convert("RGB").resize((128, 128), Image.Resampling.BILINEAR)

        for index in range(48):
            frame = glitch_frame if 20 <= index <= 27 else normal_frame
            frame.save(frame_dir / f"frame_{index:06d}.png")


def write_labels(labels_path: Path) -> None:
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    labels_path.write_text(
        "source,start_frame,end_frame,label\nworldofbugs_asset_frames,20,27,1\n",
        encoding="utf-8",
    )


def main() -> None:
    normal_image = first_existing([ASSET_DIR / "Maze-v0.png", ASSET_DIR / "World-v3.png"])
    glitch_image = first_existing(
        [
            ASSET_DIR / "Maze-v0-OutOfBounds.png",
            ASSET_DIR / "Maze-v0-OutOfBounds2.png",
            ASSET_DIR / "Maze-v0-InvalidShortcut.png",
            ASSET_DIR / "GettingStuck-v0.png",
        ]
    )

    frame_dir = ROOT / "data" / "raw" / "worldofbugs_asset_frames"
    labels_path = ROOT / "data" / "raw" / "worldofbugs_asset_labels.csv"
    processed_dir = ROOT / "data" / "processed" / "worldofbugs_asset"
    scores_path = ROOT / "outputs" / "worldofbugs_asset_scores.csv"
    metrics_path = ROOT / "outputs" / "worldofbugs_asset_metrics.json"
    plot_path = ROOT / "outputs" / "worldofbugs_asset_scores.png"

    write_repeated_frames(frame_dir, normal_image, glitch_image)
    write_labels(labels_path)
    manifest_path = preprocess_input(
        input_path=frame_dir,
        output_dir=processed_dir,
        clip_length=8,
        stride=4,
        size=128,
        fps=30.0,
    )
    score_manifest(manifest_path, scores_path)
    metrics = evaluate_scores(scores_path, labels_path, metrics_path, allow_fit_threshold=True)
    plot_scores(scores_path, plot_path)

    print(f"Normal image: {normal_image}")
    print(f"Glitch image: {glitch_image}")
    print(f"Manifest:     {manifest_path}")
    print(f"Scores:       {scores_path}")
    print(f"Metrics:      {metrics_path}")
    print(f"Plot:         {plot_path}")
    print(f"F1:           {metrics['f1']:.3f}")
    print(f"AUROC:        {metrics['auroc']:.3f}")


if __name__ == "__main__":
    main()
