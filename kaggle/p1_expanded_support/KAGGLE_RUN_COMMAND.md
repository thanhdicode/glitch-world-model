# P1 Kaggle Run Commands (K-A & K-B)

> Chạy trên Kaggle Notebook, GPU T4×2, internet OFF. Repo đã clone vào `/kaggle/working/glitch-world-model`
> (hoặc add repo as dataset). Nhớ workaround Lance: copy `.lance` sang `/tmp` trước khi đọc.

## Cell 0 — Setup chung

```bash
cd /kaggle/working/glitch-world-model
pip install -e ".[research]" -q
# Workaround Kaggle Lance read bug: copy lance inputs to /tmp
python - <<'PY'
import shutil, pathlib
src = pathlib.Path("/kaggle/input")
dst = pathlib.Path("/tmp/lance"); dst.mkdir(parents=True, exist_ok=True)
for p in src.rglob("*.lance"):
    target = dst / p.name
    if not target.exists():
        shutil.copytree(p, target)
        print("copied", p, "->", target)
PY
```

---

## K-A bước 1 — Re-score R5 TempGlitch với support mở rộng

Mục tiêu: tạo lại R5 output dir nhưng với NHIỀU normal-negative episodes hơn (target 30–50)
và calibration 4–6 episodes. Dùng runner R5 hiện có; chỉ tăng số episode normal đưa vào.

```bash
cd /kaggle/working/glitch-world-model
python scripts/run_r5_tempglitch_identical_episode_evaluation.py \
  --checkpoint /kaggle/input/lewm-weights/seed44/best_weights.pt \
  --config /kaggle/input/lewm-weights/seed44/config.json \
  --train-lance /tmp/lance/tempglitch_train_normal_all_local.lance \
  --validation-normal-lance /tmp/lance/tempglitch_validation_normal_all_local.lance \
  --validation-buggy-lance /tmp/lance/tempglitch_validation_buggy_all_local.lance \
  --max-eval-normals all \
  --device cuda \
  --output-dir /kaggle/working/r5_tempglitch_expanded
```

> Nếu runner chưa có cờ `--max-eval-normals`: nó vẫn chạy với toàn bộ normal episodes khả dụng
> trong validation-normal Lance. Ghi lại số normal-negative thực tế nó in ra (cần > 12 để có ý nghĩa).

## K-A bước 2 — Follow-up + significance trên support mở rộng

```bash
cd /kaggle/working/glitch-world-model
# Chạy follow-up với support mới (truyền expected_support qua biến môi trường nếu cần).
python scripts/run_tempglitch_followup_pair_disjoint.py \
  --r5-output-dir /kaggle/working/r5_tempglitch_expanded \
  --train-lance /tmp/lance/tempglitch_train_normal_all_local.lance \
  --validation-normal-lance /tmp/lance/tempglitch_validation_normal_all_local.lance \
  --validation-buggy-lance /tmp/lance/tempglitch_validation_buggy_all_local.lance \
  --output-dir /kaggle/working/tempglitch_followup_expanded

# Tính DeLong + paired-bootstrap ngay (LeWM tốt nhất vs baseline mạnh nhất).
# Tạo 2 file CSV episode-level: cột source,score,label cho LeWM và cho baseline.
python scripts/compute_significance_table.py \
  --lewm-scores /kaggle/working/tempglitch_followup_expanded/lewm_episode_scores.csv \
  --baseline-scores /kaggle/working/tempglitch_followup_expanded/feature_distance_episode_scores.csv \
  --group-key source --n-bootstrap 2000 --seed 42 \
  --method-label "LeWM" --baseline-label "feature\\_distance" \
  --output /kaggle/working/tempglitch_significance.json
```

**Acceptance K-A:**
- normal-negative evaluation episodes ≥ 30 (mục tiêu)
- AUROC LeWM giữ ~0.70–0.78
- ΔAUROC 95% CI **không chứa 0** HOẶC DeLong p < 0.05 → được nâng wording lên "significantly outperforms".
  Nếu chưa đạt → giữ "stronger observed separation" (vẫn hợp lệ).

---

## K-B — R5-XGame 3 seed + significance (củng cố 0.9097)

```bash
cd /kaggle/working/glitch-world-model
python scripts/run_r5_xgame_comparison.py \
  --input-root /kaggle/input \
  --output-dir /kaggle/working/r5_xgame_full \
  --seeds 42 43 44 \
  --device cuda

# Significance: LeWM tốt nhất vs feature_distance trên cùng 72 episode (12 neg + 60 pos)
python scripts/compute_significance_table.py \
  --lewm-scores /kaggle/working/r5_xgame_full/lewm_best_episode_scores.csv \
  --baseline-scores /kaggle/working/r5_xgame_full/feature_distance_episode_scores.csv \
  --group-key source --n-bootstrap 2000 --seed 42 \
  --method-label "LeWM" --baseline-label "feature\\_distance" \
  --output /kaggle/working/r5_xgame_significance.json
```

**Acceptance K-B:**
- 3 seed hoàn tất, AUROC mean ± std báo cáo được
- LeWM AUROC ~0.90 với CI tách rời baseline → **claim significant superiority hợp pháp trên XGame**
  (đây là kết quả "đẹp" mạnh nhất của paper).

---

## Quy tắc dừng (bắt buộc)
Dừng ngay nếu:
- CUDA không khả dụng
- thiếu Lance input hoặc hash không khớp
- `_role_overlap` > 0 (rò rỉ giữa calibration và evaluation)
- bất kỳ flag locked-test nào = true
