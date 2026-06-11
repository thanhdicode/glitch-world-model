from __future__ import annotations

import argparse
import json
from pathlib import Path

from glitch_detection.lewm_kaggle import validate_lewm_smoke_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Strictly validate downloaded LeWM smoke artifacts."
    )
    parser.add_argument("--artifacts-root", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = validate_lewm_smoke_artifacts(args.artifacts_root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
