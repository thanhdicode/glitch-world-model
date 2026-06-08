from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ROWS_URL = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=glitchbench%2FGlitchBench&config=default&split=validation"
    "&offset={offset}&length={length}"
)
NORMAL_IMAGE = (
    ROOT / "external" / "world-of-bugs" / "docs" / "Reference" / "Examples" / "imgs" / "Maze-v0.png"
)


def fetch_rows(limit: int, offset: int) -> list[dict]:
    with urllib.request.urlopen(
        ROWS_URL.format(offset=offset, length=limit), timeout=60
    ) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["rows"]


def download_image(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, output_path)


def save_resized(source: Path, destination: Path, size: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.convert("RGB").resize((size, size), Image.Resampling.BILINEAR).save(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a lightweight GlitchBench image subset.")
    parser.add_argument(
        "--limit", type=int, default=12, help="Number of GlitchBench samples to download."
    )
    parser.add_argument("--offset", type=int, default=0, help="Dataset viewer row offset.")
    parser.add_argument("--size", type=int, default=128, help="Output frame size.")
    parser.add_argument("--frames-per-sample", type=int, default=8)
    args = parser.parse_args()

    rows = fetch_rows(args.limit, args.offset)
    image_dir = ROOT / "data" / "raw" / "glitchbench_subset_images"
    frame_dir = ROOT / "data" / "raw" / "glitchbench_subset_frames"
    labels_path = ROOT / "data" / "raw" / "glitchbench_subset_labels.csv"
    metadata_path = ROOT / "data" / "raw" / "glitchbench_subset_metadata.csv"

    frame_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    frame_index = 0
    label_rows: list[dict[str, str | int]] = []
    metadata_rows: list[dict[str, str | int]] = []

    for sample_index, item in enumerate(rows):
        row = item["row"]
        image_url = row["image"]["src"]
        image_path = image_dir / f"glitch_{sample_index:04d}.jpg"
        download_image(image_url, image_path)

        normal_start = frame_index
        for _ in range(args.frames_per_sample):
            save_resized(NORMAL_IMAGE, frame_dir / f"frame_{frame_index:06d}.png", args.size)
            frame_index += 1

        glitch_start = frame_index
        for _ in range(args.frames_per_sample):
            save_resized(image_path, frame_dir / f"frame_{frame_index:06d}.png", args.size)
            frame_index += 1
        glitch_end = frame_index - 1

        label_rows.append(
            {
                "source": "glitchbench_subset_frames",
                "start_frame": glitch_start,
                "end_frame": glitch_end,
                "label": 1,
            }
        )
        metadata_rows.append(
            {
                "sample_index": sample_index,
                "row_idx": item["row_idx"],
                "id": row.get("id", ""),
                "game": row.get("game", ""),
                "glitch_type": row.get("glitch-type", ""),
                "normal_start": normal_start,
                "glitch_start": glitch_start,
                "glitch_end": glitch_end,
                "image_path": str(image_path),
            }
        )

    with labels_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "start_frame", "end_frame", "label"])
        writer.writeheader()
        writer.writerows(label_rows)

    with metadata_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "sample_index",
                "row_idx",
                "id",
                "game",
                "glitch_type",
                "normal_start",
                "glitch_start",
                "glitch_end",
                "image_path",
            ],
        )
        writer.writeheader()
        writer.writerows(metadata_rows)

    print(f"Frames:   {frame_dir}")
    print(f"Labels:   {labels_path}")
    print(f"Metadata: {metadata_path}")
    print(
        "Run: python -m glitch_detection.run_baseline "
        "--input data\\raw\\glitchbench_subset_frames "
        "--labels data\\raw\\glitchbench_subset_labels.csv "
        "--name glitchbench_subset_feature "
        "--clip-length 8 --stride 8 --size 128 --scorer feature_distance"
    )


if __name__ == "__main__":
    main()
