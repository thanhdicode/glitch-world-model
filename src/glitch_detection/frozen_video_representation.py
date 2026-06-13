from __future__ import annotations

import importlib.util
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FrozenVideoRepresentationConfig:
    candidates: tuple[str, ...] = ("videomae-small", "timesformer-small")
    allow_downloads: bool = False
    blocks_lewm_critical_path: bool = False


def dependency_status() -> dict[str, bool]:
    return {
        "torch": importlib.util.find_spec("torch") is not None,
        "transformers": importlib.util.find_spec("transformers") is not None,
    }


def plan_frozen_video_representation_baseline(
    output_root: Path,
    config: FrozenVideoRepresentationConfig | None = None,
) -> dict[str, Any]:
    resolved = config or FrozenVideoRepresentationConfig()
    status = dependency_status()
    output_root.mkdir(parents=True, exist_ok=True)
    if not all(status.values()):
        payload = {
            "status": "skipped",
            "reason": "missing_optional_dependency",
            "dependency_status": status,
            "config": asdict(resolved),
            "blocks_lewm_critical_path": resolved.blocks_lewm_critical_path,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        (output_root / "frozen_video_representation_skip.json").write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        return payload
    payload = {
        "status": "ready",
        "reason": "optional_dependencies_available",
        "dependency_status": status,
        "config": asdict(resolved),
        "blocks_lewm_critical_path": resolved.blocks_lewm_critical_path,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "next_step": "score identical R5 episode manifest with a frozen encoder adapter",
    }
    (output_root / "frozen_video_representation_plan.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload
