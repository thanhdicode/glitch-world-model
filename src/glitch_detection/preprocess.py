from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image

from .manifest import ClipRecord, write_manifest

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def list_frame_files(input_path: Path) -> list[Path]:
    frames = [
        path
        for path in input_path.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(frames)


def resize_and_save_frame(source: Path, destination: Path, size: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.convert("RGB").resize((size, size), Image.Resampling.BILINEAR).save(destination)


def preprocess_frames(
    input_path: Path,
    output_dir: Path,
    clip_length: int,
    stride: int,
    size: int,
    fps: float,
) -> Path:
    frames = list_frame_files(input_path)
    if len(frames) < clip_length:
        raise ValueError(f"Need at least {clip_length} frames, found {len(frames)} in {input_path}")

    source_name = input_path.stem
    clips_dir = output_dir / "clips"
    records: list[ClipRecord] = []
    clip_index = 0

    for start in range(0, len(frames) - clip_length + 1, stride):
        selected = frames[start : start + clip_length]
        clip_id = f"{source_name}_{clip_index:06d}"
        clip_dir = clips_dir / clip_id
        if clip_dir.exists():
            shutil.rmtree(clip_dir)
        clip_dir.mkdir(parents=True, exist_ok=True)
        for frame_offset, frame_path in enumerate(selected):
            resize_and_save_frame(frame_path, clip_dir / f"{frame_offset:06d}.png", size)
        records.append(
            ClipRecord(
                clip_id=clip_id,
                source=source_name,
                clip_dir=str(clip_dir),
                start_frame=start,
                end_frame=start + clip_length - 1,
                frame_count=clip_length,
                fps=fps,
            )
        )
        clip_index += 1

    manifest_path = output_dir / "manifest.csv"
    write_manifest(manifest_path, records)
    return manifest_path


def extract_video_frames(
    video_path: Path, frames_dir: Path, size: int | None = None
) -> tuple[Path, float]:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("Video preprocessing requires opencv-python.") from exc

    frames_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if size is not None:
            frame = cv2.resize(frame, (size, size), interpolation=cv2.INTER_LINEAR)
        cv2.imwrite(str(frames_dir / f"frame_{index:06d}.png"), frame)
        index += 1
    capture.release()

    if index == 0:
        raise ValueError(f"No frames extracted from {video_path}")
    return frames_dir, float(fps)


def preprocess_input(
    input_path: Path,
    output_dir: Path,
    clip_length: int,
    stride: int,
    size: int,
    fps: float | None,
) -> Path:
    input_path = input_path.resolve()
    output_dir = output_dir.resolve()
    if input_path.is_dir():
        return preprocess_frames(
            input_path=input_path,
            output_dir=output_dir,
            clip_length=clip_length,
            stride=stride,
            size=size,
            fps=fps or 30.0,
        )
    if input_path.is_file() and input_path.suffix.lower() in VIDEO_EXTENSIONS:
        frames_dir = output_dir / "frames" / input_path.stem
        extracted_dir, video_fps = extract_video_frames(input_path, frames_dir)
        return preprocess_frames(
            input_path=extracted_dir,
            output_dir=output_dir,
            clip_length=clip_length,
            stride=stride,
            size=size,
            fps=fps or video_fps,
        )
    raise ValueError(f"Input must be a frame folder or video file: {input_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preprocess gameplay videos or frames into clips.")
    parser.add_argument(
        "--input", required=True, type=Path, help="Video file or folder of image frames."
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="Output directory for clips and manifest."
    )
    parser.add_argument("--clip-length", type=int, default=16, help="Number of frames per clip.")
    parser.add_argument("--stride", type=int, default=8, help="Frame stride between clips.")
    parser.add_argument("--size", type=int, default=128, help="Output frame size in pixels.")
    parser.add_argument(
        "--fps", type=float, default=None, help="Override FPS for frame-folder inputs."
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    manifest_path = preprocess_input(
        input_path=args.input,
        output_dir=args.output,
        clip_length=args.clip_length,
        stride=args.stride,
        size=args.size,
        fps=args.fps,
    )
    print(f"Wrote manifest: {manifest_path}")


if __name__ == "__main__":
    main()
