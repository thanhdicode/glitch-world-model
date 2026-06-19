from __future__ import annotations

import io
import tarfile
from pathlib import Path

TRACKED_SPLIT = Path("configs/wob_protocol/split.csv")
FALLBACK_SPLIT = Path("outputs/gate3/world_of_bugs/split.csv")
TRACKED_PROTOCOL_AUDIT = Path("configs/wob_protocol/protocol_audit.json")
FALLBACK_PROTOCOL_AUDIT = Path("outputs/gate3/world_of_bugs/protocol_audit.json")
TRACKED_SPLIT_AUDIT = Path("configs/wob_protocol/split.audit.json")
FALLBACK_SPLIT_AUDIT = Path("outputs/gate3/world_of_bugs/split.audit.json")


def resolve_existing_path(repo_root: Path, preferred: Path, fallback: Path) -> Path:
    preferred_path = repo_root / preferred
    if preferred_path.is_file():
        return preferred_path
    fallback_path = repo_root / fallback
    if fallback_path.is_file():
        return fallback_path
    raise FileNotFoundError(f"Missing required file. Tried {preferred_path} and {fallback_path}.")


def resolve_split_csv(repo_root: Path) -> Path:
    return resolve_existing_path(repo_root, TRACKED_SPLIT, FALLBACK_SPLIT)


def resolve_protocol_audit(repo_root: Path) -> Path:
    return resolve_existing_path(repo_root, TRACKED_PROTOCOL_AUDIT, FALLBACK_PROTOCOL_AUDIT)


def resolve_split_audit(repo_root: Path) -> Path:
    return resolve_existing_path(repo_root, TRACKED_SPLIT_AUDIT, FALLBACK_SPLIT_AUDIT)


def detect_kaggle_roots(input_root: Path) -> tuple[Path, Path]:
    common_normal = [
        input_root / "world-of-bugs-normal",
        input_root / "world-of-bugs-train",
        input_root / "datasets" / "benedictwilkinsai" / "world-of-bugs-normal",
        input_root / "datasets" / "benedictwilkinsai" / "world-of-bugs-train",
    ]
    common_test = [
        input_root / "world-of-bugs-test",
        input_root / "datasets" / "benedictwilkinsai" / "world-of-bugs-test",
    ]

    def exact_match(candidates: list[Path], marker: str) -> Path | None:
        for candidate in candidates:
            if (candidate / marker).exists():
                return candidate
        return None

    def keyword_score(path: Path, keywords: tuple[str, ...]) -> tuple[int, int, str]:
        lowered = str(path).lower()
        score = sum(1 for keyword in keywords if keyword in lowered)
        return score, -len(lowered), lowered

    def fallback_match(marker: str, keywords: tuple[str, ...]) -> Path:
        candidates: list[Path] = []
        for path in input_root.rglob("*"):
            if path.is_dir() and path.name == marker:
                candidates.append(path.parent)

        unique_candidates = sorted(set(candidates))
        if not unique_candidates:
            raise FileNotFoundError(
                f"Could not detect Kaggle WOB root containing marker {marker!r}."
            )
        if len(unique_candidates) == 1:
            return unique_candidates[0]

        ranked = sorted(
            unique_candidates,
            key=lambda path: keyword_score(path, keywords),
            reverse=True,
        )
        best = ranked[0]
        best_score = keyword_score(best, keywords)
        tied = [path for path in ranked if keyword_score(path, keywords) == best_score]
        if best_score[0] > 0 and len(tied) == 1:
            return best

        raise FileNotFoundError(
            "Could not uniquely detect Kaggle WOB roots containing NORMAL-TRAIN and TEST. "
            f"Candidates for {marker!r}: {[str(path) for path in unique_candidates]}"
        )

    normal = exact_match(common_normal, "NORMAL-TRAIN")
    if normal is None:
        normal = fallback_match("NORMAL-TRAIN", ("world-of-bugs", "normal", "train"))

    test = exact_match(common_test, "TEST")
    if test is None:
        test = fallback_match("TEST", ("world-of-bugs", "test"))

    return normal, test


def add_tree_to_tar(
    archive: tarfile.TarFile, root: Path, prefix: str, *, exclude_suffixes: tuple[str, ...]
) -> None:
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if path.suffix in exclude_suffixes or any(
            str(path).endswith(suffix) for suffix in exclude_suffixes
        ):
            continue
        relative = path.relative_to(root)
        archive.add(path, arcname=str(Path(prefix) / relative))


def write_debug_tarball(
    output_path: Path,
    roots: list[tuple[Path, str]],
    *,
    exclude_suffixes: tuple[str, ...] = (".tar",),
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output_path, "w:gz") as archive:
        for root, prefix in roots:
            if root.exists():
                add_tree_to_tar(archive, root, prefix, exclude_suffixes=exclude_suffixes)


def write_text_tarball(output_path: Path, files: dict[str, str]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output_path, "w:gz") as archive:
        for name, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
