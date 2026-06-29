# K-A — TempGlitch EXPANDED-support re-evaluation (notebook riêng)

> Mục tiêu: nâng normal-negative từ 12 → ≥30 để CI hẹp lại và có cơ hội đạt DeLong p<0.05.
> Cơ chế: tải thêm video TempGlitch (public, MIT) → build 3 Lance mới → re-score bằng checkpoint
> LeWM seed42/43/44 → follow-up → significance.

## ⚠️ Điều kiện tiên quyết (đọc kỹ)
K-A cần **checkpoint LeWM seed42/43/44 cho TempGlitch**. Theo provenance, các checkpoint này hiện
nằm **local** (chưa có slug Kaggle). Bạn có 2 lựa chọn:

- **Lựa chọn 1 (khuyến nghị):** Upload checkpoint seed42/43/44 hiện có lên 1 Kaggle dataset
  (vd `huynhdieuthanh/lewm-tempglitch-seeds`), mỗi seed 1 thư mục chứa `best_weights.pt` + `config.json`.
  → Sau đó chạy "Đường A" bên dưới (chỉ re-score, ~40-90 phút).
- **Lựa chọn 2 (nếu không có checkpoint):** Train lại 3 seed trên dữ liệu mở rộng ngay trên Kaggle
  → chạy "Đường B" (train + score, ~2-3h). Đường B tự cấp checkpoint nên không cần upload.

Cả hai đường đều cần **Internet ON** để tải video.

---

## Cell 1 — Clone + cài đặt (chung)
```python
%%bash
cd /kaggle/working
rm -rf glitch-world-model
git clone https://github.com/thanhdicode/glitch-world-model.git
cd glitch-world-model
git rev-parse --short HEAD
pip install -e ".[research,video]" -q
echo "=== OK ==="
```
> HEAD phải là `main` mới nhất đã push, không được là `c638076`. Nếu Kaggle vẫn hiện `c638076`,
> notebook đang dùng bản cache/branch cũ và phải `rm -rf /kaggle/working/glitch-world-model`
> rồi clone lại.

## Cell 2 — Build dữ liệu mở rộng (chung, ~15-30 phút tải video)
```python
%%bash
cd /kaggle/working/glitch-world-model
python scripts/build_tempglitch_expanded_normal_inputs.py \
  --output-dir /kaggle/working/tempglitch_expanded \
  --limit-per-group 50 \
  --target-validation-normal-count 44 \
  --target-validation-buggy-count 44 \
  --target-evaluation-normal-count 40 \
  --minimum-calibration-normal-count 4 \
  --image-size 112 --frame-stride 1 --seed 42
```
> Với 5 category và split hiện tại `validation_ratio=0.2`, `--limit-per-group 8`, `10`, hoặc `12`
> không đủ cho K-A expanded. Dùng `50` để ưu tiên ít nhất 4 calibration-normal và khoảng 40
> normal-negative evaluation episode. Xem `expanded_inputs_summary.json` → `split_support`.
> Nếu public support theo category không đều, tăng `--limit-per-group`; không hạ
> `--minimum-calibration-normal-count` xuống 1 nữa vì run trước cho thấy threshold từ 1 episode làm
> FPR@95TPR rất xấu.
> Đường dẫn 3 Lance nằm trong JSON output.

---

## === ĐƯỜNG A: đã có checkpoint (chỉ re-score) ===

### Cell A1 — Attach dataset checkpoint
Add Input: dataset chứa seed42/seed43/seed44 (mỗi thư mục có best_weights.pt + config.json).

### Cell A2 — Re-score R5 trên dữ liệu mở rộng
```python
%%bash
cd /kaggle/working/glitch-world-model
L=/kaggle/working/tempglitch_expanded/lance
python scripts/run_r5_tempglitch_identical_episode_evaluation.py \
  --train-lance $L/tempglitch_train_normal_all_local.lance \
  --validation-normal-lance $L/tempglitch_validation_normal_all_local.lance \
  --validation-buggy-lance $L/tempglitch_validation_buggy_all_local.lance \
  --seed-artifact-root /kaggle/input/<slug>/seed42 \
  --seed-artifact-root /kaggle/input/<slug>/seed43 \
  --seed-artifact-root /kaggle/input/<slug>/seed44 \
  --device cuda --batch-size 16 \
  --output-dir /kaggle/working/r5_tempglitch_expanded
```

---

## === ĐƯỜNG B: train lại 3 seed trên dữ liệu mở rộng ===

### Cell B1 — Train seed42/43/44 (mỗi seed ~30-45 phút trên T4)
```python
%%bash
cd /kaggle/working/glitch-world-model
L=/kaggle/working/tempglitch_expanded/lance
for SEED in 42 43 44; do
  echo "=== TRAIN seed $SEED ==="
  python scripts/run_kaggle_lewm.py \
    --train-dataset $L/tempglitch_train_normal_all_local.lance \
    --validation-dataset $L/tempglitch_validation_normal_all_local.lance \
    --output-root /kaggle/working/lewm_seeds/seed$SEED \
    --device cuda --image-size 112 --batch-size 4 --epochs 1 --seed $SEED \
    --predictor-depth 6 --sigreg-projections 128
done
```
### Cell B2 — Re-score dùng checkpoint vừa train
```python
%%bash
cd /kaggle/working/glitch-world-model
L=/kaggle/working/tempglitch_expanded/lance
python scripts/run_r5_tempglitch_identical_episode_evaluation.py \
  --train-lance $L/tempglitch_train_normal_all_local.lance \
  --validation-normal-lance $L/tempglitch_validation_normal_all_local.lance \
  --validation-buggy-lance $L/tempglitch_validation_buggy_all_local.lance \
  --seed-artifact-root /kaggle/working/lewm_seeds/seed42 \
  --seed-artifact-root /kaggle/working/lewm_seeds/seed43 \
  --seed-artifact-root /kaggle/working/lewm_seeds/seed44 \
  --device cuda --batch-size 16 \
  --output-dir /kaggle/working/r5_tempglitch_expanded
```

---

## Cell 3 — Follow-up trên support mở rộng (chung)
```python
%%bash
cd /kaggle/working/glitch-world-model
python - <<'PY'
import csv
import subprocess
import sys

manifest_path = "/kaggle/working/r5_tempglitch_expanded/r5_manifest.csv"
with open(manifest_path, newline="", encoding="utf-8-sig") as handle:
    rows = list(csv.DictReader(handle))

normal_by_category = {}
for row in rows:
    if row["label"].lower() != "normal":
        continue
    normal_by_category.setdefault(row.get("category", ""), set()).add(row["source_episode_id"])
normal_ids = sorted({episode_id for ids in normal_by_category.values() for episode_id in ids})
target_evaluation_normal_count = 40
preferred_calibration_count = 4
available_for_calibration = len(normal_ids) - target_evaluation_normal_count
if available_for_calibration < preferred_calibration_count:
    raise SystemExit(
        f"Need at least {target_evaluation_normal_count + preferred_calibration_count} "
        "validation-normal episodes; "
        f"found {len(normal_ids)}"
    )
calibration_ids = []
for category in sorted(normal_by_category):
    for episode_id in sorted(normal_by_category[category]):
        if episode_id not in calibration_ids:
            calibration_ids.append(episode_id)
            break
    if len(calibration_ids) == preferred_calibration_count:
        break
if len(calibration_ids) < preferred_calibration_count:
    for episode_id in normal_ids:
        if episode_id not in calibration_ids:
            calibration_ids.append(episode_id)
        if len(calibration_ids) == preferred_calibration_count:
            break
evaluation_normal_count = len(normal_ids) - len(calibration_ids)
evaluation_buggy_count = len(
    {
        row["source_episode_id"]
        for row in rows
        if row["label"].lower() == "buggy"
    }
)
expected_support = (
    f"{len(calibration_ids)},"
    f"{evaluation_normal_count + evaluation_buggy_count},"
    f"{evaluation_buggy_count},"
    f"{evaluation_normal_count}"
)

cmd = [
    sys.executable,
    "scripts/run_tempglitch_followup_pair_disjoint.py",
    "--r5-output-dir", "/kaggle/working/r5_tempglitch_expanded",
    "--train-lance", "/kaggle/working/tempglitch_expanded/lance/tempglitch_train_normal_all_local.lance",
    "--validation-normal-lance", "/kaggle/working/tempglitch_expanded/lance/tempglitch_validation_normal_all_local.lance",
    "--validation-buggy-lance", "/kaggle/working/tempglitch_expanded/lance/tempglitch_validation_buggy_all_local.lance",
    "--output-dir", "/kaggle/working/tempglitch_followup_expanded",
    "--expected-evaluation-normal-count", str(evaluation_normal_count),
    "--expected-evaluation-buggy-count", str(evaluation_buggy_count),
    "--expected-support", expected_support,
]
for episode_id in calibration_ids:
    cmd.extend(["--calibration-episode-id", episode_id])

print("Calibration IDs:", calibration_ids)
print("Expected support:", expected_support)
subprocess.run(cmd, check=True)
PY
cat /kaggle/working/tempglitch_followup_expanded/followup_comparison.csv | head
```
> Cell này lấy calibration IDs và support tuple trực tiếp từ `r5_manifest.csv`, nên không còn phải
> sửa tay tuple frozen `(4,32,22,10)`. Acceptance target: `calibration_count >= 4`,
> `evaluation_normal_count >= 40`, `evaluation_buggy_count >= 40`, role overlap = 0,
> locked-test flags = false.

## Cell 4 — Significance (chung)
```python
%%bash
set -euo pipefail
cd /kaggle/working/glitch-world-model
python - <<'PY'
import csv
import json
import subprocess
import sys
from pathlib import Path

comparison = Path("/kaggle/working/tempglitch_followup_expanded/followup_comparison.csv")
scores = Path("/kaggle/working/tempglitch_followup_expanded/followup_episode_scores.csv")
rows = list(csv.DictReader(comparison.open(newline="", encoding="utf-8-sig")))
best_lewm = max(
    (r for r in rows if r["method_family"] == "lewm"),
    key=lambda r: (float(r["auroc"]), float(r["auprc"]), float(r["f1"])),
)
best_baseline = max(
    (r for r in rows if r["method_family"] == "baseline"),
    key=lambda r: (float(r["auroc"]), float(r["auprc"]), float(r["f1"])),
)
selection = {
    "best_lewm": best_lewm,
    "best_baseline": best_baseline,
}
Path("/kaggle/working/tempglitch_significance_selection.json").write_text(
    json.dumps(selection, indent=2) + "\n",
    encoding="utf-8",
)
cmd = [
    sys.executable,
    "scripts/compute_significance_table.py",
    "--lewm-scores", str(scores),
    "--baseline-scores", str(scores),
    "--group-key", "source",
    "--n-bootstrap", "2000",
    "--seed", "42",
    "--method-label", "LeWM",
    "--baseline-label", best_baseline["method"],
    "--lewm-method-family", "lewm",
    "--lewm-window-scorer", best_lewm["window_scorer"],
    "--lewm-seed", best_lewm["seed"],
    "--lewm-episode-aggregation", best_lewm["episode_aggregation"],
    "--baseline-method-family", "baseline",
    "--baseline-method", best_baseline["method"],
    "--baseline-episode-aggregation", best_baseline["episode_aggregation"],
    "--output", "/kaggle/working/tempglitch_expanded_significance.json",
]
print("Selected LeWM:", best_lewm)
print("Selected baseline:", best_baseline)
subprocess.run(cmd, check=True)
PY
cat /kaggle/working/tempglitch_expanded_significance.json
```

## Tải về
- `/kaggle/working/tempglitch_expanded/expanded_inputs_summary.json`
- toàn bộ `/kaggle/working/tempglitch_followup_expanded/`
- `/kaggle/working/tempglitch_expanded_significance.json`
- `/kaggle/working/tempglitch_significance_selection.json`

## Acceptance
- calibration normals ≥ 4 và normal-negative evaluation episodes ≥ 40.
- AUROC LeWM ≥ 0.70; nếu DeLong p<0.05 và bootstrap ΔAUROC CI loại 0 → "significantly
  outperforms".
- FPR@95TPR phải giảm rõ so với run calibration=1; nếu vẫn gần 1.0 thì chỉ dùng K-A như bounded
  auxiliary/diagnostic evidence, không làm headline.
