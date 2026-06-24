from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

from PIL import Image

from glitch_detection.glitchbench_protocol import (
    GlitchBenchRecord,
    map_glitchbench_label,
    write_glitchbench_manifest,
    write_protocol_summary,
)
from glitch_detection.manifest import ClipRecord, write_manifest

ROOT = Path(__file__).resolve().parents[1]
ROWS_URL = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=glitchbench%2FGlitchBench&config=default&split=validation"
    "&offset={offset}&length={length}"
)
DEFAULT_OUTPUT_ROOT = ROOT / "data" / "raw" / "glitchbench_subset"
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


def _write_repeated_clip_frames(
    *, image_path: Path, destination: Path, frames_per_sample: int, size: int
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for frame_index in range(frames_per_sample):
        save_resized(image_path, destination / f"frame_{frame_index:06d}.png", size)


def _source_name(prefix: str, sample_index: int, record_id: str) -> str:
    compact = record_id.replace("/", "_").replace(" ", "_")
    return f"glitchbench_{sample_index:04d}_{prefix}_{compact}"


def _clip_record(source: str, clips_root: Path, frames_per_sample: int) -> ClipRecord:
    clip_id = f"{source}_clip"
    clip_dir = clips_root / source / "clips" / clip_id
    return ClipRecord(
        clip_id=clip_id,
        source=source,
        clip_dir=str(clip_dir),
        start_frame=0,
        end_frame=frames_per_sample - 1,
        frame_count=frames_per_sample,
        fps=1.0,
    )


def build_glitchbench_subset(
    *,
    limit: int,
    offset: int,
    size: int,
    frames_per_sample: int,
    output_root: Path,
    normal_image: Path,
) -> dict[str, object]:
    if not normal_image.is_file():
        raise FileNotFoundError(f"Missing normal reference image: {normal_image}")
    rows = fetch_rows(limit, offset)
    output_root.mkdir(parents=True, exist_ok=True)
    image_dir = output_root / "downloaded_images"
    clips_root = output_root / "clips_root"
    structured_manifest_path = output_root / "glitchbench_records.csv"
    clip_manifest_path = output_root / "manifest.csv"
    audit_path = output_root / "glitchbench_download_audit.json"

    protocol_records: list[GlitchBenchRecord] = []
    clip_records: list[ClipRecord] = []
    for sample_index, item in enumerate(rows):
        row = item["row"]
        image_url = row["image"]["src"]
        record_id = str(row.get("id", f"row-{item['row_idx']}")).strip()
        reddit_id = str(row.get("reddit", "")).strip() or record_id
        game = str(row.get("game", "")).strip()
        glitch_type = str(row.get("glitch-type", "")).strip()
        source_domain = str(row.get("source", "")).strip()
        description = "glitch"
        downloaded_image_path = image_dir / f"{sample_index:04d}_{record_id}.jpg"
        download_image(image_url, downloaded_image_path)

        synthetic_source = _source_name("normal", sample_index, record_id)
        buggy_source = _source_name("buggy", sample_index, record_id)
        synthetic_clip = _clip_record(synthetic_source, clips_root, frames_per_sample)
        buggy_clip = _clip_record(buggy_source, clips_root, frames_per_sample)
        _write_repeated_clip_frames(
            image_path=normal_image,
            destination=Path(synthetic_clip.clip_dir),
            frames_per_sample=frames_per_sample,
            size=size,
        )
        _write_repeated_clip_frames(
            image_path=downloaded_image_path,
            destination=Path(buggy_clip.clip_dir),
            frames_per_sample=frames_per_sample,
            size=size,
        )
        clip_records.extend([synthetic_clip, buggy_clip])
        protocol_records.extend(
            [
                GlitchBenchRecord(
                    source=synthetic_source,
                    clip_id=synthetic_clip.clip_id,
                    clip_dir=synthetic_clip.clip_dir,
                    image_path=str(normal_image),
                    record_id=record_id,
                    reddit_id=reddit_id,
                    game=game,
                    glitch_type=glitch_type,
                    source_domain=source_domain,
                    raw_label="synthetic_normal",
                    mapped_label=map_glitchbench_label("synthetic_normal", synthetic_normal=True),
                    group_key=reddit_id,
                    synthetic_normal=True,
                    temporal_label_available=False,
                ),
                GlitchBenchRecord(
                    source=buggy_source,
                    clip_id=buggy_clip.clip_id,
                    clip_dir=buggy_clip.clip_dir,
                    image_path=str(downloaded_image_path),
                    record_id=record_id,
                    reddit_id=reddit_id,
                    game=game,
                    glitch_type=glitch_type,
                    source_domain=source_domain,
                    raw_label=description,
                    mapped_label=map_glitchbench_label(description, synthetic_normal=False),
                    group_key=reddit_id,
                    synthetic_normal=False,
                    temporal_label_available=False,
                ),
            ]
        )

    write_glitchbench_manifest(structured_manifest_path, protocol_records)
    write_manifest(clip_manifest_path, clip_records)
    audit = {
        "status": "glitchbench_subset_download_complete",
        "dataset_source": "https://huggingface.co/datasets/glitchbench/GlitchBench",
        "rows_api": ROWS_URL.format(offset=offset, length=limit),
        "output_root": str(output_root),
        "record_count": len(protocol_records),
        "clip_record_count": len(clip_records),
        "group_count": len({record.group_key for record in protocol_records}),
        "frames_per_sample": frames_per_sample,
        "image_size": size,
        "temporal_label_available": False,
        "synthetic_normal_used": True,
        "claim_boundary": (
            "This ingestion materializes repeated-frame image clips and synthetic normal clips for "
            "a bounded GlitchBench image-level benchmark package. It does not create temporal "
            "ground-truth labels or natural normal gameplay evidence."
        ),
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    write_protocol_summary(audit_path, audit)
    return audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download and materialize a bounded GlitchBench subset package."
    )
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--size", type=int, default=128)
    parser.add_argument("--frames-per-sample", type=int, default=8)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--normal-image", type=Path, default=NORMAL_IMAGE)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    audit = build_glitchbench_subset(
        limit=args.limit,
        offset=args.offset,
        size=args.size,
        frames_per_sample=args.frames_per_sample,
        output_root=args.output_root,
        normal_image=args.normal_image,
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
