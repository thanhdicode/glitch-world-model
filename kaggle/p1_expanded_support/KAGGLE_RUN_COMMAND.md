# P1 Kaggle Run Commands (K-A & K-B) — KHỚP VỚI CLI THẬT

> GPU T4×2. K-A và K-B là HAI notebook riêng (chạy song song được).
> K-B tự cài runtime cô lập trong script; K-A dùng checkpoint LeWM đã có.

================================================================
## K-B — R5-XGame 3 seed (notebook #1, chạy trước/song song)
================================================================

### Input dataset cần attach (Kaggle UI → Add Input):
- `benedictwilkinsai/world-of-bugs-normal`
- `benedictwilkinsai/world-of-bugs-test`
- (KHÔNG attach R5-WOB cũ / checkpoint / locked-test — script sẽ từ chối)

### Cell 1 — clone repo (branch P1):
```bash
cd /kaggle/working
rm -rf glitch-world-model
git clone --branch codex/p1-expanded-support-significance \
  https://github.com/thanhdicode/glitch-world-model.git
```

### Cell 2 — chạy staged pipeline (tự cài runtime + train 3 seed + score + đóng gói):
```bash
cd /kaggle/working/glitch-world-model
bash cloud/wob_r5_xgame/run_kaggle_r5_xgame_staged.sh
```

### Cell 3 — significance (sau khi Cell 2 xong):
```bash
cd /kaggle/working/glitch-world-model
# Bundle nằm trong /kaggle/working/r5_xgame/. Giải nén để lấy episode scores:
tar -xzf /kaggle/working/r5_xgame/r5_xgame_outputs.tar.gz -C /kaggle/working/r5_xgame_extracted
ls -R /kaggle/working/r5_xgame_extracted | head -40   # tìm 2 file *_episode_scores.csv
# Sau khi biết tên file thật, chạy:
python scripts/compute_significance_table.py \
  --lewm-scores /kaggle/working/r5_xgame_extracted/<LEWM_episode_scores.csv> \
  --baseline-scores /kaggle/working/r5_xgame_extracted/<feature_distance_episode_scores.csv> \
  --group-key source --n-bootstrap 2000 --seed 42 \
  --method-label "LeWM" --baseline-label "feature\\_distance" \
  --output /kaggle/working/r5_xgame_significance.json
```

### Tải về sau khi xong:
- `/kaggle/working/r5_xgame/r5_xgame_outputs.tar.gz`
- `/kaggle/working/r5_xgame/r5_xgame_outputs.tar.gz.sha256`
- `/kaggle/working/r5_xgame_staged.log`
- `/kaggle/working/r5_xgame_significance.json`

================================================================
## K-A — TempGlitch re-score + follow-up (notebook #2, song song)
================================================================

### Input dataset cần attach:
- Dataset chứa checkpoint LeWM seed42/43/44 (cùng cái bạn đã dùng cho run TempGlitch trước —
  thường là `<bạn>/lewm-tempglitch-weights` hoặc seed-artifact roots).
- Dataset chứa 3 Lance: `tempglitch_train_normal_all_local.lance`,
  `tempglitch_validation_normal_all_local.lance`, `tempglitch_validation_buggy_all_local.lance`.

> "Mở rộng support" = trỏ `--validation-normal-lance` vào Lance có NHIỀU normal episode hơn.
> Script tự dùng TẤT CẢ normal episode có trong Lance đó (không có cờ riêng). Nếu Lance hiện tại
> chỉ có 12-14 normal, cần build Lance normal lớn hơn từ 750 pairs trước (xem GHI CHÚ cuối file).

### Cell 1 — clone + cài + workaround Lance:
```bash
cd /kaggle/working
rm -rf glitch-world-model
git clone --branch codex/p1-expanded-support-significance \
  https://github.com/thanhdicode/glitch-world-model.git
cd glitch-world-model
pip install -e ".[research]" -q
# copy lance sang /tmp (tránh lỗi đọc Lance trên Kaggle)
python - <<'PY'
import shutil, pathlib
dst = pathlib.Path("/tmp/lance"); dst.mkdir(parents=True, exist_ok=True)
for p in pathlib.Path("/kaggle/input").rglob("*.lance"):
    t = dst / p.name
    if not t.exists():
        shutil.copytree(p, t); print("copied", p.name)
PY
```

### Cell 2 — re-score R5 TempGlitch (CLI THẬT — dùng --seed-artifact-root):
```bash
cd /kaggle/working/glitch-world-model
python scripts/run_r5_tempglitch_identical_episode_evaluation.py \
  --train-lance /tmp/lance/tempglitch_train_normal_all_local.lance \
  --validation-normal-lance /tmp/lance/tempglitch_validation_normal_all_local.lance \
  --validation-buggy-lance /tmp/lance/tempglitch_validation_buggy_all_local.lance \
  --seed-artifact-root /kaggle/input/<lewm-weights>/seed42 \
  --seed-artifact-root /kaggle/input/<lewm-weights>/seed43 \
  --seed-artifact-root /kaggle/input/<lewm-weights>/seed44 \
  --device cuda --batch-size 16 \
  --output-dir /kaggle/working/r5_tempglitch_expanded
```
> Mẹo: chạy thử với `--dry-run` trước để in kế hoạch + xác nhận seed artifacts hợp lệ, rồi bỏ `--dry-run`.

### Cell 3 — follow-up trên support mở rộng:
```bash
cd /kaggle/working/glitch-world-model
python scripts/run_tempglitch_followup_pair_disjoint.py \
  --r5-output-dir /kaggle/working/r5_tempglitch_expanded \
  --train-lance /tmp/lance/tempglitch_train_normal_all_local.lance \
  --validation-normal-lance /tmp/lance/tempglitch_validation_normal_all_local.lance \
  --validation-buggy-lance /tmp/lance/tempglitch_validation_buggy_all_local.lance \
  --output-dir /kaggle/working/tempglitch_followup_expanded
```

### Cell 4 — significance:
```bash
cd /kaggle/working/glitch-world-model
ls /kaggle/working/tempglitch_followup_expanded   # tìm file episode scores
python scripts/compute_significance_table.py \
  --lewm-scores /kaggle/working/tempglitch_followup_expanded/followup_episode_scores.csv \
  --baseline-scores /kaggle/working/tempglitch_followup_expanded/followup_episode_scores.csv \
  --group-key source --n-bootstrap 2000 --seed 42 \
  --output /kaggle/working/tempglitch_significance.json
```
> LƯU Ý: `followup_episode_scores.csv` chứa CẢ LeWM lẫn baseline trong 1 file (cột method_family).
> Computer sẽ tách 2 nhóm khi ingest; bạn chỉ cần tải nguyên file về là đủ.

### Tải về:
- toàn bộ thư mục `/kaggle/working/tempglitch_followup_expanded/`
- `/kaggle/working/tempglitch_significance.json`

================================================================
## GHI CHÚ — nếu Lance normal hiện chỉ có ~12-14 episode
================================================================
Để có ≥30 normal-negative thật sự, cần build Lance normal lớn hơn từ metadata 750 pairs:
```bash
python scripts/build_tempglitch_lewm_lance.py --help   # xem cờ build
python scripts/build_tempglitch_validation_manifest.py --help
```
Nếu phần này phức tạp, BÁO LẠI cho Computer — sẽ viết thêm script build Lance normal mở rộng.
Trong trường hợp xấu nhất, K-A vẫn chạy được với support hiện tại (kết quả = bản frozen cũ),
và đòn bẩy chính chuyển sang K-B (R5-XGame) vốn đã mạnh sẵn (AUROC 0.91).

## Quy tắc dừng (bắt buộc)
Dừng nếu: CUDA không có · thiếu Lance/seed input · `_role_overlap` > 0 · bất kỳ flag locked-test = true.
