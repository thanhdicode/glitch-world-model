from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def draw_scene(index: int, player_x: int, glitch: bool) -> Image.Image:
    image = Image.new("RGB", (160, 120), color=(22, 24, 32))
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 94, 160, 120), fill=(45, 62, 50))
    draw.rectangle((28, 68, 132, 78), fill=(98, 98, 104))
    draw.rectangle((76, 30, 84, 94), fill=(145, 80, 80))
    draw.text((6, 6), f"t={index:02d}", fill=(180, 190, 210))

    player_y = 56
    if glitch:
        draw.rectangle((74, 26, 88, 98), outline=(255, 70, 70), width=2)
        draw.text((92, 8), "TELEPORT / WALL", fill=(255, 160, 160))

    draw.ellipse((player_x, player_y, player_x + 12, player_y + 12), fill=(80, 185, 255))
    draw.rectangle((player_x + 4, player_y + 12, player_x + 8, player_y + 26), fill=(80, 185, 255))
    return image


def main() -> None:
    frame_dir = ROOT / "data" / "raw" / "dynamics_frames"
    labels_path = ROOT / "data" / "raw" / "dynamics_labels.csv"
    frame_dir.mkdir(parents=True, exist_ok=True)
    labels_path.parent.mkdir(parents=True, exist_ok=True)

    x = 12
    velocity = 2
    for index in range(96):
        glitch = 36 <= index <= 43 or 68 <= index <= 75
        if index == 36:
            x = 118
        elif index == 68:
            x = 4
        elif not glitch:
            x += velocity
            if x > 132 or x < 8:
                velocity *= -1
                x += velocity
        else:
            x = 118 if index % 2 == 0 else 12

        draw_scene(index, x, glitch).save(frame_dir / f"frame_{index:06d}.png")

    labels_path.write_text(
        "source,start_frame,end_frame,label\ndynamics_frames,36,43,1\ndynamics_frames,68,75,1\n",
        encoding="utf-8",
    )

    print(f"Frames: {frame_dir}")
    print(f"Labels: {labels_path}")
    print("Run:")
    print(
        "python -m glitch_detection.run_baseline "
        "--input data\\raw\\dynamics_frames "
        "--labels data\\raw\\dynamics_labels.csv "
        "--name dynamics_mini_latent "
        "--clip-length 16 "
        "--stride 8 "
        "--size 128 "
        "--scorer mini_latent"
    )


if __name__ == "__main__":
    main()
