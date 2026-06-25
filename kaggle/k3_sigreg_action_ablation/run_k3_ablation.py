from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from glitch_detection.kaggle_automation import FingerprintBuilder


def _load_runner():
    module_path = REPO_ROOT / "scripts" / "run_r6_sigreg_ablation.py"
    spec = importlib.util.spec_from_file_location("_k3_run_r6_sigreg_ablation", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load K3 runner: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the K3 SIGReg/action ablation matrix.")
    parser.add_argument(
        "--input-manifest",
        type=Path,
        default=PACKAGE_DIR / "k3_input_manifest.json",
    )
    parser.add_argument("--train-path", type=Path, default=None)
    parser.add_argument("--validation-path", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=Path("/kaggle/working/r6_sigreg_ablation"))
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--resume", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = _read_manifest(args.input_manifest)
    if manifest.get("status") != "prepared":
        raise ValueError(
            "K3 scientific run requires a prepared input manifest. "
            f"Current manifest status: {manifest.get('status')!r}"
        )
    train_path = (args.train_path or Path(manifest["train_path"])).resolve()
    validation_path = (args.validation_path or Path(manifest["validation_path"])).resolve()
    for name, path in (("train", train_path), ("validation", validation_path)):
        if not path.exists():
            raise FileNotFoundError(f"Missing K3 {name} input path: {path}")
    if args.device != "cuda":
        raise ValueError("Scientific K3 runs must request --device cuda.")

    expected_train_hash = manifest["dataset_hashes"]["train"]
    expected_validation_hash = manifest["dataset_hashes"]["validation"]
    actual_train_hash = FingerprintBuilder.inventory_sha256(train_path)
    actual_validation_hash = FingerprintBuilder.inventory_sha256(validation_path)
    if actual_train_hash != expected_train_hash:
        raise ValueError(
            f"K3 train dataset hash mismatch: expected {expected_train_hash}, found {actual_train_hash}"
        )
    if actual_validation_hash != expected_validation_hash:
        raise ValueError(
            "K3 validation dataset hash mismatch: "
            f"expected {expected_validation_hash}, found {actual_validation_hash}"
        )

    runner = _load_runner()
    base_config = runner.LeWMTrainConfig(
        image_size=112,
        history_size=3,
        embed_dim=192,
        batch_size=4,
        learning_rate=5e-5,
        weight_decay=1e-3,
        sigreg_weight=0.09,
        sigreg_projections=128,
        run_kind="research",
        target_optimizer_updates=500,
        evaluation_interval_updates=100,
        checkpoint_interval_updates=100,
    )
    receipt = runner.run_r6_sigreg_ablation(
        train_path=train_path,
        validation_path=validation_path,
        output_root=args.output_root,
        seeds=[42, 43, 44],
        base_config=base_config,
        device=args.device,
        dry_run=False,
        resume=args.resume,
    )
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
