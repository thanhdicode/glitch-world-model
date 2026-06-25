from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_sidecar(path: Path) -> str:
    tokens = path.read_text(encoding="utf-8-sig").strip().split()
    if not tokens:
        raise ValueError(f"Invalid SHA256 sidecar: {path}")
    return tokens[0].lower()


def _verify_optional_sidecar(bundle: Path) -> dict[str, Any] | None:
    for candidate in (
        Path(f"{bundle}.sha256"),
        bundle.with_suffix(bundle.suffix + ".sha256"),
        bundle.parent / f"{bundle.name}.sha256",
    ):
        if not candidate.is_file():
            continue
        expected = _parse_sidecar(candidate)
        actual = _sha256(bundle)
        if expected != actual:
            raise ValueError(
                f"K3 bundle SHA256 mismatch for {bundle}: expected {expected}, found {actual}"
            )
        return {
            "bundle_path": str(bundle),
            "sidecar_path": str(candidate),
            "sha256": actual,
            "sha256_verified": True,
        }
    return None


def _safe_extract_tar(tarball: Path, destination: Path) -> Path:
    root = destination.resolve()
    root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tarball, "r:*") as archive:
        for member in archive.getmembers():
            resolved = (root / member.name).resolve()
            if not resolved.is_relative_to(root):
                raise ValueError(f"Path traversal detected in K3 tarball: {member.name}")
            if member.issym() or member.islnk():
                raise ValueError(f"Archive links are not allowed in K3 bundle: {member.name}")
            if not (member.isdir() or member.isreg()):
                raise ValueError(f"Unsupported K3 tarball member: {member.name}")
        archive.extractall(root)
    return root


def _safe_extract_zip(bundle: Path, destination: Path) -> Path:
    root = destination.resolve()
    root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle) as archive:
        for member in archive.infolist():
            resolved = (root / member.filename).resolve()
            if not resolved.is_relative_to(root):
                raise ValueError(f"Path traversal detected in K3 zip bundle: {member.filename}")
        archive.extractall(root)
    return root


def _resolve_bundle_root(bundle: Path) -> tuple[Path, dict[str, Any] | None]:
    if bundle.is_dir():
        return bundle.resolve(), None
    if not bundle.is_file():
        raise FileNotFoundError(f"Missing K3 bundle: {bundle}")
    sidecar = _verify_optional_sidecar(bundle)
    with tempfile.TemporaryDirectory(prefix="k3_ablation_intake_") as tmp:
        extract_root = Path(tmp) / "extract"
        if bundle.suffix == ".zip":
            root = _safe_extract_zip(bundle, extract_root)
        else:
            root = _safe_extract_tar(bundle, extract_root)
        materialized_root = Path(tempfile.mkdtemp(prefix="k3_ablation_intake_persist_"))
        if materialized_root.exists():
            for child in root.iterdir():
                target = materialized_root / child.name
                if child.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    for nested in child.rglob("*"):
                        destination = target / nested.relative_to(child)
                        if nested.is_dir():
                            destination.mkdir(parents=True, exist_ok=True)
                        else:
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            destination.write_bytes(nested.read_bytes())
                else:
                    target.write_bytes(child.read_bytes())
        return materialized_root, sidecar


def _variant_lookup(receipt: dict[str, Any]) -> dict[str, dict[str, Any]]:
    variants = receipt.get("executed_variants", [])
    if len(variants) != 12:
        raise ValueError(
            f"K3 bundle must contain exactly 12 executed variants, found {len(variants)}."
        )
    lookup = {row["variant_name"]: row for row in variants}
    if len(lookup) != 12:
        raise ValueError("K3 bundle contains duplicate variant names.")
    return lookup


def _assert_false_flags(payload: dict[str, Any], *, context: str) -> None:
    for field in ("locked_test_materialized", "locked_test_scored"):
        if payload.get(field) is not False:
            raise ValueError(f"Unsafe {context} flag: {field}")


def _validate_controlled_pairs(
    *,
    plan: dict[str, Any],
    pairs_payload: dict[str, Any],
    receipt: dict[str, Any],
) -> dict[str, Any]:
    variants = _variant_lookup(receipt)
    declared_pairs = pairs_payload.get("pairs", [])
    if len(declared_pairs) != 12:
        raise ValueError(
            f"K3 bundle must declare exactly 12 controlled pairs, found {len(declared_pairs)}."
        )
    if plan.get("variant_count") != 12:
        raise ValueError(f"K3 plan variant_count must be 12, found {plan.get('variant_count')}.")
    if plan.get("pair_count") != 12:
        raise ValueError(f"K3 plan pair_count must be 12, found {plan.get('pair_count')}.")
    if list(plan.get("seeds", [])) != [42, 43, 44]:
        raise ValueError(f"K3 plan seeds must be [42, 43, 44], found {plan.get('seeds')}.")

    planned_pairs = {
        (
            pair["pair_type"],
            pair["control_variant"],
            pair["treatment_variant"],
            pair["changed_field"],
        )
        for pair in plan.get("controlled_pairs", [])
    }
    payload_pairs = {
        (
            pair["pair_type"],
            pair["control_variant"],
            pair["treatment_variant"],
            pair["changed_field"],
        )
        for pair in declared_pairs
    }
    if planned_pairs != payload_pairs:
        raise ValueError("K3 controlled-pair payload does not match the declared plan.")

    validated_pairs = 0
    for pair in declared_pairs:
        validated_pairs += 1
        control = variants[pair["control_variant"]]["training_metadata"]
        treatment = variants[pair["treatment_variant"]]["training_metadata"]
        if control["dataset_hashes"] != treatment["dataset_hashes"]:
            raise ValueError(f"K3 pair dataset hashes differ: {pair}")
        if control["config"]["seed"] != treatment["config"]["seed"]:
            raise ValueError(f"K3 pair seed differs: {pair}")
        differing = {
            field
            for field in ("sigreg_enabled", "action_mode")
            if control.get(field) != treatment.get(field)
        }
        if pair["pair_type"] == "sigreg":
            if differing != {"sigreg_enabled"}:
                raise ValueError(
                    f"K3 SIGReg pair must differ only in sigreg_enabled; found {sorted(differing)}."
                )
        elif pair["pair_type"] == "action_conditioning":
            if differing != {"action_mode"}:
                raise ValueError(
                    f"K3 action-conditioning pair must differ only in action_mode; found {sorted(differing)}."
                )
        else:
            raise ValueError(f"Unsupported K3 pair_type: {pair['pair_type']!r}")
    return {"validated_pair_count": validated_pairs}


def _write_report(summary: dict[str, Any], path: Path) -> Path:
    lines = [
        "# K3 Ablation Intake Report",
        "",
        f"- Status: `{summary['status']}`",
        f"- Bundle source: `{summary['bundle_source']}`",
        f"- Variant count: `{summary['variant_count']}`",
        f"- Controlled pair count: `{summary['pair_count']}`",
        f"- Seeds: `{summary['seeds']}`",
        f"- Locked test materialized: `{str(summary['locked_test_materialized']).lower()}`",
        f"- Locked test scored: `{str(summary['locked_test_scored']).lower()}`",
    ]
    if summary.get("bundle_sha256_verification"):
        lines.append(f"- Bundle SHA256: `{summary['bundle_sha256_verification']['sha256']}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def ingest_bundle(*, bundle: Path, output_root: Path) -> dict[str, Any]:
    bundle_root, sidecar = _resolve_bundle_root(bundle)
    plan_path = bundle_root / "r6_ablation_plan.json"
    pairs_path = bundle_root / "r6_controlled_pairs.json"
    receipt_path = bundle_root / "r6_ablation_receipt.json"
    for path in (plan_path, pairs_path, receipt_path):
        if not path.is_file():
            raise FileNotFoundError(f"Missing required K3 intake artifact: {path}")

    plan = _read_json(plan_path)
    pairs_payload = _read_json(pairs_path)
    receipt = _read_json(receipt_path)
    _assert_false_flags(plan, context="plan")
    _assert_false_flags(pairs_payload, context="controlled_pairs")
    _assert_false_flags(receipt, context="receipt")

    pair_summary = _validate_controlled_pairs(
        plan=plan, pairs_payload=pairs_payload, receipt=receipt
    )
    variants = _variant_lookup(receipt)
    output_root.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "k3_ablation_bundle_validated",
        "bundle_source": str(bundle),
        "bundle_root": str(bundle_root),
        "bundle_sha256_verification": sidecar,
        "variant_count": len(variants),
        "pair_count": pair_summary["validated_pair_count"],
        "seeds": plan["seeds"],
        "train_path": plan["train_path"],
        "validation_path": plan["validation_path"],
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }
    summary_path = _write_json(output_root / "k3_ablation_intake_summary.json", summary)
    report_path = _write_report(summary, output_root / "K3_ABLATION_INTAKE_REPORT.md")
    return {
        **summary,
        "summary_path": str(summary_path),
        "summary_sha256": _sha256(summary_path),
        "report_path": str(report_path),
        "report_sha256": _sha256(report_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a downloaded K3 ablation bundle.")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs") / "k3_ablation_intake",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = ingest_bundle(bundle=args.bundle, output_root=args.output_root)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
