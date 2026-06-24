from __future__ import annotations

from glitch_detection.glitchbench_protocol import GlitchBenchRecord
from scripts.freeze_glitchbench_split import freeze_glitchbench_support


def _record(index: int, label: str) -> GlitchBenchRecord:
    source = f"group_{index}_{label.lower()}"
    return GlitchBenchRecord(
        source=source,
        clip_id=f"{source}_clip",
        clip_dir=f"/tmp/{source}",
        image_path=f"/tmp/{source}.png",
        record_id=f"record-{index}",
        reddit_id=f"reddit-{index}",
        game="Game",
        glitch_type="Physics",
        source_domain="Social Media",
        raw_label="synthetic_normal" if label == "Normal" else "glitch",
        mapped_label=label,
        group_key=f"reddit-{index}",
        synthetic_normal=label == "Normal",
        temporal_label_available=False,
    )


def _records(count: int = 8) -> list[GlitchBenchRecord]:
    rows: list[GlitchBenchRecord] = []
    for index in range(count):
        rows.append(_record(index, "Normal"))
        rows.append(_record(index, "Buggy"))
    return rows


def test_freeze_glitchbench_split_is_deterministic_and_train_normal_only():
    selected_a, split_a, audit_a = freeze_glitchbench_support(
        _records(), seed=42, validation_ratio=0.4
    )
    selected_b, split_b, audit_b = freeze_glitchbench_support(
        _records(), seed=42, validation_ratio=0.4
    )

    assert selected_a == selected_b
    assert split_a == split_b
    assert audit_a == audit_b
    assert all(row.label == "Normal" for row in split_a if row.split == "train")
    assert {row.label for row in split_a if row.split == "validation"} == {"Normal", "Buggy"}
