from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare a canonical WOB root inside Kaggle.")
    parser.add_argument("--split-csv", required=True, type=Path)
    parser.add_argument("--normal-input-root", required=True, type=Path)
    parser.add_argument("--test-input-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--mode", choices=["symlink", "copy"], default="symlink")
    parser.add_argument("--no-locked", action="store_true")
    parser.add_argument(
        "--phase",
        choices=["p0_full_nonlocked", "p1_train_only"],
        required=True,
    )
    return parser


def load_rows(split_csv: Path) -> list[dict[str, str]]:
    with split_csv.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def selected_rows(
    rows: list[dict[str, str]], phase: str, *, no_locked: bool
) -> tuple[list[dict[str, str]], int]:
    locked_skipped = 0
    selected: list[dict[str, str]] = []
    for row in rows:
        if row["split"] == "test":
            locked_skipped += 1
            if no_locked:
                continue
        if phase == "p0_full_nonlocked":
            if row["split"] != "test":
                selected.append(row)
        elif phase == "p1_train_only":
            if row["label"] == "Normal" and row["split"] in {"train", "validation"}:
                selected.append(row)
    return sorted(selected, key=lambda row: row["source"]), locked_skipped


def build_flat_index(root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in root.rglob("*.tar"):
        index.setdefault(path.name, []).append(path)
    return index


def resolve_source(
    source: str,
    *,
    normal_input_root: Path,
    test_input_root: Path,
    normal_flat: dict[str, list[Path]],
    test_flat: dict[str, list[Path]],
) -> tuple[Path | None, str]:
    root = normal_input_root if source.startswith("NORMAL-TRAIN/") else test_input_root
    exact = root / Path(source)
    if exact.is_file():
        return exact, "exact"
    basename = Path(source).name
    index = normal_flat if source.startswith("NORMAL-TRAIN/") else test_flat
    matches = index.get(basename, [])
    if len(matches) == 1:
        return matches[0], "flattened_unique"
    if len(matches) > 1:
        raise ValueError(f"Ambiguous flattened basename for {source}: {basename}")
    return None, "missing"


def materialize_link(src: Path, dst: Path, mode: str) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    if mode == "copy":
        shutil.copy2(src, dst)
        return "copied"
    try:
        dst.symlink_to(src)
        return "symlinked"
    except OSError:
        os.link(src, dst)
        return "hardlinked_fallback"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_prepare(
    *,
    split_csv: Path,
    normal_input_root: Path,
    test_input_root: Path,
    output_root: Path,
    mode: str,
    phase: str,
    no_locked: bool,
) -> dict[str, Any]:
    rows = load_rows(split_csv)
    selected, locked_skipped = selected_rows(rows, phase, no_locked=no_locked)
    normal_flat = build_flat_index(normal_input_root)
    test_flat = build_flat_index(test_input_root)
    manifest_rows: list[dict[str, str]] = []
    missing_rows: list[str] = []

    for row in selected:
        resolved, resolution = resolve_source(
            row["source"],
            normal_input_root=normal_input_root,
            test_input_root=test_input_root,
            normal_flat=normal_flat,
            test_flat=test_flat,
        )
        if resolved is None:
            missing_rows.append(row["source"])
            continue
        target = output_root / Path(row["source"])
        link_action = materialize_link(resolved, target, mode)
        manifest_rows.append(
            {
                "source": row["source"],
                "dataset_id": row["dataset_id"],
                "split": row["split"],
                "label": row["label"],
                "category": row["category"],
                "resolved_relative": row["source"] if resolution == "exact" else resolved.name,
                "output_relative": row["source"],
                "resolution": resolution,
                "materialization": link_action,
            }
        )

    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / "wob_root_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(manifest_rows[0]) if manifest_rows else ["source"]
        )
        writer.writeheader()
        writer.writerows(manifest_rows)
    manifest_sha = sha256_file(manifest_path)
    (output_root / "wob_root_manifest.sha256").write_text(
        f"{manifest_sha}  {manifest_path.name}\n",
        encoding="utf-8",
    )
    metadata = {
        "phase": phase,
        "mode": mode,
        "selected_rows": len(selected),
        "resolved_rows": len(manifest_rows),
        "missing_rows": len(missing_rows),
        "missing_sources": missing_rows,
        "locked_rows_skipped": locked_skipped,
        "no_locked": no_locked,
        "manifest_sha256": manifest_sha,
    }
    (output_root / "wob_root_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> None:
    args = build_parser().parse_args()
    metadata = run_prepare(
        split_csv=args.split_csv,
        normal_input_root=args.normal_input_root,
        test_input_root=args.test_input_root,
        output_root=args.output_root,
        mode=args.mode,
        phase=args.phase,
        no_locked=args.no_locked,
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))
    if metadata["missing_rows"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
