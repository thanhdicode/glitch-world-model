from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPLIT_PATH = ROOT / "outputs" / "gate3" / "world_of_bugs" / "split.csv"
DEFAULT_PROTOCOL_AUDIT_PATH = ROOT / "outputs" / "gate3" / "world_of_bugs" / "protocol_audit.json"
DEFAULT_SPLIT_AUDIT_PATH = ROOT / "outputs" / "gate3" / "world_of_bugs" / "split.audit.json"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "wob_p0_materialization_audit"
CONVERTER_SCRIPTS = [
    ROOT / "scripts" / "freeze_wob_protocol.py",
    ROOT / "scripts" / "build_wob_lewm_lance.py",
]
LANCE_OUTPUT_PATTERNS = [
    ROOT / "outputs" / "gate4" / "wob*.lance",
    ROOT / "outputs" / "gate5" / "packages" / "wob" / "*.lance",
]
MANIFEST_FIELDS = [
    "dataset_id",
    "source",
    "episode_id",
    "pair_id",
    "category",
    "label",
    "split",
    "action_mode",
    "use_for_training",
    "materialize",
    "source_exists",
]
ACTION_CAVEAT = "semantic_action_synchronization_verified=false"


@dataclass(frozen=True)
class WobP0Config:
    wob_root: Path | None
    output_dir: Path
    split_path: Path
    protocol_audit_path: Path
    split_audit_path: Path
    dry_run: bool
    allow_materialization_check: bool
    no_locked: bool
    write_manifest_preview: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit WOB materialization readiness without training."
    )
    parser.add_argument("--wob-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--split-path", type=Path, default=DEFAULT_SPLIT_PATH)
    parser.add_argument("--protocol-audit-path", type=Path, default=DEFAULT_PROTOCOL_AUDIT_PATH)
    parser.add_argument("--split-audit-path", type=Path, default=DEFAULT_SPLIT_AUDIT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-materialization-check", action="store_true")
    parser.add_argument("--no-locked", action="store_true")
    parser.add_argument("--write-manifest-preview", action="store_true")
    return parser


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def detect_converter_scripts() -> list[str]:
    return [str(path) for path in CONVERTER_SCRIPTS if path.is_file()]


def detect_lance_outputs() -> list[str]:
    outputs: list[str] = []
    for pattern in LANCE_OUTPUT_PATTERNS:
        outputs.extend(str(path) for path in sorted(pattern.parent.glob(pattern.name)))
    return outputs


def resolve_source_path(source: str, wob_root: Path | None) -> Path | None:
    if wob_root is None:
        return None
    return (wob_root / Path(source)).resolve()


def source_exists(source: str, wob_root: Path | None) -> bool:
    path = resolve_source_path(source, wob_root)
    return path.is_file() if path is not None else False


def assert_safe_wob_root(wob_root: Path | None) -> None:
    if wob_root is None:
        return
    parts = {part.upper() for part in wob_root.parts}
    if "TEST" in parts:
        raise ValueError(
            "Refusing locked-test path as --wob-root. Point --wob-root above TEST or use non-locked data."
        )


def build_manifest_rows(rows: list[dict[str, str]], wob_root: Path | None) -> list[dict[str, str]]:
    manifest_rows: list[dict[str, str]] = []
    for row in rows:
        if row["split"] == "test":
            continue
        manifest_rows.append(
            {
                "dataset_id": row["dataset_id"],
                "source": row["source"],
                "episode_id": row["episode_id"],
                "pair_id": row["pair_id"],
                "category": row["category"],
                "label": row["label"],
                "split": row["split"],
                "action_mode": row["action_mode"],
                "use_for_training": row["use_for_training"],
                "materialize": row["materialize"],
                "source_exists": str(source_exists(row["source"], wob_root)).lower(),
            }
        )
    return manifest_rows


def write_manifest_preview(
    output_dir: Path,
    rows: list[dict[str, str]],
) -> tuple[Path, Path, Path]:
    manifest_path = output_dir / "wob_manifest_preview.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    manifest_sha = sha256_file(manifest_path)
    sha_path = output_dir / "wob_manifest_preview.sha256"
    sha_path.write_text(f"{manifest_sha}  {manifest_path.name}\n", encoding="utf-8")
    metadata_path = output_dir / "wob_manifest_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "manifest_path": str(manifest_path),
                "manifest_sha256": manifest_sha,
                "row_count": len(rows),
                "locked_rows_excluded": True,
                "metadata_only_preview": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path, sha_path, metadata_path


def build_missing_inputs(rows: list[dict[str, str]], wob_root: Path | None) -> list[str]:
    if wob_root is None:
        return ["Missing --wob-root for source existence checks against split metadata."]
    missing: list[str] = []
    for row in rows:
        if row["split"] == "test":
            continue
        if not source_exists(row["source"], wob_root):
            missing.append(str(resolve_source_path(row["source"], wob_root)))
    return sorted(missing)


def materialization_status(rows: list[dict[str, str]], wob_root: Path | None) -> dict[str, int]:
    non_locked = [row for row in rows if row["split"] != "test"]
    existing = sum(1 for row in non_locked if source_exists(row["source"], wob_root))
    return {
        "non_locked_expected_count": len(non_locked),
        "non_locked_existing_count": existing,
        "non_locked_missing_count": len(non_locked) - existing,
    }


def determine_status(
    *,
    rows: list[dict[str, str]],
    wob_root: Path | None,
    converter_scripts: list[str],
) -> str:
    if not converter_scripts:
        return "BLOCKED_IMPLEMENTATION_GAP"
    status = materialization_status(rows, wob_root)
    if wob_root is None or status["non_locked_missing_count"] > 0:
        return "BLOCKED_MISSING_INPUTS"
    return "READY_FOR_WOB_P1"


def build_human_instructions(wob_root: Path | None, missing_inputs: list[str]) -> list[str]:
    if wob_root is None:
        return [
            "Provide --wob-root pointing at the local World of Bugs attachment root that contains NORMAL-TRAIN and TEST.",
            "Re-run the WOB-P0 audit with --allow-materialization-check --no-locked --write-manifest-preview.",
        ]
    if not missing_inputs:
        return [
            "Non-locked WOB sources are present under the provided root.",
            "WOB-P1 can proceed only after standard preflight and explicit human authorization.",
        ]
    preview = missing_inputs[:5]
    lines = [
        "Populate the non-locked WOB tar tree under the provided --wob-root so split.csv sources resolve directly.",
        "Required root layout must include NORMAL-TRAIN/<episode>/ep-XXXX.tar and TEST/<category>/<episode>/ep-XXXX.tar.",
        "Re-run the WOB-P0 audit after syncing the missing non-locked tar files.",
    ]
    lines.extend(f"Missing example: {item}" for item in preview)
    if len(missing_inputs) > len(preview):
        lines.append(
            f"... plus {len(missing_inputs) - len(preview)} more missing non-locked tar paths."
        )
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    materialization = report["materialization_status"]
    lines = [
        "# WOB-P0 Materialization Audit",
        "",
        f"- Status: `{report['status']}`",
        f"- Split metadata: `{report['split_path']}`",
        f"- Protocol audit: `{report['protocol_audit_path']}`",
        f"- WOB root: `{report['wob_root']}`",
        f"- Dry run: `{str(report['dry_run']).lower()}`",
        f"- Converter scripts detected: `{len(report['converter_scripts'])}`",
        f"- Existing Lance outputs detected: `{len(report['lance_outputs'])}`",
        f"- Non-locked expected rows: `{materialization['non_locked_expected_count']}`",
        f"- Non-locked existing rows: `{materialization['non_locked_existing_count']}`",
        f"- Non-locked missing rows: `{materialization['non_locked_missing_count']}`",
        f"- Action caveat: `{report['action_caveat']}`",
        f"- Locked test materialized: `{str(report['locked_test_materialized']).lower()}`",
        f"- Locked test scored: `{str(report['locked_test_scored']).lower()}`",
        "",
        "## Human Instructions",
        "",
    ]
    lines.extend(f"- {item}" for item in report["human_instructions"])
    return "\n".join(lines) + "\n"


def run_audit(config: WobP0Config) -> dict[str, Any]:
    assert_safe_wob_root(config.wob_root)
    rows = load_csv_rows(config.split_path)
    protocol_audit = load_json(config.protocol_audit_path)
    split_audit = load_json(config.split_audit_path)
    converter_scripts = detect_converter_scripts()
    lance_outputs = detect_lance_outputs()
    manifest_preview_paths: dict[str, str] | None = None
    manifest_sha256: str | None = None
    missing_inputs = build_missing_inputs(rows, config.wob_root)

    if config.allow_materialization_check and not config.no_locked:
        raise ValueError(
            "Materialization check requires --no-locked to keep the locked split closed."
        )

    report = {
        "status": determine_status(
            rows=rows, wob_root=config.wob_root, converter_scripts=converter_scripts
        ),
        "dry_run": config.dry_run,
        "wob_root": str(config.wob_root) if config.wob_root else None,
        "split_path": str(config.split_path),
        "protocol_audit_path": str(config.protocol_audit_path),
        "split_audit_path": str(config.split_audit_path),
        "split_counts": split_audit.get("split_counts", {}),
        "documented_protocol_counts": {
            "normal_inventory_count": protocol_audit.get("normal_inventory", {}).get(
                "normal_episode_count"
            ),
            "bug_inventory_count": protocol_audit.get("test_inventory", {}).get(
                "bug_episode_count"
            ),
        },
        "materialization_status": materialization_status(rows, config.wob_root),
        "converter_scripts": converter_scripts,
        "lance_outputs": lance_outputs,
        "action_metadata_present": bool(
            protocol_audit.get("normal_sample") and protocol_audit.get("bug_sample")
        ),
        "action_caveat": ACTION_CAVEAT,
        "semantic_action_synchronization_verified": False,
        "locked_test_materialized": bool(split_audit.get("locked_test_materialized", False)),
        "locked_test_scored": bool(split_audit.get("locked_test_scored", False)),
        "missing_inputs": missing_inputs,
        "human_instructions": build_human_instructions(config.wob_root, missing_inputs),
        "performance_metrics_present": False,
        "execution_claim_present": False,
    }

    config.output_dir.mkdir(parents=True, exist_ok=True)
    if config.write_manifest_preview:
        manifest_rows = build_manifest_rows(rows, config.wob_root)
        manifest_path, sha_path, metadata_path = write_manifest_preview(
            config.output_dir, manifest_rows
        )
        manifest_preview_paths = {
            "manifest_path": str(manifest_path),
            "sha256_path": str(sha_path),
            "metadata_path": str(metadata_path),
        }
        manifest_sha256 = sha256_file(manifest_path)
    report["manifest_preview"] = manifest_preview_paths
    report["manifest_sha256"] = manifest_sha256

    json_path = config.output_dir / "wob_p0_audit.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = config.output_dir / "wob_p0_audit.md"
    md_path.write_text(render_markdown(report), encoding="utf-8")
    report["json_path"] = str(json_path)
    report["markdown_path"] = str(md_path)
    return report
