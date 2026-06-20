from __future__ import annotations

import json

from glitch_detection.wob_p0_audit import WobP0Config, build_parser, run_audit


def main() -> None:
    args = build_parser().parse_args()
    report = run_audit(
        WobP0Config(
            wob_root=args.wob_root,
            output_dir=args.output_dir,
            split_path=args.split_path,
            protocol_audit_path=args.protocol_audit_path,
            split_audit_path=args.split_audit_path,
            dry_run=args.dry_run,
            allow_materialization_check=args.allow_materialization_check,
            no_locked=args.no_locked,
            write_manifest_preview=args.write_manifest_preview,
        )
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
