from __future__ import annotations

import json
import tarfile
from pathlib import Path

from scripts.ingest_k3_ablation_bundle import ingest_bundle


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _valid_bundle_dir(root: Path) -> Path:
    bundle = root / "bundle"
    bundle.mkdir()
    plan = {
        "status": "training_complete_unvalidated",
        "train_path": "inputs/train.lance",
        "validation_path": "inputs/validation.lance",
        "variant_count": 12,
        "pair_count": 12,
        "seeds": [42, 43, 44],
        "locked_test_materialized": False,
        "locked_test_scored": False,
        "controlled_pairs": [],
    }
    variants = []
    pairs = []
    for seed in (42, 43, 44):
        for sigreg_enabled, sigreg_name in ((True, "on"), (False, "off")):
            for action_mode in ("real", "zero_action"):
                variants.append(
                    {
                        "variant_name": f"seed{seed}_sigreg_{sigreg_name}_{action_mode}",
                        "training_metadata": {
                            "dataset_hashes": {"train": "trainhash", "validation": "valhash"},
                            "config": {"seed": seed},
                            "sigreg_enabled": sigreg_enabled,
                            "action_mode": action_mode,
                        },
                    }
                )
        pairs.extend(
            [
                {
                    "pair_type": "sigreg",
                    "control_variant": f"seed{seed}_sigreg_off_real",
                    "treatment_variant": f"seed{seed}_sigreg_on_real",
                    "changed_field": "sigreg_enabled",
                },
                {
                    "pair_type": "sigreg",
                    "control_variant": f"seed{seed}_sigreg_off_zero_action",
                    "treatment_variant": f"seed{seed}_sigreg_on_zero_action",
                    "changed_field": "sigreg_enabled",
                },
                {
                    "pair_type": "action_conditioning",
                    "control_variant": f"seed{seed}_sigreg_on_zero_action",
                    "treatment_variant": f"seed{seed}_sigreg_on_real",
                    "changed_field": "action_mode",
                },
                {
                    "pair_type": "action_conditioning",
                    "control_variant": f"seed{seed}_sigreg_off_zero_action",
                    "treatment_variant": f"seed{seed}_sigreg_off_real",
                    "changed_field": "action_mode",
                },
            ]
        )
    plan["controlled_pairs"] = pairs
    _write_json(bundle / "r6_ablation_plan.json", plan)
    _write_json(
        bundle / "r6_controlled_pairs.json",
        {
            "status": "controlled_pairs_declared",
            "pairs": pairs,
            "variant_count": 12,
            "locked_test_materialized": False,
            "locked_test_scored": False,
        },
    )
    _write_json(
        bundle / "r6_ablation_receipt.json",
        {
            **plan,
            "executed_variants": variants,
        },
    )
    return bundle


def test_ingest_k3_bundle_from_directory(tmp_path: Path):
    bundle = _valid_bundle_dir(tmp_path)
    result = ingest_bundle(bundle=bundle, output_root=tmp_path / "intake")

    assert result["status"] == "k3_ablation_bundle_validated"
    assert result["variant_count"] == 12
    assert result["pair_count"] == 12
    assert Path(result["summary_path"]).is_file()
    assert Path(result["report_path"]).is_file()


def test_ingest_k3_bundle_rejects_mismatched_pairs(tmp_path: Path):
    bundle = _valid_bundle_dir(tmp_path)
    payload = json.loads((bundle / "r6_controlled_pairs.json").read_text(encoding="utf-8"))
    payload["pairs"][0]["treatment_variant"] = "seed42_sigreg_on_zero_action"
    _write_json(bundle / "r6_controlled_pairs.json", payload)

    try:
        ingest_bundle(bundle=bundle, output_root=tmp_path / "intake")
    except ValueError as exc:
        assert "controlled-pair payload does not match the declared plan" in str(exc)
    else:
        raise AssertionError("Expected K3 intake to reject mismatched controlled pairs.")


def test_ingest_k3_bundle_verifies_tarball_sidecar(tmp_path: Path):
    bundle = _valid_bundle_dir(tmp_path)
    tarball = tmp_path / "k3_bundle.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        for child in bundle.iterdir():
            archive.add(child, arcname=child.name)
    sha = __import__("hashlib").sha256(tarball.read_bytes()).hexdigest()
    (tmp_path / "k3_bundle.tar.gz.sha256").write_text(f"{sha}  {tarball.name}\n", encoding="utf-8")

    result = ingest_bundle(bundle=tarball, output_root=tmp_path / "intake")

    assert result["bundle_sha256_verification"]["sha256_verified"] is True
