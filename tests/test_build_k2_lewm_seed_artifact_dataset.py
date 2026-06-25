from __future__ import annotations

import json
from pathlib import Path

from scripts.build_k2_lewm_seed_artifact_dataset import build_k2_lewm_seed_artifact_dataset


def _seed_root(tmp_path: Path, seed: int) -> Path:
    root = tmp_path / f"seed{seed}"
    root.mkdir(parents=True, exist_ok=True)
    (root / "best_weights.pt").write_bytes(f"weights-{seed}".encode("utf-8"))
    (root / "config.json").write_text(json.dumps({"seed": seed}), encoding="utf-8")
    (root / "checkpoint.sha256").write_text("hash\n", encoding="utf-8")
    (root / "training_metadata.json").write_text(
        json.dumps({"seed": seed, "status": "ready"}), encoding="utf-8"
    )
    return root


def test_build_k2_lewm_seed_artifact_dataset_normalizes_seed_layout(tmp_path: Path):
    audit = build_k2_lewm_seed_artifact_dataset(
        output_root=tmp_path / "out",
        seed42_root=_seed_root(tmp_path, 42),
        seed43_root=_seed_root(tmp_path, 43),
        seed44_root=_seed_root(tmp_path, 44),
    )

    package_root = Path(audit["package_root"])
    assert audit["status"] == "k2_lewm_seed_artifacts_ready"
    assert (package_root / "seed42" / "best_weights.pt").is_file()
    assert (package_root / "seed43" / "config.json").is_file()
    assert (package_root / "seed44" / "training_metadata.json").is_file()
    assert Path(audit["zip_path"]).is_file()
    assert Path(audit["zip_sha256_path"]).is_file()
