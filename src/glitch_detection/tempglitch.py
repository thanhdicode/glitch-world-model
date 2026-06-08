from __future__ import annotations

import csv
import json
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .manifest import ClipRecord, read_manifest, write_manifest

DATASET_ID = "asgaardlab/TempGlitch"
DATASET_PAGE_URL = "https://huggingface.co/datasets/asgaardlab/TempGlitch"
DATASET_API_URL = "https://huggingface.co/api/datasets/asgaardlab/TempGlitch"
ROWS_URL = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=asgaardlab%2FTempGlitch&config=default&split=train"
    "&offset={offset}&length={length}"
)
NORMAL_LABEL = "Normal"
BUGGY_LABEL = "Buggy"
DEFAULT_CATEGORIES = [
    "Blinking",
    "Frozen Animation",
    "Shooting Error",
    "Stuck in Place",
    "Velocity Bug",
]


@dataclass(frozen=True)
class TempGlitchVideoRef:
    dataset_revision: str
    category: str
    public_label_raw: str
    public_label: str
    file_name: str
    source_name: str


@dataclass(frozen=True)
class TempGlitchSample:
    row_idx: int
    category: str
    public_label_raw: str
    public_label: str
    is_glitch: bool
    source_name: str
    file_name: str
    video_url: str
    dataset_revision: str
    local_video_path: str


def normalize_tempglitch_label(label: str) -> str:
    normalized = label.strip()
    if normalized not in {BUGGY_LABEL, NORMAL_LABEL}:
        raise ValueError(f"Unexpected TempGlitch label: {label!r}")
    return normalized


def encode_tempglitch_video_url(video_url: str) -> str:
    parsed = urllib.parse.urlsplit(video_url)
    encoded_path = urllib.parse.quote(parsed.path, safe="/%")
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, encoded_path, parsed.query, parsed.fragment)
    )


def parse_tempglitch_video_url(video_url: str) -> TempGlitchVideoRef:
    decoded_path = urllib.parse.unquote(urllib.parse.urlparse(video_url).path)
    parts = [part for part in decoded_path.split("/") if part]
    try:
        resolve_index = parts.index("resolve")
    except ValueError as exc:
        raise ValueError(
            f"TempGlitch URL does not contain a revision segment: {video_url}"
        ) from exc

    if len(parts) <= resolve_index + 4:
        raise ValueError(f"TempGlitch URL is missing category/label/file segments: {video_url}")

    dataset_revision = parts[resolve_index + 1]
    category = parts[resolve_index + 2]
    public_label_raw = parts[resolve_index + 3]
    public_label = normalize_tempglitch_label(public_label_raw)
    file_name = parts[resolve_index + 4]
    return TempGlitchVideoRef(
        dataset_revision=dataset_revision,
        category=category,
        public_label_raw=public_label_raw,
        public_label=public_label,
        file_name=file_name,
        source_name=Path(file_name).stem,
    )


def _load_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def fetch_tempglitch_dataset_info() -> dict[str, Any]:
    return _load_json(DATASET_API_URL)


def fetch_tempglitch_rows(offset: int, length: int) -> dict[str, Any]:
    return _load_json(ROWS_URL.format(offset=offset, length=length))


def tempglitch_category_counts(dataset_info: dict[str, Any]) -> dict[tuple[str, str], int]:
    counts: Counter[tuple[str, str]] = Counter()
    for sibling in dataset_info.get("siblings", []):
        file_name = sibling.get("rfilename", "")
        if not file_name.endswith(".mp4"):
            continue
        parts = file_name.split("/")
        if len(parts) != 3:
            continue
        category, label, _ = parts
        counts[(category, normalize_tempglitch_label(label))] += 1
    return dict(counts)


def _relative_video_path(category: str, public_label: str, file_name: str) -> Path:
    return Path("videos") / category / public_label / file_name


def _write_tempglitch_source_readme(
    output_dir: Path,
    dataset_info: dict[str, Any],
    selected_categories: list[str],
    limit_per_group: int,
) -> Path:
    counts = tempglitch_category_counts(dataset_info)
    readme_path = output_dir / "README_SOURCE.txt"
    lines = [
        f"Dataset: {DATASET_ID}",
        f"Dataset page: {DATASET_PAGE_URL}",
        f"Access date: {date.today().isoformat()}",
        f"License: {dataset_info.get('cardData', {}).get('license', 'unknown')}",
        f"Total public downloads: {dataset_info.get('downloads', 'unknown')}",
        f"Selected categories: {', '.join(selected_categories)}",
        f"Limit per category/label group: {limit_per_group}",
        "",
        "Verified public category counts:",
    ]
    for category in selected_categories:
        for public_label in [BUGGY_LABEL, NORMAL_LABEL]:
            lines.append(
                f"- {category} / {public_label}: {counts.get((category, public_label), 0)}"
            )
    readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return readme_path


def _write_metadata_csv(output_dir: Path, samples: list[TempGlitchSample]) -> Path:
    metadata_path = output_dir / "metadata.csv"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "row_idx",
                "category",
                "public_label_raw",
                "public_label",
                "is_glitch",
                "source",
                "file_name",
                "dataset_revision",
                "video_url",
                "local_video_path",
            ],
        )
        writer.writeheader()
        for sample in samples:
            writer.writerow(
                {
                    "row_idx": sample.row_idx,
                    "category": sample.category,
                    "public_label_raw": sample.public_label_raw,
                    "public_label": sample.public_label,
                    "is_glitch": int(sample.is_glitch),
                    "source": sample.source_name,
                    "file_name": sample.file_name,
                    "dataset_revision": sample.dataset_revision,
                    "video_url": sample.video_url,
                    "local_video_path": sample.local_video_path,
                }
            )
    return metadata_path


def download_tempglitch_subset(
    output_dir: Path,
    categories: list[str] | None = None,
    limit_per_group: int = 1,
    page_size: int = 100,
) -> tuple[list[TempGlitchSample], Path, Path]:
    selected_categories = categories or list(DEFAULT_CATEGORIES)
    category_set = set(selected_categories)
    dataset_info = fetch_tempglitch_dataset_info()

    required_counts = {
        (category, public_label): limit_per_group
        for category in selected_categories
        for public_label in [BUGGY_LABEL, NORMAL_LABEL]
    }
    downloaded_counts: Counter[tuple[str, str]] = Counter()
    samples: list[TempGlitchSample] = []

    offset = 0
    while True:
        page = fetch_tempglitch_rows(offset=offset, length=page_size)
        rows = page.get("rows", [])
        features = page.get("features", [])
        if not rows:
            break

        label_names = features[1]["type"]["names"] if len(features) > 1 else None
        for item in rows:
            row = item["row"]
            video_url = row["video"]["src"]
            row_idx = int(item["row_idx"])
            parsed = parse_tempglitch_video_url(video_url)
            if parsed.category not in category_set:
                continue

            public_label_raw = (
                label_names[row["label"]] if label_names is not None else parsed.public_label_raw
            )
            public_label = normalize_tempglitch_label(public_label_raw)
            key = (parsed.category, public_label)
            if downloaded_counts[key] >= required_counts[key]:
                continue

            relative_video_path = _relative_video_path(
                category=parsed.category,
                public_label=public_label,
                file_name=parsed.file_name,
            )
            local_video_path = output_dir / relative_video_path
            local_video_path.parent.mkdir(parents=True, exist_ok=True)
            if not local_video_path.exists():
                urllib.request.urlretrieve(encode_tempglitch_video_url(video_url), local_video_path)

            samples.append(
                TempGlitchSample(
                    row_idx=row_idx,
                    category=parsed.category,
                    public_label_raw=public_label_raw,
                    public_label=public_label,
                    is_glitch=public_label == BUGGY_LABEL,
                    source_name=parsed.source_name,
                    file_name=parsed.file_name,
                    video_url=video_url,
                    dataset_revision=parsed.dataset_revision,
                    local_video_path=str(relative_video_path).replace("\\", "/"),
                )
            )
            downloaded_counts[key] += 1

            if all(downloaded_counts[key] >= required for key, required in required_counts.items()):
                metadata_path = _write_metadata_csv(output_dir, samples)
                readme_path = _write_tempglitch_source_readme(
                    output_dir=output_dir,
                    dataset_info=dataset_info,
                    selected_categories=selected_categories,
                    limit_per_group=limit_per_group,
                )
                return samples, metadata_path, readme_path
        offset += len(rows)

    missing = {
        f"{category}/{public_label}": required_counts[(category, public_label)]
        - downloaded_counts[(category, public_label)]
        for category, public_label in required_counts
        if downloaded_counts[(category, public_label)] < required_counts[(category, public_label)]
    }
    raise RuntimeError(f"Could not satisfy TempGlitch subset request: {missing}")


def read_tempglitch_metadata(metadata_path: Path) -> list[dict[str, str]]:
    with metadata_path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def combine_manifests(manifest_paths: list[Path], output_path: Path) -> Path:
    records: list[ClipRecord] = []
    for manifest_path in manifest_paths:
        records.extend(read_manifest(manifest_path))
    write_manifest(output_path, records)
    return output_path


def write_tempglitch_full_video_labels(
    metadata_path: Path,
    manifest_path: Path,
    output_path: Path,
) -> Path:
    bounds_by_source: dict[str, tuple[int, int]] = {}
    for record in read_manifest(manifest_path):
        start_frame, end_frame = bounds_by_source.get(
            record.source,
            (record.start_frame, record.end_frame),
        )
        bounds_by_source[record.source] = (
            min(start_frame, record.start_frame),
            max(end_frame, record.end_frame),
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "start_frame", "end_frame", "label"])
        writer.writeheader()
        for row in read_tempglitch_metadata(metadata_path):
            source = row["source"]
            if int(row["is_glitch"]) != 1:
                continue
            if source not in bounds_by_source:
                raise ValueError(f"Missing manifest records for TempGlitch source {source!r}")
            start_frame, end_frame = bounds_by_source[source]
            writer.writerow(
                {
                    "source": source,
                    "start_frame": start_frame,
                    "end_frame": end_frame,
                    "label": 1,
                }
            )
    return output_path
