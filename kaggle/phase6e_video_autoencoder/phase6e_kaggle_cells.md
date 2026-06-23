# Phase 6E Kaggle Cells

This is a launch-template note for the historical Phase 6E validation-only Conv3D autoencoder
path. It is not evidence of a new run.

## Cell 1 - Dry Run

Run the package entrypoint in dry-run mode before any live execution:

```powershell
python scripts/run_kaggle_video_autoencoder.py --dry-run
```

## Cell 2 - Dataset Metadata

Prepare the private Kaggle dataset metadata from `dataset-metadata.template.json` and upload only
the launch package inputs. Do not upload credentials, outputs, checkpoints, or locked-test data.

## Cell 3 - Live Validation-Only Launch

When a separate task explicitly authorizes the historical Phase 6E workflow, run
`run_kaggle_video_autoencoder.py` with the validation-only manifest/split inputs. Keep locked test
closed.

## Cell 4 - Download And Validate

Download the produced artifact bundle and validate it locally with the repository intake tooling.
Preserve the resulting summary JSON for the final locked-test safety check.

## Cell 5 - Locked-Test Safety Check

The downloaded summary must keep `test_scored` false:

```python
import json
from pathlib import Path

summary = json.loads(Path("phase6e_summary.json").read_text(encoding="utf-8"))
assert summary.get("test_scored") is False
```
