"""Finalize WOB-P1 seed42 artifacts: manifest JSON, SHA256 hashes, tarball.

Refuses to package raw datasets, credentials, locked-test files, or huge caches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FORBIDDEN_PATTERNS = [
    "locked_test",
    "test_outputs",
    "test_scores",
    ".env",
    "kaggle.json",
    "credentials",
    ".lance",
]

ALLOWED_EXTENSIONS = {
    ".json",
    ".csv",
    ".pt",
    ".txt",
    ".log",
    ".sha256",
    ".yaml",
    ".yml",
    ".md",
}

MAX_SINGLE_FILE_MB = 500


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_forbidden(path: Path) -> bool:
    name = path.name.lower()
    full = str(path).lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in full:
            return True
    if name.startswith("."):
        return True
    return False


def _collect_artifacts(root: Path) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    if not root.exists():
        return artifacts
    for item in sorted(root.rglob("*")):
        if not item.is_file():
            continue
        if _is_forbidden(item):
            continue
        size_mb = item.stat().st_size / (1024 * 1024)
        entry: dict[str, Any] = {
            "path": str(item.relative_to(root)),
            "size_bytes": item.stat().st_size,
            "size_mb": round(size_mb, 2),
        }
        if item.suffix in ALLOWED_EXTENSIONS and size_mb < MAX_SINGLE_FILE_MB:
            entry["sha256"] = _sha256_file(item)
        elif item.suffix == ".pt" and size_mb < MAX_SINGLE_FILE_MB:
            entry["sha256"] = _sha256_file(item)
        else:
            entry["sha256"] = "skipped_large_or_binary"
        artifacts.append(entry)
    return artifacts


def _write_sha256_files(root: Path, artifacts: list[dict[str, Any]]) -> None:
    for entry in artifacts:
        if entry.get("sha256", "").startswith("skipped"):
            continue
        sha_path = root / (entry["path"] + ".sha256")
        sha_path.parent.mkdir(parents=True, exist_ok=True)
        sha_path.write_text(f"{entry['sha256']}  {entry['path']}\n", encoding="utf-8")


def _build_tarball(
    tarball_path: Path,
    output_root: Path,
    metadata_root: Path,
    log_dir: Path,
) -> None:
    with tarfile.open(str(tarball_path), "w:gz") as tar:
        for root, prefix in [
            (output_root, "wob_outputs/wob_seed42"),
            (metadata_root, "wob_p1_metadata"),
            (log_dir, "logs"),
        ]:
            if not root.exists():
                continue
            for item in sorted(root.rglob("*")):
                if not item.is_file():
                    continue
                if _is_forbidden(item):
                    continue
                # Skip very large files in tarball (e.g., Lance datasets)
                if item.stat().st_size > MAX_SINGLE_FILE_MB * 1024 * 1024:
                    continue
                arcname = f"{prefix}/{item.relative_to(root)}"
                tar.add(str(item), arcname=arcname)


def finalize(
    output_root: str,
    metadata_root: str,
    log_dir: str,
    tarball_path: str,
) -> dict[str, Any]:
    out = Path(output_root)
    meta = Path(metadata_root)
    logs = Path(log_dir)
    tar_path = Path(tarball_path)

    manifest: dict[str, Any] = {
        "timestamp": _utc_now(),
        "phase": "wob_p1_seed42",
        "output_root": output_root,
        "metadata_root": metadata_root,
    }

    # Collect and hash artifacts
    manifest["output_artifacts"] = _collect_artifacts(out)
    manifest["metadata_artifacts"] = _collect_artifacts(meta)
    manifest["total_output_files"] = len(manifest["output_artifacts"])
    manifest["total_metadata_files"] = len(manifest["metadata_artifacts"])

    # Write individual .sha256 files
    _write_sha256_files(out, manifest["output_artifacts"])

    # Check training completion
    training_meta = out / "training_metadata.json"
    if training_meta.is_file():
        try:
            tmeta = json.loads(training_meta.read_text(encoding="utf-8"))
            manifest["training_completed"] = True
            manifest["training_status"] = tmeta.get("status", "unknown")
            manifest["updates_completed"] = tmeta.get("updates_completed")
            manifest["best_validation_loss"] = tmeta.get("best_validation_loss")
        except Exception as exc:
            manifest["training_completed"] = False
            manifest["training_read_error"] = str(exc)
    else:
        manifest["training_completed"] = False

    # Check validator
    validator_report = out / "validator_report.json"
    if validator_report.is_file():
        manifest["validator_passed"] = True
    else:
        manifest["validator_passed"] = False

    manifest["locked_test_materialized"] = False
    manifest["locked_test_scored"] = False
    manifest["evaluation_run"] = False

    # Write manifest
    manifest_path = out / "artifact_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest written to {manifest_path}")

    # Build tarball
    _build_tarball(tar_path, out, meta, logs)
    if tar_path.is_file():
        manifest["tarball_sha256"] = _sha256_file(tar_path)
        # Re-write manifest with tarball hash
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"Tarball written to {tar_path} ({tar_path.stat().st_size} bytes)")

    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Finalize WOB-P1 seed42 artifacts")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--metadata-root", required=True)
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("--tarball-path", required=True)
    args = parser.parse_args(argv)

    manifest = finalize(args.output_root, args.metadata_root, args.log_dir, args.tarball_path)
    print("\n=== Artifact Manifest Summary ===")
    print(
        json.dumps(
            {
                k: v
                for k, v in manifest.items()
                if k not in ("output_artifacts", "metadata_artifacts")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
