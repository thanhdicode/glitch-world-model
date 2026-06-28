# K-A Aggressive Topic A Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make K-A genuinely expanded-support and Kaggle-ready while K-B runs, so the Topic A paper can report stronger TempGlitch and R5-XGame evidence without weakening locked-test or claim discipline.

**Architecture:** Keep the historical TempGlitch follow-up defaults unchanged, then add opt-in expanded-support controls around them. The builder will target actual validation support, the follow-up runner will accept explicit support/calibration parameters, and the runbooks/paper TODOs will stop implying locked-test evidence.

**Tech Stack:** Python CLI scripts, pytest, ruff, TempGlitch Lance materialization, repository research validators, LaTeX paper docs.

---

## File Structure

- Modify: `scripts/build_tempglitch_expanded_normal_inputs.py`
  - Add support-count helpers.
  - Add target validation-normal/buggy CLI controls.
  - Fail closed when expanded support is below target unless explicitly allowed.
  - Include actual split support in `expanded_inputs_summary.json`.

- Modify: `tests/test_build_tempglitch_expanded_normal_inputs.py`
  - Add a deterministic split-support test showing `limit_per_group=8` is insufficient.
  - Add a parser/default test for the new K-A target controls.
  - Add a helper-level fail-closed test that does not download videos.

- Modify: `src/glitch_detection/tempglitch_followup.py`
  - Thread explicit calibration IDs and expected support through `run_tempglitch_followup_pair_disjoint`.
  - Preserve default frozen support and default calibration episode IDs.
  - Write expanded support expectations into provenance.

- Modify: `scripts/run_tempglitch_followup_pair_disjoint.py`
  - Expose `--calibration-episode-id`, `--expected-evaluation-normal-count`, `--expected-evaluation-buggy-count`, and `--expected-support`.
  - Parse support tuples safely.

- Modify: `tests/test_tempglitch_followup.py`
  - Add a test proving `run_tempglitch_followup_pair_disjoint` can pass expanded support parameters into manifest/episode validation without changing historical defaults.
  - Add a parser/parse-support test for the CLI.

- Modify: `kaggle/p1_expanded_support/KAGGLE_K_A_EXPANDED.md`
  - Replace the incorrect `--limit-per-group 8/10/12` guidance.
  - Make `--target-validation-normal-count 34` the acceptance target.
  - Document that five categories need roughly `--limit-per-group 35` under the current 20% validation split to preserve at least 30 normal-negative evaluation episodes after calibration.

- Modify: `paper/sections/08_results.tex`
  - Replace locked-test TODO comments with non-locked K-A/K-B TODO comments.
  - Keep final wording conservative until validated outputs arrive.

## Task 1: Builder Support Accounting

**Files:**
- Modify: `scripts/build_tempglitch_expanded_normal_inputs.py`
- Test: `tests/test_build_tempglitch_expanded_normal_inputs.py`

- [ ] **Step 1: Add failing tests for support counting and target defaults**

Add tests that exercise helper logic without network or Lance materialization:

```python
def _paired_rows(categories: list[str], limit_per_group: int) -> list[dict[str, str]]:
    rows = []
    for category in categories:
        for index in range(limit_per_group):
            pair_id = f"{category}/pair-{index:03d}"
            rows.append(
                {
                    "source": f"{category}_Normal_{index}",
                    "episode_id": f"{category}_Normal_{index}",
                    "pair_id": pair_id,
                    "category": category,
                    "label": "Normal",
                }
            )
            rows.append(
                {
                    "source": f"{category}_Buggy_{index}",
                    "episode_id": f"{category}_Buggy_{index}",
                    "pair_id": pair_id,
                    "category": category,
                    "label": "Buggy",
                }
            )
    return rows


def test_split_support_counts_show_limit_8_is_not_expanded_enough():
    records = mod.freeze_tempglitch_split(
        _paired_rows(["Blinking", "Frozen", "Shooting", "Teleportation", "Physics"], 8),
        exposed_groups=set(),
        seed=42,
    )
    support = mod._split_support_counts(records)
    assert support["validation_normal_episode_count"] == 10
    assert support["validation_buggy_episode_count"] == 10


def test_split_support_counts_reaches_target_at_limit_30():
    records = mod.freeze_tempglitch_split(
        _paired_rows(["Blinking", "Frozen", "Shooting", "Teleportation", "Physics"], 30),
        exposed_groups=set(),
        seed=42,
    )
    support = mod._split_support_counts(records)
    assert support["validation_normal_episode_count"] == 30
    assert support["validation_buggy_episode_count"] == 30
```

- [ ] **Step 2: Run the new tests and confirm they fail**

Run:

```powershell
python -m pytest tests/test_build_tempglitch_expanded_normal_inputs.py -q
```

Expected: fail because `_split_support_counts` does not exist yet.

- [ ] **Step 3: Implement support-count helper**

Add this helper near `_build_split_rows`:

```python
def _split_support_counts(records: list[object]) -> dict[str, int]:
    train_normal = {
        record.episode_id
        for record in records
        if record.split == "train" and record.label == "Normal"
    }
    validation_normal = {
        record.episode_id
        for record in records
        if record.split == "validation" and record.label == "Normal"
    }
    validation_buggy = {
        record.episode_id
        for record in records
        if record.split == "validation" and record.label == "Buggy"
    }
    test_normal = {
        record.episode_id
        for record in records
        if record.split == "test" and record.label == "Normal"
    }
    test_buggy = {
        record.episode_id
        for record in records
        if record.split == "test" and record.label == "Buggy"
    }
    return {
        "train_normal_episode_count": len(train_normal),
        "validation_normal_episode_count": len(validation_normal),
        "validation_buggy_episode_count": len(validation_buggy),
        "test_normal_episode_count": len(test_normal),
        "test_buggy_episode_count": len(test_buggy),
    }
```

- [ ] **Step 4: Verify support-count tests pass**

Run:

```powershell
python -m pytest tests/test_build_tempglitch_expanded_normal_inputs.py -q
```

Expected: pass.

## Task 2: Builder Target Controls

**Files:**
- Modify: `scripts/build_tempglitch_expanded_normal_inputs.py`
- Test: `tests/test_build_tempglitch_expanded_normal_inputs.py`

- [ ] **Step 1: Add parser/default tests**

Update `test_build_parser_defaults`:

```python
def test_build_parser_defaults():
    parser = mod.build_parser()
    args = parser.parse_args(["--output-dir", "/tmp/x"])
    assert args.limit_per_group == 30
    assert args.target_validation_normal_count == 30
    assert args.target_validation_buggy_count == 30
    assert not args.allow_under_target_support
    assert args.image_size == 112
    assert args.frame_stride == 1
```

Add a target failure test:

```python
def test_raise_if_under_target_support_blocks_weak_expanded_split():
    support = {
        "validation_normal_episode_count": 10,
        "validation_buggy_episode_count": 10,
    }
    with pytest.raises(ValueError, match="below K-A target support"):
        mod._raise_if_under_target_support(
            support,
            target_validation_normal_count=30,
            target_validation_buggy_count=30,
            allow_under_target_support=False,
        )
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```powershell
python -m pytest tests/test_build_tempglitch_expanded_normal_inputs.py -q
```

Expected: fail because parser defaults and helper are not implemented.

- [ ] **Step 3: Implement fail-closed target helper and CLI defaults**

Add helper:

```python
def _raise_if_under_target_support(
    support: dict[str, int],
    *,
    target_validation_normal_count: int,
    target_validation_buggy_count: int,
    allow_under_target_support: bool,
) -> None:
    if allow_under_target_support:
        return
    actual_normal = support["validation_normal_episode_count"]
    actual_buggy = support["validation_buggy_episode_count"]
    if (
        actual_normal < target_validation_normal_count
        or actual_buggy < target_validation_buggy_count
    ):
        raise ValueError(
            "Expanded TempGlitch split is below K-A target support: "
            f"validation_normal={actual_normal}/{target_validation_normal_count}, "
            f"validation_buggy={actual_buggy}/{target_validation_buggy_count}. "
            "Increase --limit-per-group or pass --allow-under-target-support only "
            "when documenting maximum public support."
        )
```

Change `build_expanded_inputs` signature:

```python
def build_expanded_inputs(
    *,
    output_dir: Path,
    limit_per_group: int,
    categories: list[str] | None = None,
    image_size: int = 112,
    frame_stride: int = 1,
    seed: int = 42,
    target_validation_normal_count: int = 30,
    target_validation_buggy_count: int = 30,
    allow_under_target_support: bool = False,
) -> dict[str, object]:
```

Change parser defaults:

```python
parser.add_argument(
    "--limit-per-group",
    type=int,
    default=30,
    help="Videos per (category, label) group. With five categories and the default 20%% validation split, 35 targets about 35 validation normals.",
)
parser.add_argument("--target-validation-normal-count", type=int, default=34)
parser.add_argument("--target-validation-buggy-count", type=int, default=34)
parser.add_argument("--allow-under-target-support", action="store_true")
```

After `records = freeze_tempglitch_split(...)`, compute support, enforce targets, and write it into provenance and summary:

```python
support = _split_support_counts(records)
_raise_if_under_target_support(
    support,
    target_validation_normal_count=target_validation_normal_count,
    target_validation_buggy_count=target_validation_buggy_count,
    allow_under_target_support=allow_under_target_support,
)
```

Add to provenance and summary:

```python
"target_validation_normal_count": target_validation_normal_count,
"target_validation_buggy_count": target_validation_buggy_count,
"allow_under_target_support": allow_under_target_support,
"split_support": support,
```

Thread CLI args into `build_expanded_inputs`.

- [ ] **Step 4: Verify builder tests**

Run:

```powershell
python -m pytest tests/test_build_tempglitch_expanded_normal_inputs.py -q
```

Expected: pass.

## Task 3: Follow-Up Parameter Threading

**Files:**
- Modify: `src/glitch_detection/tempglitch_followup.py`
- Test: `tests/test_tempglitch_followup.py`

- [ ] **Step 1: Add unit test for expanded support validation path**

Add a direct test around existing helpers:

```python
def test_followup_helpers_accept_expanded_support_parameters():
    rows = [
        _manifest_row("w1", "cal-1", "pair/cal-1", "Normal", "evaluation"),
        _manifest_row("w2", "cal-2", "pair/cal-2", "Normal", "evaluation"),
        _manifest_row("w3", "eval-normal-1", "pair/eval-normal-1", "Normal", "evaluation"),
        _manifest_row("w4", "eval-normal-2", "pair/eval-normal-2", "Normal", "evaluation"),
        _manifest_row("w5", "eval-buggy-1", "pair/eval-buggy-1", "Buggy", "evaluation"),
        _manifest_row("w6", "eval-buggy-2", "pair/eval-buggy-2", "Buggy", "evaluation"),
    ]
    followup_rows = build_followup_manifest_rows(
        rows,
        calibration_episode_ids=("cal-1", "cal-2"),
        expected_evaluation_normal_count=2,
        expected_evaluation_buggy_count=2,
    )
    summary = validate_followup_manifest_rows(
        followup_rows,
        calibration_episode_ids=("cal-1", "cal-2"),
        expected_evaluation_normal_count=2,
        expected_evaluation_buggy_count=2,
    )
    assert summary["calibration_episode_count"] == 2
    assert summary["evaluation_normal_episode_count"] == 2
    assert summary["evaluation_buggy_episode_count"] == 2
```

- [ ] **Step 2: Run tests**

Run:

```powershell
python -m pytest tests/test_tempglitch_followup.py -q
```

Expected: this may already pass for helper-level expanded support. If it passes, continue to function threading.

- [ ] **Step 3: Thread parameters through `run_tempglitch_followup_pair_disjoint`**

Change signature:

```python
def run_tempglitch_followup_pair_disjoint(
    *,
    r5_output_dir: Path,
    train_lance: Path,
    validation_normal_lance: Path,
    validation_buggy_lance: Path,
    output_dir: Path,
    bootstrap_seed: int = 42,
    n_bootstrap: int = 1000,
    command_text: str,
    calibration_episode_ids: tuple[str, ...] = CALIBRATION_NORMAL_EPISODE_IDS,
    expected_evaluation_normal_count: int = EXPECTED_EVALUATION_NORMAL_COUNT,
    expected_evaluation_buggy_count: int = EXPECTED_EVALUATION_BUGGY_COUNT,
) -> dict[str, Any]:
```

Pass these values into `build_followup_manifest_rows`, `validate_followup_manifest_rows`,
`build_followup_episode_rows`, and `validate_followup_episode_rows`.

Add to metrics/provenance payloads:

```python
"calibration_episode_ids": list(calibration_episode_ids),
"expected_evaluation_normal_count": expected_evaluation_normal_count,
"expected_evaluation_buggy_count": expected_evaluation_buggy_count,
```

- [ ] **Step 4: Verify follow-up tests**

Run:

```powershell
python -m pytest tests/test_tempglitch_followup.py -q
```

Expected: pass.

## Task 4: Follow-Up CLI Controls

**Files:**
- Modify: `scripts/run_tempglitch_followup_pair_disjoint.py`
- Test: `tests/test_tempglitch_followup.py`

- [ ] **Step 1: Add parser helpers**

Add to `scripts/run_tempglitch_followup_pair_disjoint.py`:

```python
def parse_expected_support(value: str) -> tuple[str, str, str, str]:
    parts = tuple(part.strip() for part in value.split(","))
    if len(parts) != 4 or any(not part.isdigit() for part in parts):
        raise argparse.ArgumentTypeError(
            "expected support must be four comma-separated integers: calibration,evaluation,positive,negative"
        )
    return parts
```

Add arguments:

```python
parser.add_argument(
    "--calibration-episode-id",
    action="append",
    default=None,
    help="Calibration normal episode ID. Repeat for expanded K-A; defaults to frozen follow-up IDs.",
)
parser.add_argument("--expected-evaluation-normal-count", type=int, default=10)
parser.add_argument("--expected-evaluation-buggy-count", type=int, default=22)
parser.add_argument("--expected-support", type=parse_expected_support, default=None)
```

In `main`, derive:

```python
calibration_episode_ids = (
    tuple(args.calibration_episode_id)
    if args.calibration_episode_id
    else CALIBRATION_NORMAL_EPISODE_IDS
)
```

Pass IDs and counts to `run_tempglitch_followup_pair_disjoint`. If `expected_support` is used only for output validation later, include it in command provenance and runbook; do not silently validate wrong support here unless the validator is called by the script.

- [ ] **Step 2: Add parser tests**

Import the script module in `tests/test_tempglitch_followup.py` and assert:

```python
import scripts.run_tempglitch_followup_pair_disjoint as followup_cli


def test_parse_expected_support_accepts_four_counts():
    assert followup_cli.parse_expected_support("2,60,30,30") == ("2", "60", "30", "30")


def test_parse_expected_support_rejects_bad_shape():
    with pytest.raises(Exception):
        followup_cli.parse_expected_support("2,60,30")
```

- [ ] **Step 3: Run parser tests**

Run:

```powershell
python -m pytest tests/test_tempglitch_followup.py -q
```

Expected: pass.

## Task 5: Runbook And Paper Safety Text

**Files:**
- Modify: `kaggle/p1_expanded_support/KAGGLE_K_A_EXPANDED.md`
- Modify: `paper/sections/08_results.tex`

- [ ] **Step 1: Update K-A runbook command**

Replace builder command guidance with:

```powershell
python scripts/build_tempglitch_expanded_normal_inputs.py `
  --output-dir /kaggle/working/tempglitch_expanded `
  --limit-per-group 35 `
  --target-validation-normal-count 34 `
  --target-validation-buggy-count 34 `
  --image-size 112 `
  --frame-stride 1
```

Add note:

```markdown
With five categories and the current `validation_ratio=0.2`, `--limit-per-group 8`,
`10`, or `12` is not expanded enough for K-A. Use `35` first so four calibration
normals still leave at least 30 normal-negative evaluation episodes; increase only if
the downloaded public support is uneven across categories.
```

- [ ] **Step 2: Update follow-up command guidance**

Add explicit support guidance:

```markdown
After R5 scoring, read `expanded_inputs_summary.json` and use the actual support counts
when validating follow-up outputs. For the target K-A run, expected support should be
`calibration_count, evaluation_count, positive_count, negative_count`, where
`evaluation_count = positive_count + negative_count`.
```

- [ ] **Step 3: Remove locked-test TODO hazards from results**

Change comments in `paper/sections/08_results.tex` from locked-test wording to:

```tex
% TODO-KA: insert validated non-locked expanded TempGlitch K-A AUROC, AUPRC, CI, and support here.
% TODO-KB: insert validated non-locked R5-XGame K-B DeLong/significance wording here.
```

- [ ] **Step 4: Confirm no K-A/K-B locked-test TODO remains**

Run:

```powershell
rg -n "TODO-KA|TODO-KB|locked-test R5-XGame|R5-XGame locked-test" paper kaggle/p1_expanded_support
```

Expected: TODOs may remain, but none should say locked-test R5-XGame.

## Task 6: Focused Verification

**Files:**
- No edits unless verification reveals a bug.

- [ ] **Step 1: Run focused pytest**

Run:

```powershell
python -m pytest tests/test_build_tempglitch_expanded_normal_inputs.py tests/test_tempglitch_followup.py tests/test_compute_significance_table.py
```

Expected: pass.

- [ ] **Step 2: Run focused ruff**

Run:

```powershell
python -m ruff check scripts/build_tempglitch_expanded_normal_inputs.py scripts/run_tempglitch_followup_pair_disjoint.py src/glitch_detection/tempglitch_followup.py tests/test_build_tempglitch_expanded_normal_inputs.py tests/test_tempglitch_followup.py
python -m ruff format --check scripts/build_tempglitch_expanded_normal_inputs.py scripts/run_tempglitch_followup_pair_disjoint.py src/glitch_detection/tempglitch_followup.py tests/test_build_tempglitch_expanded_normal_inputs.py tests/test_tempglitch_followup.py
```

Expected: pass.

- [ ] **Step 3: Record remaining heavy verification**

If focused checks pass, defer the full `AGENTS.md` command suite until after K-B/K-A outputs are available and paper tables are regenerated.
