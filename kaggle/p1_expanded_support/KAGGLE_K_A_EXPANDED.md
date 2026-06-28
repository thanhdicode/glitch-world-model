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
pip install -e ".[research,video]" -q
echo "=== OK ==="
```

## Cell 2 — Build dữ liệu mở rộng (chung, ~15-30 phút tải video)
```python
%%bash
cd /kaggle/working/glitch-world-model
python scripts/build_tempglitch_expanded_normal_inputs.py \
  --output-dir /kaggle/working/tempglitch_expanded \
  --limit-per-group 8 \
  --image-size 112 --frame-stride 1 --seed 42
```
> 5 category × 8 normal = tối đa 40 normal episode. Script in JSON báo
> `downloaded_normal_episodes` thực tế. Cần ≥30 (sau khi split, ~20% vào validation → có thể cần
> tăng `--limit-per-group` lên 10-12 nếu validation-normal chưa đủ; xem JSON `validation_normal`).
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
L=/kaggle/working/tempglitch_expanded/lance
python scripts/run_tempglitch_followup_pair_disjoint.py \
  --r5-output-dir /kaggle/working/r5_tempglitch_expanded \
  --train-lance $L/tempglitch_train_normal_all_local.lance \
  --validation-normal-lance $L/tempglitch_validation_normal_all_local.lance \
  --validation-buggy-lance $L/tempglitch_validation_buggy_all_local.lance \
  --output-dir /kaggle/working/tempglitch_followup_expanded
cat /kaggle/working/tempglitch_followup_expanded/followup_comparison.csv | head
```
> Nếu validator báo "support mismatch": đó là vì support mới khác tuple frozen (4,32,22,10).
> Báo lại con số support thực tế cho Computer — sẽ truyền `expected_support` đúng (code đã hỗ trợ).

## Cell 4 — Significance (chung)
```python
%%bash
cd /kaggle/working/glitch-world-model
python scripts/compute_significance_table.py \
  --lewm-scores /kaggle/working/tempglitch_followup_expanded/followup_episode_scores.csv \
  --baseline-scores /kaggle/working/tempglitch_followup_expanded/followup_episode_scores.csv \
  --group-key source --n-bootstrap 2000 --seed 42 \
  --output /kaggle/working/tempglitch_expanded_significance.json
cat /kaggle/working/tempglitch_expanded_significance.json
```

## Tải về
- `/kaggle/working/tempglitch_expanded/expanded_inputs_summary.json`
- toàn bộ `/kaggle/working/tempglitch_followup_expanded/`
- `/kaggle/working/tempglitch_expanded_significance.json`

## Acceptance
- validation-normal episodes ≥ 30 → CI hẹp hơn [0.535, 0.877] cũ.
- AUROC LeWM ≥ 0.70; nếu DeLong p<0.05 → "significantly outperforms".
- FPR@95TPR giảm so với 0.75 là tín hiệu tốt.
