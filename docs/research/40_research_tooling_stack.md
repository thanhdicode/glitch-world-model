# Research Tooling Stack

## Layers

| Layer | Tooling | Repository policy |
| --- | --- | --- |
| Source and governance | Git, GitHub Actions, pre-commit | Track code, docs, configs, tests, paper |
| Python environment | `uv` preferred, pip fallback | Dependencies declared in `pyproject.toml` |
| Data/model versioning | DVC planned | Metadata may be tracked; payloads remain external |
| Configuration | Hydra planned | Track readable YAML configs |
| Experiment tracking | MLflow preferred; W&B optional | Track summaries, not credentials or local stores |
| Paper | LaTeX, BibTeX, documented table generator | Track source and small tables/figures |

## Storage Boundary

GitHub may contain source, configs, DVC metadata, protocols, claim registry, paper source, and
small documented summary tables. Raw datasets, generated outputs, checkpoints, MLflow stores,
credentials, and caches remain local or in approved remote storage.

Zenodo can later archive a tagged release, paper, source snapshot, documented summary tables, and
legally redistributable artifacts. It must not receive restricted data or credentials.
