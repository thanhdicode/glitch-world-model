from __future__ import annotations

import json

from glitch_detection.r5_tempglitch_eval import (
    build_parser,
    parse_seed_artifact_roots,
    run_r5_tempglitch_identical_episode_evaluation,
)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    result = run_r5_tempglitch_identical_episode_evaluation(
        train_lance=args.train_lance,
        validation_normal_lance=args.validation_normal_lance,
        validation_buggy_lance=args.validation_buggy_lance,
        seed_artifact_roots=parse_seed_artifact_roots(args.seed_artifact_root),
        output_dir=args.output_dir,
        device=args.device,
        batch_size=args.batch_size,
        include_conv3d=args.include_conv3d,
        include_frozen_video_rep=args.include_frozen_video_rep,
        dry_run=args.dry_run,
        bootstrap_seed=args.bootstrap_seed,
        n_bootstrap=args.n_bootstrap,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
