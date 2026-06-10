from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from .manifest import ClipRecord, clip_has_glitch, read_labels, read_manifest
from .preprocess import IMAGE_EXTENSIONS


@dataclass(frozen=True)
class MiniLatentModel:
    mean: np.ndarray
    components: np.ndarray
    weights: np.ndarray
    image_size: int


def list_clip_frames(clip_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in clip_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def load_frame_vector(path: Path, image_size: int) -> np.ndarray:
    with Image.open(path) as image:
        gray = image.convert("L").resize((image_size, image_size), Image.Resampling.BILINEAR)
        return np.asarray(gray, dtype=np.float32).reshape(-1) / 255.0


def load_clip_matrix(clip_dir: Path, image_size: int) -> np.ndarray:
    frames = list_clip_frames(clip_dir)
    if not frames:
        return np.zeros((0, image_size * image_size), dtype=np.float32)
    return np.stack([load_frame_vector(path, image_size) for path in frames])


def fit_pca_encoder(frame_matrix: np.ndarray, latent_dim: int) -> tuple[np.ndarray, np.ndarray]:
    mean = frame_matrix.mean(axis=0)
    centered = frame_matrix - mean
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    components = vt[: min(latent_dim, vt.shape[0])]
    if components.shape[0] < latent_dim:
        pad = np.zeros((latent_dim - components.shape[0], frame_matrix.shape[1]), dtype=np.float32)
        components = np.vstack([components, pad])
    return mean.astype(np.float32), components.astype(np.float32)


def encode_frames(frame_matrix: np.ndarray, mean: np.ndarray, components: np.ndarray) -> np.ndarray:
    return (frame_matrix - mean) @ components.T


def fit_transition(latents: list[np.ndarray]) -> np.ndarray:
    sources: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    for clip_latents in latents:
        if len(clip_latents) < 3:
            continue
        velocity = clip_latents[1:-1] - clip_latents[:-2]
        sources.append(np.hstack([clip_latents[1:-1], velocity]))
        targets.append(clip_latents[2:])

    if not sources:
        dim = latents[0].shape[1]
        weights = np.zeros((2 * dim + 1, dim), dtype=np.float32)
        weights[:dim, :] = np.eye(dim, dtype=np.float32)
        return weights

    x = np.vstack(sources)
    y = np.vstack(targets)
    x_aug = np.hstack([x, np.ones((x.shape[0], 1), dtype=np.float32)])
    weights, *_ = np.linalg.lstsq(x_aug, y, rcond=None)
    return weights.astype(np.float32)


def transition_error(clip_latents: np.ndarray, weights: np.ndarray) -> float:
    if len(clip_latents) < 3:
        return 0.0
    velocity = clip_latents[1:-1] - clip_latents[:-2]
    x = np.hstack([clip_latents[1:-1], velocity])
    y = clip_latents[2:]
    x_aug = np.hstack([x, np.ones((x.shape[0], 1), dtype=np.float32)])
    predictions = x_aug @ weights
    return float(np.mean(np.linalg.norm(predictions - y, axis=1)))


def fit_model(
    records: list[ClipRecord],
    latent_dim: int = 8,
    image_size: int = 32,
) -> MiniLatentModel:
    matrices = [load_clip_matrix(Path(record.clip_dir), image_size) for record in records]
    matrices = [matrix for matrix in matrices if len(matrix) > 0]
    if not matrices:
        raise ValueError("Need at least one non-empty training record to fit mini_latent.")

    mean, components = fit_pca_encoder(np.vstack(matrices), latent_dim)
    latents = [encode_frames(matrix, mean, components) for matrix in matrices]
    weights = fit_transition([latent for latent in latents if len(latent) > 1])
    return MiniLatentModel(
        mean=mean,
        components=components,
        weights=weights,
        image_size=image_size,
    )


def score_records_with_model(
    records: list[ClipRecord],
    model: MiniLatentModel,
) -> dict[str, float]:
    scores: dict[str, float] = {}
    for record in records:
        matrix = load_clip_matrix(Path(record.clip_dir), model.image_size)
        latents = encode_frames(matrix, model.mean, model.components)
        scores[record.clip_id] = transition_error(latents, model.weights)
    return scores


def score_records(
    records: list[ClipRecord],
    labels: list[int],
    latent_dim: int = 8,
    image_size: int = 32,
) -> dict[str, float]:
    normal_records = [record for record, label in zip(records, labels) if label == 0]
    model = fit_model(normal_records or records, latent_dim=latent_dim, image_size=image_size)
    return score_records_with_model(records, model)


def score_manifest(
    manifest_path: Path,
    labels_path: Path | None,
    output_path: Path,
    latent_dim: int = 8,
    image_size: int = 32,
) -> Path:
    records = read_manifest(manifest_path)
    intervals = read_labels(labels_path)
    labels = [
        int(clip_has_glitch(record.source, record.start_frame, record.end_frame, intervals))
        for record in records
    ]
    scores = score_records(records, labels, latent_dim=latent_dim, image_size=image_size)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["clip_id", "source", "clip_dir", "start_frame", "end_frame", "score"],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "clip_id": record.clip_id,
                    "source": record.source,
                    "clip_dir": record.clip_dir,
                    "start_frame": record.start_frame,
                    "end_frame": record.end_frame,
                    "score": f"{scores[record.clip_id]:.8f}",
                }
            )
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score clips with a mini latent transition model.")
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest.csv.")
    parser.add_argument(
        "--labels", type=Path, default=None, help="Optional labels CSV for demo-only fitting."
    )
    parser.add_argument("--output", required=True, type=Path, help="Output scores.csv path.")
    parser.add_argument("--latent-dim", type=int, default=8)
    parser.add_argument("--image-size", type=int, default=32)
    parser.add_argument(
        "--demo-allow-evaluation-label-fitting",
        action="store_true",
        help="Unsafe for benchmark claims; fit the model using labels from this manifest.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if not args.demo_allow_evaluation_label_fitting:
        raise SystemExit(
            "mini_latent CLI is demo-only because it fits on the supplied manifest. "
            "Use a split-aware experiment runner or pass --demo-allow-evaluation-label-fitting."
        )
    output_path = score_manifest(
        args.manifest,
        args.labels,
        args.output,
        latent_dim=args.latent_dim,
        image_size=args.image_size,
    )
    print(f"Wrote scores: {output_path}")


if __name__ == "__main__":
    main()
