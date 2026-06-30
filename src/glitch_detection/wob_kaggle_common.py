from __future__ import annotations

import io
import os
import tarfile
from pathlib import Path

TRACKED_SPLIT = Path("configs/wob_protocol/split.csv")
FALLBACK_SPLIT = Path("outputs/gate3/world_of_bugs/split.csv")
TRACKED_PROTOCOL_AUDIT = Path("configs/wob_protocol/protocol_audit.json")
FALLBACK_PROTOCOL_AUDIT = Path("outputs/gate3/world_of_bugs/protocol_audit.json")
TRACKED_SPLIT_AUDIT = Path("configs/wob_protocol/split.audit.json")
FALLBACK_SPLIT_AUDIT = Path("outputs/gate3/world_of_bugs/split.audit.json")
SUPPORTED_WOB_SEEDS = (42, 43, 44)


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


def _path_from_env(names: tuple[str, ...], *, kind: str) -> Path | None:
    for name in names:
        raw = os.environ.get(name)
        if not raw:
            continue
        path = Path(raw)
        if kind == "file" and not path.is_file():
            raise FileNotFoundError(f"Environment override {name} points to missing file: {path}")
        if kind == "dir" and not path.is_dir():
            raise FileNotFoundError(
                f"Environment override {name} points to missing directory: {path}"
            )
        return path
    return None


def _keyword_score(path: Path, keywords: tuple[str, ...]) -> tuple[int, int, str]:
    lowered = str(path).lower()
    score = sum(1 for keyword in keywords if keyword in lowered)
    return score, -len(lowered), lowered


def _select_candidate(
    candidates: list[Path],
    *,
    description: str,
    keywords: tuple[str, ...],
) -> Path:
    unique_candidates = sorted(set(candidates))
    if not unique_candidates:
        raise FileNotFoundError(f"Could not detect Kaggle path for {description}.")
    if len(unique_candidates) == 1:
        return unique_candidates[0]

    ranked = sorted(
        unique_candidates,
        key=lambda path: _keyword_score(path, keywords),
        reverse=True,
    )
    best = ranked[0]
    best_score = _keyword_score(best, keywords)
    tied = [path for path in ranked if _keyword_score(path, keywords) == best_score]
    if best_score[0] > 0 and len(tied) == 1:
        return best

    raise FileNotFoundError(
        f"Could not uniquely detect Kaggle path for {description}. "
        f"Candidates: {[str(path) for path in unique_candidates]}"
    )


def iter_kaggle_dataset_roots(input_root: Path) -> list[Path]:
    if not input_root.is_dir():
        return []

    roots: list[Path] = []
    for child in sorted(input_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name != "datasets":
            roots.append(child)
            continue
        for owner in sorted(item for item in child.iterdir() if item.is_dir()):
            roots.extend(sorted(item for item in owner.iterdir() if item.is_dir()))
    return roots


def is_wob_seed_artifact_root(path: Path, *, seed: int) -> bool:
    """Return true for a direct Kaggle seed artifact folder.

    Upload-ready Kaggle datasets may expose seeds as ``seed42/`` directories
    containing the validated checkpoint files directly, instead of the original
    ``wob_seed42_artifacts/wob_outputs/wob_seed42/`` tarball layout.
    """
    if not path.is_dir():
        return False
    required = ("best_weights.pt", "config.json", "training_metadata.json")
    if not all((path / name).is_file() for name in required):
        return False
    expected_names = {f"seed{seed}", f"wob_seed{seed}"}
    return path.name in expected_names or path.parent.name in expected_names


def detect_kaggle_roots(input_root: Path) -> tuple[Path, Path]:
    env_normal = _path_from_env(("NORMAL_INPUT_ROOT", "R5_WOB_NORMAL_INPUT_ROOT"), kind="dir")
    env_test = _path_from_env(("TEST_INPUT_ROOT", "R5_WOB_TEST_INPUT_ROOT"), kind="dir")
    if env_normal is not None and env_test is not None:
        return env_normal, env_test

    dataset_roots = iter_kaggle_dataset_roots(input_root)
    normal_candidates = [root for root in dataset_roots if (root / "NORMAL-TRAIN").is_dir()]
    test_candidates = [root for root in dataset_roots if (root / "TEST").is_dir()]
    if not normal_candidates:
        raise FileNotFoundError(
            "Could not detect Kaggle WOB normal root containing 'NORMAL-TRAIN'. "
            f"Dataset roots: {[str(path) for path in dataset_roots]}"
        )
    if not test_candidates:
        raise FileNotFoundError(
            "Could not detect Kaggle WOB test root containing 'TEST'. "
            f"Dataset roots: {[str(path) for path in dataset_roots]}"
        )

    normal = _select_candidate(
        normal_candidates,
        description="WOB normal root",
        keywords=("world-of-bugs", "normal", "train"),
    )
    test = _select_candidate(
        test_candidates,
        description="WOB test root",
        keywords=("world-of-bugs", "test"),
    )
    return normal, test


def resolve_wob_seed_input(input_root: Path, *, seed: int) -> dict[str, Path | str]:
    tarball = _path_from_env(
        (f"WOB_SEED{seed}_TARBALL", f"R5_WOB_SEED{seed}_TARBALL"),
        kind="file",
    )
    sidecar = _path_from_env(
        (f"WOB_SEED{seed}_SHA256", f"R5_WOB_SEED{seed}_SHA256"),
        kind="file",
    )
    extracted_root = _path_from_env(
        (f"WOB_SEED{seed}_EXTRACTED_ROOT", f"R5_WOB_SEED{seed}_EXTRACTED_ROOT"),
        kind="dir",
    )
    if tarball is not None or sidecar is not None:
        if tarball is None or sidecar is None:
            raise FileNotFoundError(
                f"Seed {seed} overrides must provide both tarball and sha256 sidecar."
            )
        return {"mode": "direct_tarball", "tarball": tarball, "sidecar": sidecar}
    if extracted_root is not None:
        return {"mode": "extracted_root", "source_root": extracted_root}

    dataset_roots = iter_kaggle_dataset_roots(input_root)
    tar_name = f"wob_seed{seed}_artifacts.tar.gz"
    sha_name = f"{tar_name}.sha256"
    extracted_name = f"wob_seed{seed}_artifacts"
    tar_candidates = [root / tar_name for root in dataset_roots if (root / tar_name).is_file()]
    sha_candidates = [root / sha_name for root in dataset_roots if (root / sha_name).is_file()]
    extracted_candidates = [
        root / extracted_name
        for root in dataset_roots
        if (root / extracted_name / "wob_outputs" / f"wob_seed{seed}").is_dir()
    ]
    direct_seed_candidates = [
        root / f"seed{seed}"
        for root in dataset_roots
        if is_wob_seed_artifact_root(root / f"seed{seed}", seed=seed)
    ]
    direct_seed_candidates.extend(
        root / f"wob_seed{seed}"
        for root in dataset_roots
        if is_wob_seed_artifact_root(root / f"wob_seed{seed}", seed=seed)
    )

    if tar_candidates and sha_candidates:
        tarball = _select_candidate(
            tar_candidates,
            description=f"seed {seed} tarball",
            keywords=(f"seed{seed}", "artifact", "wob"),
        )
        sidecar = _select_candidate(
            sha_candidates,
            description=f"seed {seed} sidecar",
            keywords=(f"seed{seed}", "artifact", "wob"),
        )
        return {"mode": "direct_tarball", "tarball": tarball, "sidecar": sidecar}
    if extracted_candidates:
        source_root = _select_candidate(
            extracted_candidates,
            description=f"seed {seed} extracted root",
            keywords=(f"seed{seed}", "artifact", "wob"),
        )
        return {"mode": "extracted_root", "source_root": source_root}
    if direct_seed_candidates:
        source_root = _select_candidate(
            direct_seed_candidates,
            description=f"seed {seed} direct artifact root",
            keywords=(f"seed{seed}", "artifact", "wob"),
        )
        return {"mode": "direct_seed_root", "source_root": source_root}
    if tar_candidates or sha_candidates:
        missing_parts: list[str] = []
        if not tar_candidates:
            missing_parts.append("tarball")
        if not sha_candidates:
            missing_parts.append("sha256 sidecar")
        raise FileNotFoundError(
            f"Found only a partial seed {seed} artifact bundle under {input_root}; "
            f"missing {' and '.join(missing_parts)}."
        )

    raise FileNotFoundError(
        f"Could not locate seed {seed} artifact tarball, sidecar, extracted root, "
        f"or direct seed root under {input_root}. "
        f"Dataset roots: {[str(path) for path in dataset_roots]}"
    )


def discover_r5_wob_input_overrides(input_root: Path) -> dict[str, str]:
    normal_root, test_root = detect_kaggle_roots(input_root)
    overrides = {
        "NORMAL_INPUT_ROOT": str(normal_root),
        "TEST_INPUT_ROOT": str(test_root),
    }
    for seed in SUPPORTED_WOB_SEEDS:
        resolved = resolve_wob_seed_input(input_root, seed=seed)
        mode = str(resolved["mode"])
        if mode == "direct_tarball":
            overrides[f"WOB_SEED{seed}_TARBALL"] = str(resolved["tarball"])
            overrides[f"WOB_SEED{seed}_SHA256"] = str(resolved["sidecar"])
            continue
        if mode in {"extracted_root", "direct_seed_root"}:
            overrides[f"WOB_SEED{seed}_EXTRACTED_ROOT"] = str(resolved["source_root"])
            continue
        raise ValueError(f"Unsupported seed {seed} discovery mode: {mode}")
    return overrides


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
