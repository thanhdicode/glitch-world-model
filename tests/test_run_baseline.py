from pathlib import Path

import pytest
from PIL import Image

from glitch_detection.run_baseline import run_baseline


def test_run_baseline_creates_all_outputs(tmp_path: Path):
    frame_dir = tmp_path / "frames"
    frame_dir.mkdir()
    for index in range(12):
        value = 220 if 4 <= index <= 7 else 30
        Image.new("RGB", (16, 16), color=(value, value, value)).save(
            frame_dir / f"frame_{index:06d}.png"
        )

    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "source,start_frame,end_frame,label\nframes,4,7,1\n",
        encoding="utf-8",
    )

    outputs = run_baseline(
        input_path=frame_dir,
        labels_path=labels_path,
        experiment_name="tiny",
        clip_length=4,
        stride=2,
        size=16,
        fps=30.0,
        data_dir=tmp_path / "processed",
        outputs_dir=tmp_path / "outputs",
        scorer_name="frame_diff",
    )

    for path in outputs.values():
        assert path.exists()
    assert outputs["metrics"].read_text(encoding="utf-8")


def test_run_baseline_rejects_train_dependent_scorer_without_demo_opt_in(tmp_path: Path):
    with pytest.raises(ValueError, match="demo_allow_evaluation_label_fitting"):
        run_baseline(
            input_path=tmp_path / "frames",
            labels_path=tmp_path / "labels.csv",
            experiment_name="unsafe",
            clip_length=4,
            stride=2,
            size=16,
            fps=30.0,
            data_dir=tmp_path / "processed",
            outputs_dir=tmp_path / "outputs",
            scorer_name="mini_latent",
        )
