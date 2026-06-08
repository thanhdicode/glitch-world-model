# Research Tooling Stack

| Tool | Purpose | Install status | When to use | Risk | Why not always installed | Command examples |
| --- | --- | --- | --- | --- | --- | --- |
| uv | Fast Python package and environment management | Documented only | Later if dependency resolution becomes slow | Another tool to teach contributors | pip is enough for current MVP | `uv pip install -e ".[dev]"` |
| ruff | Linting and formatting | Dev extra | Every code change and CI | May report style issues in old code | Lightweight enough for dev | `python -m ruff check .` |
| pre-commit | Local commit hygiene | Dev extra and config | Before commits | First run downloads hook envs | Optional local workflow | `python -m pre_commit run --all-files` |
| pytest / pytest-cov | Tests and coverage visibility | Dev extra | Every code change and CI | Coverage can be low early | No fail-under threshold yet | `python -m pytest --cov=glitch_detection --cov-report=term-missing` |
| GitHub Actions | CI on push/PR | Scaffolded | Remote validation | CI can fail on platform differences | Runs only on GitHub | See `.github/workflows/ci.yml` |
| DVC | Dataset and pipeline reproducibility | Optional `data` extra | Later, after dataset license/source are verified | Can accidentally track large data if misused | Should not manage raw data until Phase 2 | `python -m pip install -e ".[data]"` |
| MLflow | Local experiment tracking | Optional `tracking` extra | Later, for repeated experiments | Can create noisy `mlruns/` output | Not needed for Phase 0 | `mlflow ui` |
| Hydra/OmegaConf | Structured experiment configs | Optional `config` extra | Later, if CLI flags become unwieldy | Can overcomplicate simple scripts | Current CLIs are adequate | `python -m pip install -e ".[config]"` |
| decord | Video decoding | Optional `video` extra | Later, for larger video datasets | Platform-specific wheels | Pillow frame folders are enough now | `python -m pip install -e ".[video]"` |
| Hugging Face Datasets | Dataset access | Optional `data` extra | Later, for public dataset loaders | Downloads data if used | No dataset downloads in Phase 0 | `python -m pip install -e ".[data]"` |
| nbstripout | Notebook output stripping | Documented only | Add if notebooks appear | Extra hook dependency | No notebooks currently tracked | `pre-commit` hook later |
| le-wm | Future model backbone | Submodule reference | Phase 5 or explicit LeWM task | Heavy model/checkpoint integration | Not part of MVP runtime | `git submodule update --init external/le-wm` |
| world-of-bugs | Game bug reference/data source | Submodule reference | Data audit phase | Unity/platform complexity | Not needed for core tests | `git submodule update --init external/world-of-bugs` |
| vjepa2 | Reference/future backbone | Documented only | Related work or future baseline | Heavy checkpoints | No integration in MVP | External reference |
| VideoMAE | Future video baseline | Documented only | Later baseline comparison | Heavy dependencies/checkpoints | Not needed for Phase 0 | External reference |
| TimeSformer | Future video baseline | Documented only | Later supervised baseline | Requires labeled clips | Not anomaly detector by default | External reference |

## Tooling policy

- Keep core install small: `numpy` and `Pillow`.
- Put research/video/tracking/data tools behind optional extras.
- Do not add PyTorch by default.
- Do not make DVC or MLflow mandatory for CI until the workflow is proven.
