from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def draw_frame(index: int, glitch: bool) -> Image.Image:
    image = Image.new("RGB", (160, 120), color=(24, 28, 36))
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 92, 160, 120), fill=(54, 70, 54))
    draw.rectangle((20, 70, 140, 92), fill=(88, 88, 92))
    draw.rectangle((36, 56, 64, 70), fill=(120, 105, 80))
    draw.rectangle((98, 50, 126, 70), fill=(80, 105, 120))

    player_x = 12 + (index * 3) % 110
    player_y = 76
    if glitch:
        player_y = 18 if index % 2 == 0 else 6
        player_x = 118 if index % 3 == 0 else player_x
        draw.line((player_x, 0, player_x + 18, 119), fill=(255, 60, 80), width=3)
        draw.rectangle((4, 4, 52, 18), outline=(255, 60, 80), width=2)
        draw.text((8, 6), "GLITCH", fill=(255, 180, 180))

    draw.ellipse((player_x, player_y, player_x + 12, player_y + 12), fill=(80, 180, 255))
    draw.rectangle((player_x + 3, player_y + 12, player_x + 9, player_y + 24), fill=(80, 180, 255))
    return image


def main() -> None:
    frame_dir = ROOT / "data" / "raw" / "my_frames"
    labels_path = ROOT / "data" / "raw" / "my_labels.csv"
    frame_dir.mkdir(parents=True, exist_ok=True)
    labels_path.parent.mkdir(parents=True, exist_ok=True)

    glitch_ranges = [(20, 31), (52, 61)]
    for index in range(80):
        glitch = any(start <= index <= end for start, end in glitch_ranges)
        draw_frame(index, glitch).save(frame_dir / f"frame_{index:06d}.png")

    labels_path.write_text(
        "source,start_frame,end_frame,label\nmy_frames,20,31,1\nmy_frames,52,61,1\n",
        encoding="utf-8",
    )

    print(f"Frames: {frame_dir}")
    print(f"Labels: {labels_path}")
    print("Run:")
    print(
        "python -m glitch_detection.run_baseline "
        "--input data\\raw\\my_frames "
        "--labels data\\raw\\my_labels.csv "
        "--name my_experiment "
        "--clip-length 16 "
        "--stride 8 "
        "--size 128"
    )


if __name__ == "__main__":
    main()
