# P1 — Expanded-Support Re-evaluation (K-A & K-B)

**Mục tiêu:** Biến kết quả "bounded" (CI rộng, chồng lấn) thành kết quả **significant** (CI hẹp,
DeLong p < 0.05) bằng cách (1) mở rộng evaluation support và (2) tính significance đầy đủ.

Đây KHÔNG phải train lại model. Checkpoint LeWM seed42/43/44 đã có. Chúng ta chỉ:
- **K-A:** re-score TempGlitch trên tập normal-negative mở rộng (lấy thêm normal episodes từ 750 pairs),
  giữ pair-disjoint (leakage = 0), nâng calibration lên 4–6 normal episodes.
- **K-B:** chạy đủ 3 seed cho R5-XGame để củng cố AUROC 0.9097 thành kết quả chính có CI + DeLong.
- Sau mỗi run: chạy `scripts/compute_significance_table.py` để in ngay DeLong p + ΔAUROC CI.

> **Lưu ý leakage:** mọi normal episode mới đưa vào evaluation PHẢI có `pair_id` khác với
> calibration episodes. Validator sẽ tự kiểm tra (`_role_overlap` phải = 0). Nếu vi phạm → dừng.

## Thứ tự thực hiện
1. K-A bước 1: re-score R5 TempGlitch mở rộng (notebook cell A1).
2. K-A bước 2: chạy follow-up + significance (cell A2).
3. K-B: chạy R5-XGame 3 seed + significance (cell B1).
4. Tải outputs về, báo lại cho Computer để ingest + điền số vào paper.

Chi tiết command: xem `KAGGLE_RUN_COMMAND.md`.
Output mong đợi: xem `KAGGLE_OUTPUTS_EXPECTED.md`.
