# Claim Registry — LeWM Glitch Detection

> **Cập nhật:** 2026-07-01 | Branch: main | SHA: 9d2ed1a9
>
> Mọi claim số liệu trong paper PHẢI khớp bảng này trước khi nộp.
> Không được claim từ artifact chưa validated hoặc từ locked-test.

---

## 1. TempGlitch — R5 (non-locked, validated)

| Config | Seed | Window scorer | Episode agg | AUROC | AUPRC | F1 |
|---|---|---|---|---|---|---|
| **BEST** | 44 | `lewm_l2_max` | `mean` | **0.69697** | — | — |

- Artifact: `r5_tempglitch_comparison.csv` (validated, followup_complete)
- Protocol: `r5_tempglitch_nonlocked`
- Calibration: 4 frozen normal episodes (p95 threshold)
- Support: 10 normal + 22 buggy = 32 evaluation episodes

**Safe wording:**
> "On the R5 TempGlitch split, our method achieves AUROC 0.697 using
> window-max L2 surprise scoring with episode-level mean aggregation
> (seed 44)."

**FORBIDDEN:**
- ~~"mean aggregation"~~ (khi nói về best row — đây là window-level max,
  episode-level mean)
- ~~Không được ghi chỉ `lewm_mse_mean` hay `lewm_l2_mean`~~

---

## 2. TempGlitch — pair-disjoint follow-up (non-locked, validated)

| Config | Seed | Window scorer | Episode agg | AUROC |
|---|---|---|---|---|
| **BEST** | 44 | `lewm_l2_max` | `mean` | **0.71591** |

- Artifact: `followup_comparison.csv` (status: followup_complete)
- Protocol: `tempglitch_followup_pair_disjoint_nonlocked`
- Calibration: 4 frozen normal episodes
- Support: 10 normal + 22 buggy = 32 episodes
- CI: ĐO LẠI từ `followup_comparison.csv` trước khi claim CI range

**Safe wording:**
> "Under the stricter pair-disjoint protocol, LeWM achieves AUROC 0.716
> (seed 44, `lewm_l2_max`, episode mean)."

---

## 3. TempGlitch — K-A expanded (non-locked, validated)

| Config | Seed | Window scorer | Episode agg | AUROC |
|---|---|---|---|---|
| **BEST** | 43 | `lewm_l2_max` | `mean` | **0.700544** |

- Artifact: K-A expanded comparison CSV (intake complete 2026-06-30)
- Protocol: `tempglitch_followup_pair_disjoint_nonlocked` (expanded pool)

---

## 4. WOB R5 — positive-probe (non-locked)

| Metric | Value | Notes |
|---|---|---|
| F1 | **0.9474** | positive-probe, R5-WOB split |
| AUROC (locked-test) | 0.573 ± 0.118 | 4 seeds, CI [0.53, 0.87] |

- Locked test: CLOSED, unmaterialized, unscored
- CI rộng do calibration support nhỏ → không claim mạnh AUROC locked

**Safe wording:**
> "On the World of Bugs R5 split, our method achieves F1=0.947 under
> the positive-probe protocol (non-locked validation)."

---

## 5. Framing zero_action — Contribution, Không Phải Limitation

LeWM được sử dụng trong chế độ `zero_action` (không cần action labels):

**ĐÚNG — dùng trong paper:**
> "Our approach operates in an unsupervised, action-label-free setting:
> the model scores gameplay episodes without requiring synchronized
> controller input or action annotations, making it applicable to any
> recorded gameplay footage."

**SAI — tuyệt đối không dùng:**
> ~~"Due to the unavailability of action labels, we use zero-action mode
> which may limit performance..."~~

Lý do: `zero_action` là **design choice** phù hợp với threat model
(post-hoc QA trên recorded footage), không phải engineering shortcut.

---

## 6. Boundary Claims — K-B / R5-XGame

| Split | Best AUROC | Được claim ở đâu |
|---|---|---|
| R5-XGame (cross-game) | 0.9097 (`lewm_mse_max`) | Section 4 cross-game — RIÊNG |
| K-B | pending K-C | Chỉ sau K-C validated |

**KHÔNG** kéo R5-XGame AUROC vào bảng TempGlitch so sánh.

---

## 7. GPU-Gated Items (Chỉ Làm Sau K-C)

Những thứ sau **yêu cầu GPU retrain**, chưa được thực hiện:

| Item | Lý do cần GPU | Trigger điều kiện |
|---|---|---|
| `history_size=6` | Thay đổi training hyperparameter | K-C AUROC < 0.68 hoặc paper gap rõ |
| ViT-Small pretrained | Thay đổi encoder architecture | Sau khi xác nhận K-C narrative |

Nếu K-C cho AUROC ≥ 0.72 → paper viết được ngay, **KHÔNG** cần GPU.

---

## 8. Checklist Trước Khi Nộp Paper

- [ ] Mọi số trong Table 2/3 khớp với registry này
- [ ] Không có claim "episode max" hay "mean aggregation" sai ngữ cảnh
- [ ] `zero_action` được frame là contribution
- [ ] Locked test không được mention trong results section
- [ ] CI của follow-up đã được đo lại từ artifact
- [ ] K-C intake done trước khi claim WOB binary result
