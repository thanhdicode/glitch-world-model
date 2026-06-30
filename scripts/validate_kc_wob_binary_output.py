from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_READINESS_JSON = REPO_ROOT / "configs" / "wob_protocol" / "wob_expansion_readiness.json"
DEFAULT_OUTPUT_DIR = Path("/kaggle/working/kc_wob_binary")
REQUIRED_STAGE_MARKERS = (
    "stage_preflight.json",
    "stage_materialize_lance.json",
    "stage_baseline_scores.json",
    "stage_lewm_seed42.json",
    "stage_lewm_seed43.json",
    "stage_lewm_seed44.json",
    "stage_aggregate_metrics.json",
    "stage_validate_package.json",
)


def _load_r5_validator() -> Any:
    module_path = Path(__file__).resolve().with_name("validate_r5_wob_evaluation.py")
    spec = importlib.util.spec_from_file_location("_kc_validate_r5_wob_evaluation", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load validator module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_kc_wob_binary(output_dir: Path, readiness_json: Path) -> dict[str, Any]:
    """Validate a full K-C WOB binary output directory without weakening R5-WOB gates."""
    core = _load_r5_validator().validate_r5_wob(output_dir, readiness_json)
    missing_markers = [name for name in REQUIRED_STAGE_MARKERS if not (output_dir / name).is_file()]
    if missing_markers:
        raise ValueError(f"missing K-C stage marker(s): {', '.join(missing_markers)}")

    metrics = json.loads((output_dir / "r5_wob_metrics.json").read_text(encoding="utf-8-sig"))
    if metrics.get("smoke") is True or metrics.get("paper_valid") is False:
        raise ValueError("K-C WOB binary validation requires a full non-smoke output bundle.")

    return {
        "status": "kc_wob_binary_validated",
        "protocol": "wob_identical_episode_nonlocked",
        "output_dir": str(output_dir),
        "core_validator": core,
        "stage_markers_present": list(REQUIRED_STAGE_MARKERS),
        "paper_valid": True,
        "validation_buggy_used_for_fit_select": False,
        "locked_test_materialized": False,
        "locked_test_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate K-C WOB binary outputs and staged markers."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--readiness-json", type=Path, default=DEFAULT_READINESS_JSON)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(json.dumps(validate_kc_wob_binary(args.output_dir, args.readiness_json), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
