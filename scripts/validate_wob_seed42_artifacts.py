from __future__ import annotations

import json

from scripts.validate_wob_seed_artifacts import (
    build_parser,
    run_from_args,
    validate_artifact_tarball,
    validate_artifacts,
)

__all__ = [
    "validate_artifacts",
    "validate_artifact_tarball",
]


def main(argv: list[str] | None = None) -> None:
    parser = build_parser(
        description="Validate WOB seed42 training artifacts.",
        default_seed=42,
    )
    args = parser.parse_args(argv)
    result = run_from_args(args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
