.PHONY: install install-research lint format format-check test test-cov synthetic phase0-check sync-github sync-github-dry

install:
	python -m pip install -e ".[dev]"

install-research:
	python -m pip install -e ".[dev,research]"

lint:
	python -m ruff check .

format:
	python -m ruff format .

format-check:
	python -m ruff format --check .

test:
	python -m pytest

test-cov:
	python -m pytest --cov=glitch_detection --cov-report=term-missing

synthetic:
	python scripts/run_synthetic_demo.py

phase0-check:
	python scripts/run_synthetic_demo.py
	python -m pytest

sync-github:
	bash scripts/sync_from_github.sh

sync-github-dry:
	bash scripts/sync_from_github.sh --dry-run
