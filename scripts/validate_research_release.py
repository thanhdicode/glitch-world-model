from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    "README.md",
    "AGENTS.md",
    "docs/research/16_claim_registry.md",
    "docs/research/31_phase6e_kaggle_validation_results.md",
    "paper/main.tex",
    "paper/references.bib",
    "pyproject.toml",
    "tests",
)
PROHIBITED_SUFFIXES = {".pt", ".pth", ".ckpt"}
PROHIBITED_PREFIXES = ("outputs/", "data/raw/", "data/processed/")
PROHIBITED_NAMES = {"kaggle.json", ".env"}
PROHIBITED_FRAGMENTS = ("access_token", "private_key", "id_rsa", "id_ed25519")


def git_tracked_files(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def validate_tracked_files(tracked_files: list[str]) -> list[str]:
    errors: list[str] = []
    for tracked in tracked_files:
        normalized = tracked.replace("\\", "/")
        path = Path(normalized)
        lowered = normalized.lower()
        if path.name == ".gitkeep":
            continue
        prohibited = (
            path.suffix.lower() in PROHIBITED_SUFFIXES
            or path.name.lower() in PROHIBITED_NAMES
            or lowered.startswith(PROHIBITED_PREFIXES)
            or any(fragment in lowered for fragment in PROHIBITED_FRAGMENTS)
        )
        if prohibited:
            errors.append(f"prohibited tracked file: {tracked}")
    return errors


def validate_required_paths(root: Path) -> list[str]:
    return [
        f"missing required path: {relative}"
        for relative in REQUIRED_PATHS
        if not (root / relative).exists()
    ]


def validate_release(root: Path, tracked_files: list[str] | None = None) -> list[str]:
    tracked = tracked_files if tracked_files is not None else git_tracked_files(root)
    return [*validate_required_paths(root), *validate_tracked_files(tracked)]


def working_tree_errors(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return ["git working tree is not clean"] if completed.stdout.strip() else []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate research release policy.")
    parser.add_argument("--strict", action="store_true", help="Require a clean Git working tree.")
    parser.add_argument("--ci", action="store_true", help="CI-friendly release validation.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors = validate_release(ROOT)
    if args.strict:
        errors.extend(working_tree_errors(ROOT))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Research release validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
