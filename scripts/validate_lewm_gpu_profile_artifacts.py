from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    from glitch_detection.lewm_gpu_profile import validate_lewm_gpu_profile_artifacts

    parser = argparse.ArgumentParser(description="Strictly validate LeWM GPU profile artifacts.")
    parser.add_argument("--artifacts-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = validate_lewm_gpu_profile_artifacts(args.artifacts_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
