from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Sequence


def plot_series(
    values: Sequence[float],
    output_path: Path,
    *,
    x_values: Sequence[float] | None = None,
    threshold: float | None = None,
    title: str = "LeWM latent-surprise timeline",
    x_label: str = "Clip index",
    y_label: str = "Surprise score",
    qualitative_note: str | None = None,
) -> Path:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        plt = None
    if not values:
        raise ValueError("Cannot plot an empty surprise timeline.")
    x_axis = list(range(len(values))) if x_values is None else list(x_values)
    if len(x_axis) != len(values):
        raise ValueError("x_values must align 1:1 with the surprise values.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if plt is not None:
        figure, axis = plt.subplots(figsize=(10, 4))
        axis.plot(x_axis, values, linewidth=1.5, color="#1f4b99")
        if threshold is not None:
            axis.axhline(
                threshold,
                linestyle="--",
                linewidth=1.1,
                color="#b22222",
                label=f"threshold={threshold:.6g}",
            )
            axis.legend(loc="upper right")
        axis.set_title(title)
        axis.set_xlabel(x_label)
        axis.set_ylabel(y_label)
        if qualitative_note:
            axis.text(
                0.01,
                0.98,
                qualitative_note,
                transform=axis.transAxes,
                ha="left",
                va="top",
                fontsize=8,
                bbox={"facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.85},
            )
        figure.tight_layout()
        figure.savefig(output_path, dpi=160)
        plt.close(figure)
        return output_path

    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("Timeline plotting requires matplotlib or Pillow.") from exc

    width = 1200
    height = 500
    left = 70
    right = width - 30
    top = 55
    bottom = height - 70
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((left, 15), title, fill="#111111")
    draw.text((left, height - 25), x_label, fill="#333333")
    draw.text((10, top), y_label, fill="#333333")
    if qualitative_note:
        draw.text((left, top + 5), qualitative_note, fill="#555555")

    min_x = float(min(x_axis))
    max_x = float(max(x_axis)) if len(x_axis) > 1 else float(min(x_axis) + 1.0)
    min_y = float(min(values))
    max_y = float(max(values))
    if threshold is not None:
        min_y = min(min_y, threshold)
        max_y = max(max_y, threshold)
    if max_y == min_y:
        max_y += 1.0

    def _scale_x(value: float) -> float:
        return left + ((value - min_x) / (max_x - min_x)) * (right - left)

    def _scale_y(value: float) -> float:
        return bottom - ((value - min_y) / (max_y - min_y)) * (bottom - top)

    draw.line((left, top, left, bottom), fill="#666666", width=1)
    draw.line((left, bottom, right, bottom), fill="#666666", width=1)
    points = [(_scale_x(float(x)), _scale_y(float(y))) for x, y in zip(x_axis, values)]
    if len(points) == 1:
        x_pos, y_pos = points[0]
        draw.ellipse((x_pos - 2, y_pos - 2, x_pos + 2, y_pos + 2), fill="#1f4b99")
    else:
        draw.line(points, fill="#1f4b99", width=2)
    if threshold is not None:
        y_pos = _scale_y(float(threshold))
        draw.line((left, y_pos, right, y_pos), fill="#b22222", width=1)
        draw.text((right - 180, max(top, y_pos - 18)), f"threshold={threshold:.6g}", fill="#b22222")
    image.save(output_path)
    return output_path


def plot_scores(scores_path: Path, output_path: Path) -> Path:
    with scores_path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("Cannot plot an empty scores.csv.")
    values = [float(row["score"]) for row in rows]
    return plot_series(values, output_path)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plot LeWM scores without changing CSV format.")
    parser.add_argument("--scores", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    print(plot_scores(args.scores, args.output))


if __name__ == "__main__":
    main()
