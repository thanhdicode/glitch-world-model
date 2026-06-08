# Windows PowerShell Commands

Use these commands when `make` is not available on Windows.

## Install

```powershell
python -m pip install -e ".[dev]"
```

## Install research extras

```powershell
python -m pip install -e ".[dev,research]"
```

## Lint

```powershell
python -m ruff check .
```

## Format

```powershell
python -m ruff format .
```

## Format check

```powershell
python -m ruff format --check .
```

## Tests

```powershell
python -m pytest
```

## Tests with coverage

```powershell
python -m pytest --cov=glitch_detection --cov-report=term-missing
```

## Synthetic demo

```powershell
python scripts\run_synthetic_demo.py
```

## Phase 0 check

```powershell
python scripts\run_synthetic_demo.py
python -m pytest
```

## Doctor

```powershell
python scripts\doctor.py
```
