# P1 Expected Outputs (để Computer ingest)

Sau khi chạy xong, tải toàn bộ các file dưới đây về và báo lại đường dẫn cho Computer.

## K-A (TempGlitch mở rộng)
```
/kaggle/working/r5_tempglitch_expanded/           # R5 output dir mở rộng
/kaggle/working/tempglitch_followup_expanded/
  ├── followup_manifest.csv
  ├── followup_manifest.sha256
  ├── followup_episode_scores.csv
  ├── followup_comparison.csv          # <-- bảng chính (AUROC/CI cho mọi config)
  ├── followup_metrics.json
  ├── followup_provenance.json
  ├── followup_validator_receipt.json  # phải có status = followup_validated
  └── FOLLOWUP_REPORT.md
/kaggle/working/tempglitch_significance.json       # DeLong p + ΔAUROC CI
```

## K-B (R5-XGame 3 seed)
```
/kaggle/working/r5_xgame_full/                     # output 3 seed
/kaggle/working/r5_xgame_significance.json         # DeLong p + ΔAUROC CI
```

## Các con số Computer cần để điền vào paper
Từ `followup_comparison.csv` và 2 file `*_significance.json`, hãy báo lại:
1. Số normal-negative / buggy-positive evaluation episodes thực tế (support mới).
2. AUROC + 95% CI của LeWM tốt nhất (TempGlitch & XGame).
3. ΔAUROC point + 95% CI (LeWM − baseline) cho cả hai.
4. DeLong p-value cho cả hai.
5. FPR@95TPR của LeWM tốt nhất (xem có giảm so với 0.75 không).
6. Giá trị `significant` (true/false) từ mỗi file significance.

## Acceptance tổng (định nghĩa "số đẹp đạt chuẩn")
- TempGlitch: support ≥ 30 neg, AUROC ≥ 0.70, CI hẹp hơn [0.535, 0.877] cũ.
- R5-XGame: AUROC ~0.90, CI tách rời baseline, DeLong p < 0.05 → claim significant.
- Tối thiểu MỘT trong hai benchmark đạt significance → đủ để nâng paper từ "evaluation" lên "method".
