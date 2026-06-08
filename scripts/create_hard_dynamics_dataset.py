from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RNG = random.Random(7)


def draw_scene(index: int, player_x: int, player_y: int, glitch: bool) -> Image.Image:
    jitter_x = int(2 * math.sin(index / 5))
    image = Image.new("RGB", (180, 128), color=(20, 23, 32))
    draw = ImageDraw.Draw(image)

    for star in range(12):
        sx = (star * 31 + index * 2) % 180
        sy = 8 + (star * 17) % 40
        draw.point((sx, sy), fill=(80, 88, 110))

    ground_y = 100 + int(2 * math.sin(index / 9))
    draw.rectangle((0, ground_y, 180, 128), fill=(42, 58, 48))
    draw.rectangle((20 + jitter_x, 78, 76 + jitter_x, 88), fill=(95, 95, 104))
    draw.rectangle((106 + jitter_x, 70, 164 + jitter_x, 80), fill=(95, 95, 104))
    draw.rectangle((86 + jitter_x, 44, 94 + jitter_x, ground_y), fill=(130, 76, 76))
    draw.text((6, 6), f"hard t={index:03d}", fill=(170, 180, 200))

    if glitch:
        draw.rectangle(
            (84 + jitter_x, 40, 98 + jitter_x, ground_y + 2), outline=(255, 60, 60), width=2
        )
        draw.text((100, 8), "SHORT TELEPORT", fill=(255, 150, 150))

    px = player_x + jitter_x
    draw.ellipse((px, player_y, px + 11, player_y + 11), fill=(70, 170, 255))
    draw.rectangle((px + 3, player_y + 11, px + 8, player_y + 25), fill=(70, 170, 255))
    return image


def main() -> None:
    frame_dir = ROOT / "data" / "raw" / "hard_dynamics_frames"
    labels_path = ROOT / "data" / "raw" / "hard_dynamics_labels.csv"
    frame_dir.mkdir(parents=True, exist_ok=True)
    labels_path.parent.mkdir(parents=True, exist_ok=True)

    x = 14
    velocity = 2
    glitch_ranges = [(44, 47), (92, 95)]
    for index in range(128):
        if index % 23 == 0 and index > 0:
            velocity = RNG.choice([-3, -2, 2, 3])

        glitch = any(start <= index <= end for start, end in glitch_ranges)
        if glitch:
            x = 138 if index % 2 == 0 else 24
        else:
            x += velocity
            if x < 12 or x > 152:
                velocity *= -1
                x += velocity

        y = 72 + int(4 * math.sin(index / 6))
        if index % 31 in {0, 1, 2, 3, 4}:
            y -= 12
        draw_scene(index, x, y, glitch).save(frame_dir / f"frame_{index:06d}.png")

    labels_path.write_text(
        "source,start_frame,end_frame,label\n"
        "hard_dynamics_frames,44,47,1\n"
        "hard_dynamics_frames,92,95,1\n",
        encoding="utf-8",
    )

    print(f"Frames: {frame_dir}")
    print(f"Labels: {labels_path}")


if __name__ == "__main__":
    main()
