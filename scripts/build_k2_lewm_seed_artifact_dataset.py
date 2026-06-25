from __future__ import annotations

import argparse
import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any

from glitch_detection.gate6_data import sha256_file

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "lewm-k2-lewm-seed-artifacts"
SEEDS = (42, 43, 44)
REQUIRED_FILES = ("best_weights.pt", "config.json")
OPTIONAL_FILES = (
    "training_metadata.json",
    "training_metadata.json.sha256",
    "config.json.sha256",
    "best_weights.pt.sha256",
    "best_checkpoint_metadata.json",
    "best_checkpoint_metadata.json.sha256",
)


def _default_seed_source(seed: int) -> Path | None:
    candidates = [
        ROOT
        / "outputs"
        / "r5_wob_identical_episode_dryrun_check"
        / "_seed_artifacts"
        / f"seed{seed}"
        / "wob_outputs"
        / f"wob_seed{seed}",
        ROOT
        / "outputs"
        / "r5_wob_identical_episode_dryrun"
        / "_seed_artifacts"
        / f"seed{seed}"
        / "wob_outputs"
        / f"wob_seed{seed}",
    ]
    for candidate in candidates:
        if candidate.is_dir() and all((candidate / name).is_file() for name in REQUIRED_FILES):
            return candidate
    return None


def _resolve_seed_sources(
    seed42_root: Path | None,
    seed43_root: Path | None,
    seed44_root: Path | None,
) -> dict[int, Path]:
    explicit = {42: seed42_root, 43: seed43_root, 44: seed44_root}
    resolved: dict[int, Path] = {}
    for seed in SEEDS:
        source_root = explicit[seed] or _default_seed_source(seed)
        if source_root is None:
            raise FileNotFoundError(
                f"Could not resolve a local source root for seed{seed}. "
                "Pass --seed42-root/--seed43-root/--seed44-root explicitly."
            )
        missing = [name for name in REQUIRED_FILES if not (source_root / name).is_file()]
        if missing:
            raise FileNotFoundError(
                f"Seed{seed} source root is incomplete for K2 packaging: {source_root} missing {missing}"
            )
        resolved[seed] = source_root
    return resolved


def _link_or_copy_file(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        if dst.exists():
            dst.unlink()
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def _write_readme(path: Path, audit: dict[str, Any]) -> Path:
    text = "\n".join(
        [
            "# K2 LeWM Seed Artifacts",
            "",
            "This package normalizes three LeWM seed artifact roots for Kaggle K2 scoring.",
            "",
            "Expected Kaggle layout:",
            "- /kaggle/input/lewm-k2-lewm-seed-artifacts/seed42/best_weights.pt",
            "- /kaggle/input/lewm-k2-lewm-seed-artifacts/seed42/config.json",
            "- /kaggle/input/lewm-k2-lewm-seed-artifacts/seed43/best_weights.pt",
            "- /kaggle/input/lewm-k2-lewm-seed-artifacts/seed43/config.json",
            "- /kaggle/input/lewm-k2-lewm-seed-artifacts/seed44/best_weights.pt",
            "- /kaggle/input/lewm-k2-lewm-seed-artifacts/seed44/config.json",
            "",
            "Optional sidecars are preserved when present, including `checkpoint.sha256`.",
            "",
            "Claim boundary:",
            "- this package is an input-only artifact bundle",
            "- it does not itself establish K2 performance claims",
            "- K2 remains bounded, image-level, and synthetic-normal on the GlitchBench side",
            "",
            "Resolved local source roots:",
            f"- seed42: {audit['seed_sources']['seed42']}",
            f"- seed43: {audit['seed_sources']['seed43']}",
            f"- seed44: {audit['seed_sources']['seed44']}",
            "",
        ]
    )
    path.write_text(text + "\n", encoding="utf-8")
    return path


def _zip_package(package_root: Path, zip_path: Path) -> Path:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        for file_path in sorted(package_root.rglob("*")):
            if file_path.is_file():
                archive.write(
                    file_path,
                    str(Path(package_root.name) / file_path.relative_to(package_root)).replace(
                        "\\", "/"
                    ),
                )
    return zip_path


def build_k2_lewm_seed_artifact_dataset(
    *,
    output_root: Path,
    package_name: str = PACKAGE_NAME,
    seed42_root: Path | None = None,
    seed43_root: Path | None = None,
    seed44_root: Path | None = None,
) -> dict[str, Any]:
    seed_sources = _resolve_seed_sources(seed42_root, seed43_root, seed44_root)
    package_root = output_root / package_name
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)
    action_counts: dict[str, int] = {"hardlink": 0, "copy": 0}
    seed_audit: list[dict[str, Any]] = []
    for seed, source_root in seed_sources.items():
        destination_root = package_root / f"seed{seed}"
        copied_files: list[str] = []
        for name in (*REQUIRED_FILES, *OPTIONAL_FILES):
            source_path = source_root / name
            if not source_path.is_file():
                continue
            action = _link_or_copy_file(source_path, destination_root / name)
            action_counts[action] += 1
            copied_files.append(name)
        checkpoint_path = destination_root / "best_weights.pt"
        config_path = destination_root / "config.json"
        checkpoint_sha256 = sha256_file(checkpoint_path)
        normalized_checkpoint_sidecar = destination_root / "checkpoint.sha256"
        normalized_checkpoint_sidecar.write_text(f"{checkpoint_sha256}\n", encoding="utf-8")
        copied_files.append("checkpoint.sha256")
        seed_receipt = {
            "seed": seed,
            "source_root": str(source_root),
            "copied_files": copied_files,
            "checkpoint_sha256": checkpoint_sha256,
            "config_sha256": sha256_file(config_path),
            "normalized_checkpoint_sha256_path": str(normalized_checkpoint_sidecar),
        }
        source_checkpoint_sidecar = source_root / "checkpoint.sha256"
        if source_checkpoint_sidecar.is_file():
            seed_receipt["source_checkpoint_sha256_sidecar"] = source_checkpoint_sidecar.read_text(
                encoding="utf-8-sig"
            ).strip()
        seed_audit.append(seed_receipt)
    audit = {
        "status": "k2_lewm_seed_artifacts_ready",
        "dataset_name": package_name,
        "package_root": str(package_root),
        "seed_sources": {f"seed{seed}": str(path) for seed, path in seed_sources.items()},
        "seeds": seed_audit,
        "file_action_counts": action_counts,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    _write_readme(package_root / "README_KAGGLE.md", audit)
    audit_path = package_root / "artifact_manifest.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    zip_path = output_root / f"{package_name}.zip"
    _zip_package(package_root, zip_path)
    sha_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    zip_sha256 = sha256_file(zip_path)
    sha_path.write_text(f"{zip_sha256}  {zip_path.name}\n", encoding="utf-8")
    audit["zip_path"] = str(zip_path)
    audit["zip_sha256"] = zip_sha256
    audit["zip_sha256_path"] = str(sha_path)
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a normalized Kaggle dataset of LeWM seed artifacts for K2 scoring."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "outputs" / "k2_lewm_seed_artifacts",
    )
    parser.add_argument("--package-name", default=PACKAGE_NAME)
    parser.add_argument("--seed42-root", type=Path, default=None)
    parser.add_argument("--seed43-root", type=Path, default=None)
    parser.add_argument("--seed44-root", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    audit = build_k2_lewm_seed_artifact_dataset(
        output_root=args.output_root,
        package_name=args.package_name,
        seed42_root=args.seed42_root,
        seed43_root=args.seed43_root,
        seed44_root=args.seed44_root,
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
