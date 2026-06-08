# MASTER ROADMAP — LeWM-Glitch Research Project
## "Latent Surprise: Temporal Video Game Glitch Localization via Regularized JEPA"
### Dành cho EAI FISAT 2026 — Deadline nộp paper: 20/07/2026

> **Trạng thái hiện tại:** 08/06/2026. Còn đúng **42 ngày** đến deadline nộp bài.
> **Cảnh báo quan trọng:** Mọi kết quả thực nghiệm chưa được chạy = TBD. Mọi dataset chưa tải = TBD. Không được bịa số liệu.

---

# PHẦN 1 — EXECUTIVE DECISION

## 1.1 Kết luận: Có nên tiếp tục đề tài?

**→ CÓ. Đề tài này khả thi và phù hợp FISAT 2026 với điều kiện giữ scope đúng.**

Lý do tiếp tục:
- Repo đã có pipeline chạy được (preprocess → score → evaluate → report).
- Ba baseline (frame_diff, feature_distance, mini_latent) đã implement xong.
- TempGlitch dataset **vừa được xác nhận có code và data công khai** (May 2026).
- GlitchBench đã có script tải về.
- FISAT là conference Scopus Q4, phù hợp level sinh viên FPT với pipeline rõ ràng.
- VLMs trên TempGlitch **gần như ngẫu nhiên** — mở cơ hội cho lightweight world model.

## 1.2 Phiên bản paper tối thiểu (MVP — đủ để nộp FISAT)

**Scope:** Temporal glitch detection bằng latent dynamics proxy trên TempGlitch benchmark.

- Dataset: TempGlitch (public, binary labels, 5 loại temporal glitch, paired glitch-free videos).
- Method: mini_latent (PCA + linear transition model) làm lightweight latent dynamics proxy.
- Baselines: frame_diff, feature_distance, mini_latent. Thêm video autoencoder nếu còn thời gian.
- Metrics: AUROC, F1, precision, recall. Temporal IoU nếu TempGlitch có temporal annotation.
- Paper: 6–8 trang Springer format. Trung thực về limitation (LeWM chưa tích hợp).
- Claim an toàn: "mini_latent outperforms simple visual baselines on temporal glitches" — nếu kết quả ủng hộ.

## 1.3 Phiên bản paper tham vọng (nếu còn thời gian)

- Tích hợp lewm_latent thật (checkpoint từ lucas-maes/le-wm).
- Thêm VideoGlitchBench subset (5238 videos, built on GamePhysics) nếu tải được.
- Thêm CNN-LSTM baseline.
- Ablation đầy đủ (temporal smoothing, clip length, SIGReg on/off).
- Inference FPS table.

## 1.4 Must-have để nộp FISAT

| # | Must-Have | Deadline nội bộ |
|---|-----------|-----------------|
| 1 | TempGlitch dataset tải thành công và pipeline chạy được | 15/06 |
| 2 | Ba baseline (frame_diff, feature_distance, mini_latent) có số liệu trên TempGlitch | 22/06 |
| 3 | Bảng kết quả so sánh 3 baselines với metric AUROC + F1 | 29/06 |
| 4 | Paper draft 6-8 trang (Springer template, tiếng Anh) | 10/07 |
| 5 | GitHub repo clean, reproducible README | 15/07 |
| 6 | Slides 10-15 trang | 18/07 |
| 7 | Submit lên EAI submission system | 20/07 |

## 1.5 Nice-to-have

- Real LeWM integration (lewm_latent.py).
- Event-level Macro-F1 và temporal mIoU (nếu TempGlitch có temporal span).
- Video autoencoder baseline.
- Qualitative hình ảnh minh họa.
- Inference FPS comparison.

---

# PHẦN 2 — RESEARCH GOAL & PAPER DEFINITION

## 2.1 Final Research Title

**Full title:** "Latent Surprise: Temporal Video Game Glitch Localization via a Lightweight Regularized Joint-Embedding Predictive Architecture"

**Short title:** "LeWM-Glitch: Latent Dynamics for Temporal Glitch Detection"

**One-sentence pitch:**
"We show that a lightweight latent world model detects temporal video game glitches more reliably than simple visual baselines by measuring unexpected deviations in learned gameplay dynamics."

## 2.2 Research Problem

Phát hiện glitch trong game dựa trên frame đơn lẻ bỏ qua lớp lỗi chỉ xuất hiện theo thời gian (teleport, wall-clip, physics violation, animation freeze). Câu hỏi là: một latent world model học từ gameplay bình thường có thể phát hiện các lỗi này bằng latent prediction error không?

## 2.3 Main Hypothesis

Các temporal glitch trong game vi phạm dynamics bình thường. Một mô hình học từ normal gameplay sẽ sinh ra latent prediction error cao hơn trên các clip glitch so với clip bình thường — và error này phân biệt được glitch tốt hơn sự khác biệt pixel thô.

## 2.4 Ba Research Questions Quan Trọng Nhất

| RQ | Nội dung | Metric tương ứng |
|----|----------|-----------------|
| RQ1 | Latent dynamics proxy có phát hiện temporal glitch tốt hơn visual baselines không? | AUROC, F1 trên TempGlitch |
| RQ2 | Loại temporal glitch nào dễ/khó phát hiện nhất bằng latent prediction error? | Per-category F1 |
| RQ3 | Temporal smoothing có cải thiện localization không? | AUROC, F1 với/không temporal smoothing |

## 2.5 Ba Contributions An Toàn (Không Overclaim)

1. **Pipeline reproducible:** Hệ thống preprocessing → scoring → evaluation chuẩn hóa CSV, chạy được trên Colab/Kaggle, có unit tests.
2. **Benchmark baseline:** Kết quả định lượng đầu tiên của lightweight latent dynamics approach trên TempGlitch temporal glitch categories.
3. **Phân tích failure modes:** Chỉ rõ loại glitch nào latent proxy phát hiện được/không được, tại sao, và gợi ý hướng cải thiện.

## 2.6 Ba Claims Tuyệt Đối Tránh

1. ❌ "LeWM-Glitch phát hiện mọi loại glitch trong game" → chỉ claim trên loại visual/physics/temporal trong TempGlitch.
2. ❌ "Vượt qua VLM ở mọi khía cạnh" → chỉ so sánh speed, cost, temporal localization khi có số liệu.
3. ❌ "Tạo dataset mới" → chỉ dùng public benchmark, dataset tự tạo chỉ là sanity check.

---

# PHẦN 3 — ROADMAP TỔNG THỂ THEO PHASE

## Phase 0 — Repo & Research Foundation

| Hạng mục | Chi tiết |
|----------|----------|
| **Objective** | Đảm bảo repo, docs, environment sẵn sàng trước khi chạy thực nghiệm |
| **Tasks** | (1) Git pull latest. (2) Verify submodules. (3) Install deps. (4) Chạy synthetic demo. (5) Update research docs. |
| **Files to create/update** | `docs/research/00_research_overview.md`, `AGENTS.md`, `README.md`, `docs/research/11_tempglitch_integration_plan.md` |
| **Commands** | `git submodule update --init`, `pip install -e .[dev]`, `python scripts/run_synthetic_demo.py`, `python -m pytest` |
| **Expected outputs** | Tests pass, synthetic_scores.csv + metrics.json exist |
| **Acceptance criteria** | F1 > 0 trên synthetic demo. pytest không có lỗi import. |
| **Estimated time** | 0.5 ngày |
| **Risks** | Missing deps (numpy, Pillow, pytest) |
| **Backup plan** | `pip install numpy Pillow pytest` thủ công |

## Phase 1 — Literature Review & Source Verification

| Hạng mục | Chi tiết |
|----------|----------|
| **Objective** | Verify tất cả paper citations, dataset links trước khi viết literature review |
| **Tasks** | Verify LeWM arXiv, TempGlitch arXiv, VideoGlitchBench arXiv, GlitchBench CVPR 2024, World of Bugs. Cập nhật literature_matrix.md. |
| **Files** | `docs/research/02_literature_matrix.md` (update TBD → confirmed/not-available) |
| **Commands** | Web search cho từng paper. `curl -L arxiv.org/abs/...` để kiểm tra availability. |
| **Expected outputs** | literature_matrix.md không còn TBD cho những paper đã xác nhận |
| **Acceptance criteria** | ≥ 6 papers được verify URL + abstract. Tất cả claim đều có source. |
| **Estimated time** | 1 ngày |
| **Risks** | Một số paper mới chưa có code/data |
| **Backup plan** | Đánh dấu "accessed Jun 2026" cho papers đã verify |

## Phase 2 — Dataset Access & Data Pipeline

| Hạng mục | Chi tiết |
|----------|----------|
| **Objective** | Tải TempGlitch và/hoặc GlitchBench, verify format, convert sang pipeline hiện tại |
| **Tasks** | (1) Tìm TempGlitch project website. (2) Download data. (3) Convert sang clip format. (4) Tạo labels.csv. (5) Chạy pipeline verify. |
| **Files** | `scripts/download_tempglitch.py`, `scripts/convert_tempglitch_labels.py`, `data/raw/tempglitch/` (gitignored) |
| **Commands** | `python scripts/download_tempglitch.py --output data/raw/tempglitch` |
| **Expected outputs** | manifest.csv với TempGlitch clips. labels.csv với binary glitch labels. |
| **Acceptance criteria** | Pipeline preprocess → score → evaluate chạy end-to-end trên TempGlitch subset. |
| **Estimated time** | 2-3 ngày |
| **Risks** | Dataset format khác với expected. Video files lớn. |
| **Backup plan** | Nếu TempGlitch không tải được → dùng GlitchBench (HuggingFace, đã có script). |

## Phase 3 — Baseline Experiments

| Hạng mục | Chi tiết |
|----------|----------|
| **Objective** | Chạy frame_diff và feature_distance trên TempGlitch, có metrics.json |
| **Tasks** | Chạy 2 baselines. Generate comparison table. Document failure modes. |
| **Files** | `outputs/tempglitch_frame_diff_metrics.json`, `outputs/tempglitch_feature_distance_metrics.json`, `outputs/tempglitch_baseline_comparison.md` |
| **Commands** | `python scripts/run_tempglitch_experiments.py --scorers frame_diff feature_distance` |
| **Expected outputs** | Bảng AUROC, F1, Precision, Recall cho từng baseline |
| **Acceptance criteria** | Ít nhất 1 baseline có AUROC > 0.5 (better than random) |
| **Estimated time** | 2 ngày |
| **Risks** | Kết quả tệt hơn random → pipeline bug |
| **Backup plan** | Debug với synthetic data; verify label format |

## Phase 4 — Mini-Latent / Proxy Latent Dynamics

| Hạng mục | Chi tiết |
|----------|----------|
| **Objective** | Chạy mini_latent trên TempGlitch và so sánh với baselines |
| **Tasks** | Tune latent_dim, image_size. Chạy mini_latent. So sánh với frame_diff và feature_distance. |
| **Files** | `outputs/tempglitch_mini_latent_metrics.json`, `outputs/tempglitch_full_comparison.md` |
| **Commands** | `python -m glitch_detection.run_baseline --scorer mini_latent --input data/raw/tempglitch/frames --labels data/raw/tempglitch/labels.csv --name tempglitch_mini_latent` |
| **Expected outputs** | mini_latent metrics.json. So sánh 3 baselines. |
| **Acceptance criteria** | mini_latent AUROC ≥ frame_diff AUROC trên ít nhất 1 glitch category |
| **Estimated time** | 2 ngày |
| **Risks** | mini_latent không hơn baseline → điều chỉnh latent_dim, thêm normalization |
| **Backup plan** | Vẫn báo cáo kết quả trung thực; phân tích tại sao |

## Phase 5 — Real LeWorldModel Integration (Optional / Best-effort)

| Hạng mục | Chi tiết |
|----------|----------|
| **Objective** | Thay thế mini_latent bằng LeWM thật nếu checkpoint có sẵn |
| **Tasks** | Audit external/le-wm. Load checkpoint. Implement lewm_latent.py. Score on TempGlitch subset. |
| **Files** | `src/glitch_detection/lewm_latent.py` (implement thật), `scripts/download_lewm_checkpoint.py` |
| **Commands** | `git submodule update --init external/le-wm`, kiểm tra requirements, load checkpoint |
| **Expected outputs** | lewm_latent scores.csv trên ≥ 50 clips TempGlitch |
| **Acceptance criteria** | LeWM AUROC ≥ mini_latent AUROC. Pipeline chạy không OOM. |
| **Estimated time** | 3-5 ngày |
| **Risks** | OOM, API mismatch, checkpoint không tải được |
| **Backup plan** | Giữ mini_latent làm primary method; frame LeWM là "future work" trong paper |

## Phase 6 — Evaluation & Metrics

| Hạng mục | Chi tiết |
|----------|----------|
| **Objective** | Tính đủ metrics cho paper |
| **Tasks** | AUROC, F1, Precision, Recall trên TempGlitch. Per-category breakdown. Temporal smoothing ablation. Threshold calibration. |
| **Files** | `src/glitch_detection/evaluate.py` (mở rộng cho per-category). `outputs/final_metrics_table.json` |
| **Commands** | `python -m glitch_detection.evaluate --scores ... --labels ... --output ...` |
| **Expected outputs** | metrics table với ≥ 3 methods × ≥ 2 metric |
| **Acceptance criteria** | Không có data leakage. Threshold chọn trên val set, test trên test set. |
| **Estimated time** | 2 ngày |
| **Risks** | Không đủ dữ liệu để split properly |
| **Backup plan** | Dùng leave-one-video-out cross-validation nếu dataset nhỏ |

## Phase 7 — Ablation Studies

| Hạng mục | Chi tiết |
|----------|----------|
| **Objective** | Ít nhất 2 ablations có số liệu để viết vào paper |
| **Tasks** | Ablation 1: với/không temporal smoothing. Ablation 2: latent_dim khác nhau. |
| **Files** | `outputs/ablation_smoothing.md`, `outputs/ablation_latent_dim.md` |
| **Estimated time** | 1-2 ngày |

## Phase 8 — Figure & Table Generation

| Hạng mục | Chi tiết |
|----------|----------|
| **Objective** | Tạo figures cho paper: architecture diagram, score timeline, results table |
| **Tasks** | Architecture SVG/draw. Score timeline plot (score_plot từ plot_scores.py). Results table LaTeX/Markdown. |
| **Files** | `paper/figures/architecture.svg`, `paper/figures/score_timeline.png`, `paper/tables/main_results.tex` |
| **Estimated time** | 2 ngày |

## Phase 9 — Paper Writing

| Hạng mục | Chi tiết |
|----------|----------|
| **Objective** | Paper 6-8 trang, Springer format, tiếng Anh |
| **Tasks** | Viết theo thứ tự: Problem → Method → Experiments → Results → Ablation → Discussion → Abstract → Intro. |
| **Files** | `paper/main.tex`, `paper/references.bib` |
| **Estimated time** | 5-7 ngày (trải đều) |

## Phase 10 — Slides & Submission Package

| Hạng mục | Chi tiết |
|----------|----------|
| **Objective** | Submission-ready package |
| **Tasks** | Polish paper. Slides 10-15 trang. Kiểm tra formatting. Submit lên EAI system. |
| **Files** | `slides/fisat2026_presentation.pptx`, `paper/main.pdf` |
| **Estimated time** | 2-3 ngày |

---

# PHẦN 4 — ROADMAP 30 NGÀY ĐẦU TIÊN

> **Context:** Hôm nay 08/06. Deadline 20/07. 30 ngày đầu = đến 08/07, còn 12 ngày buffer để polish.

## Block 1: Ngày 1-2 (08-09/06) — Environment & Foundation

**Làm gì:**
- [ ] Chạy `git submodule update --init` → kiểm tra `external/le-wm` và `external/world-of-bugs`.
- [ ] Chạy `python -m pip install -e .[dev]` và `python -m pytest` → fix nếu có lỗi.
- [ ] Chạy `python scripts/run_synthetic_demo.py` → xác nhận pipeline end-to-end.
- [ ] Chạy `python scripts/run_dynamics_experiments.py` → lấy baseline numbers trên synthetic.
- [ ] Tạo `docs/research/11_tempglitch_integration_plan.md` ghi kế hoạch tải TempGlitch.
- [ ] Web search tìm TempGlitch project website (paper: arXiv 2605.21443, submitted 20 May 2026).

**Output:**
- pytest pass.
- `outputs/dynamics_comparison.md` có số liệu 3 baselines.
- TempGlitch project website URL đã tìm được.

**Tiêu chí pass:**
- `outputs/synthetic_scores.csv` tồn tại.
- TempGlitch URL xác nhận code + data có thể download.

---

## Block 2: Ngày 3-5 (10-12/06) — TempGlitch Dataset

**Làm gì:**
- [ ] Tải TempGlitch dataset từ project website (TBD — cần verify URL từ arXiv paper).
- [ ] Inspect data format: video files hay frame folders? annotation format?
- [ ] Tạo `scripts/download_tempglitch.py` hoặc document manual download steps.
- [ ] Tạo `scripts/convert_tempglitch_labels.py`: convert annotation sang `labels.csv` format (`source,start_frame,end_frame,label`).
- [ ] Chạy preprocess trên ≥ 20 TempGlitch clips.
- [ ] Verify manifest.csv có đúng format.

**Output:**
- `data/raw/tempglitch/` (gitignored) có clips.
- `data/raw/tempglitch_labels.csv` có binary labels.
- `data/processed/tempglitch_test/manifest.csv` tồn tại.

**Tiêu chí pass:**
- Preprocess không lỗi.
- Manifest có ≥ 20 rows với source, start_frame, end_frame hợp lệ.
- Labels CSV có ít nhất 5 positive (glitch) clips.

**Nếu thất bại:**
- Backup: tải GlitchBench thêm (đã có `download_glitchbench_subset.py`). Script tải 12 images và tạo labels.
- Backup 2: Dùng World of Bugs asset demo (đã có `run_worldofbugs_asset_demo.py`).

---

## Block 3: Ngày 6-9 (13-16/06) — Baseline Results trên TempGlitch

**Làm gì:**
- [ ] Tạo `scripts/run_tempglitch_experiments.py` (clone từ `run_dynamics_experiments.py`).
- [ ] Chạy frame_diff trên TempGlitch → `outputs/tempglitch_frame_diff_metrics.json`.
- [ ] Chạy feature_distance → `outputs/tempglitch_feature_distance_metrics.json`.
- [ ] Chạy mini_latent → `outputs/tempglitch_mini_latent_metrics.json`.
- [ ] Tạo comparison table `outputs/tempglitch_baseline_comparison.md`.
- [ ] Tạo `scripts/summarize_tempglitch_experiments.py` (clone từ `summarize_all_experiments.py`).

**Output:**
- `outputs/tempglitch_baseline_comparison.md` với AUROC, F1, Precision, Recall.
- Score plots cho mỗi baseline.

**Tiêu chí pass:**
- Ít nhất 1 baseline có AUROC > 0.5.
- mini_latent metrics.json tồn tại (kể cả nếu kết quả không tốt).
- Không có NaN hoặc exception trong evaluate.py.

**Nếu AUROC < 0.5:**
- Debug: kiểm tra label alignment (frame numbers có đúng không?).
- Thử stride nhỏ hơn (4 thay vì 8).
- Thử clip_length = 8 thay vì 16.

---

## Block 4: Ngày 10-13 (17-20/06) — Literature Matrix & Research Docs

**Làm gì:**
- [ ] Update `docs/research/02_literature_matrix.md`: thay tất cả "TBD / verify" bằng confirmed hoặc "not-available-as-of-Jun-2026".
- [ ] Đặc biệt verify: LeWM (arXiv 2603.19312), TempGlitch (arXiv 2605.21443), VideoGlitchBench (arXiv 2604.07818), GlitchBench CVPR 2024, World of Bugs (arXiv 2206.11037).
- [ ] Update `docs/research/04_dataset_benchmark_map.md`: thêm TempGlitch với confirmed access status.
- [ ] Update `docs/research/09_risks_and_limitations.md`: thêm risk "TempGlitch annotation format requires conversion".
- [ ] Tạo `docs/research/12_experiment_results_log.md`: log running results.

**Output:**
- literature_matrix.md không còn "TBD" cho các paper quan trọng.
- Mỗi paper có: title, year, venue, URL, main claim, relevance to this repo.

**Tiêu chí pass:**
- ≥ 6 papers được verify đầy đủ với URL.
- Không có paper nào bị cite mà không có URL verified.

---

## Block 5: Ngày 14-17 (21-24/06) — Extended Baselines & Ablation Planning

**Làm gì:**
- [ ] Thêm temporal smoothing vào mini_latent: implement `smooth_scores(scores, window=3)` trong evaluate.py hoặc score_clips.py.
- [ ] Chạy mini_latent với temporal smoothing → so sánh AUROC với/không smoothing.
- [ ] Thử latent_dim = {4, 8, 16, 32} trên mini_latent → ghi vào ablation table.
- [ ] Thử clip_length = {8, 16, 32} → xem ảnh hưởng.
- [ ] Tạo `docs/research/13_ablation_results.md`.

**Output:**
- Ablation table cho temporal smoothing.
- Ablation table cho latent_dim.
- `outputs/ablation_smoothing_comparison.md`.

**Tiêu chí pass:**
- Ít nhất 1 ablation cho thấy sự khác biệt có ý nghĩa (> 0.02 AUROC).

---

## Block 6: Ngày 18-21 (25-28/06) — LeWM Integration Attempt

**Làm gì:**
- [ ] `git submodule update --init external/le-wm`.
- [ ] Đọc `external/le-wm/README.md` và code structure.
- [ ] Kiểm tra: có checkpoint pre-trained không? Requirements là gì?
- [ ] Quyết định go/no-go: Nếu checkpoint có thể tải và chạy trên T4 → proceed. Nếu không → skip, dùng mini_latent làm primary.
- [ ] Nếu proceed: implement `lewm_latent.py` Stage 1-4 (encoder + checkpoint loading).

**Output:**
- `docs/research/14_lewm_integration_audit.md`: kết quả audit, go/no-go decision với lý do rõ ràng.
- Nếu proceed: lewm_latent.py có thể encode ít nhất 1 clip.

**Tiêu chí pass:**
- Decision được ghi thành văn bản. Nếu skip, có backup plan rõ ràng.

---

## Block 7: Ngày 22-25 (29/06-02/07) — Results Consolidation

**Làm gì:**
- [ ] Chạy tất cả experiments lần cuối với seed cố định.
- [ ] Tạo final metrics table với ≥ 3 methods × ≥ 3 metrics.
- [ ] Tạo `paper/tables/main_results.tex` hoặc `paper/tables/main_results.md`.
- [ ] Tạo score timeline plots đẹp cho ≥ 2 representative clips.
- [ ] Tạo architecture figure (có thể dùng draw.io, matplotlib, hoặc SVG).

**Output:**
- Final results table (LaTeX-ready).
- ≥ 2 figures cho paper.
- `scripts/generate_paper_figures.py`.

**Tiêu chí pass:**
- Tất cả số liệu đều reproducible (chạy lại script → cùng results trong ±0.01).
- Figures đủ chất lượng để đưa vào paper.

---

## Block 8: Ngày 26-30 (03-07/07) — Paper Writing Sprint

**Làm gì:**
- [ ] Tải Springer LNCS template: `paper/main.tex`.
- [ ] Viết theo thứ tự: Problem Formulation → Methodology → Experimental Setup → Results → Ablation → Discussion → Limitations → Abstract → Introduction → Conclusion.
- [ ] Target: 6 pages content + 1-2 pages references.
- [ ] Review internal: đọc lại, check claim không overclaim.
- [ ] Update `docs/research/references.bib`.

**Output:**
- `paper/main.tex` compilable.
- `paper/main.pdf` ≥ 6 trang.

**Tiêu chí pass:**
- Paper compile không lỗi.
- Không có claim nào không có evidence từ thực nghiệm.
- Tất cả references có đúng bibtex.

---

# PHẦN 5 — ROADMAP 8 TUẦN HOÀN THÀNH PAPER

> **Thực tế:** Còn 6 tuần đến deadline (20/07). Tuần 7-8 rút ngắn thành buffer + submission.

| Tuần | Ngày | Goal | Deliverables | Pass/Fail | Risk | Fallback |
|------|------|------|--------------|-----------|------|----------|
| **1** | 08-14/06 | Research foundation + dataset access | TempGlitch tải thành công. Synthetic baseline verified. Literature matrix updated. | TempGlitch manifest.csv tồn tại | TempGlitch không accessible | GlitchBench + World of Bugs fallback |
| **2** | 15-21/06 | Baseline results trên TempGlitch | 3 baselines có metrics.json. Comparison table. | ≥ 1 baseline AUROC > 0.5 | Kết quả gần random | Debug label alignment |
| **3** | 22-28/06 | Ablation + LeWM audit | Ablation table (smoothing + latent_dim). LeWM audit go/no-go document. | Ablation table ≥ 6 rows | LeWM quá nặng | Mini_latent làm primary method |
| **4** | 29/06-05/07 | Figures + results consolidation | Final results table, architecture figure, score timeline plots | All figures reproducible | Matplotlib không đủ đẹp | Draw.io export PNG |
| **5** | 06-12/07 | Paper writing (draft) | Paper draft 5-6 trang compilable Springer | Paper compile | Không đủ kết quả | Reduced scope |
| **6** | 13-20/07 | Polish + submit | Final paper ≥ 6 trang, slides, GitHub clean, submit | Submit trước 20/07 23:59 AoE | Technical issues EAI system | Submit 19/07 để có buffer |

---

# PHẦN 6 — DATASET STRATEGY

## 6.1 TempGlitch (Primary Benchmark — **ƯU TIÊN SỐ 1**)

**Vai trò:** Benchmark chính cho temporal glitch detection.

**Tại sao TempGlitch:**
- Paper arXiv 2605.21443 (May 2026) xác nhận: "Code and data are available at the project website."
- Thiết kế đặc biệt cho temporal glitch detection (không phải spatial).
- Có 5 loại temporal glitch với balanced per-category samples.
- Paired glitch-free videos → binary evaluation chuẩn xác.
- VLMs near chance trên benchmark này → opportunity for lightweight methods.

**Cách kiểm tra availability:**
```bash
# Bước 1: Tìm project website từ paper
# arXiv 2605.21443 → contact info → project URL
# Thường là GitHub hoặc project page
curl -L "https://arxiv.org/abs/2605.21443" | grep -i "github\|project\|dataset"

# Bước 2: Thử trực tiếp từ thông tin author
# Authors: Yu, Wiens, Barahona-Rios, Wilkins, Zadtootaghaj, Barman, Bezemer
# Wilkins = Benedict Wilkins (World of Bugs author) → check github.com/BenedictWilkins
```

**Annotation format cần tìm hiểu:**
- Binary label per clip hoặc per video?
- Temporal span annotations (start/end second) hay frame-level?
- Nếu có temporal spans → convert sang `source,start_frame,end_frame,label` CSV format.

**Rủi ro:** Paper mới (3 tuần tuổi) — project website có thể chưa stable.

**Backup nếu không tải được:**
1. GlitchBench (Hugging Face) — đã có script.
2. World of Bugs asset demo — đã có script.
3. VideoGlitchBench (GamePhysics, public Reddit data) — cần script mới.

## 6.2 World of Bugs (Secondary — Benchmark Phụ)

**Vai trò:** Controlled game bug examples, possible evaluation source.

**Cách dùng:**
```bash
git submodule update --init external/world-of-bugs
ls external/world-of-bugs/docs/Reference/Examples/imgs/
python scripts/run_worldofbugs_asset_demo.py
```

**Annotation format:** TBD / verify sau khi init submodule.

**Rủi ro Unity:** Chỉ cần image assets, không cần Unity runtime.

**Backup:** Script `run_worldofbugs_asset_demo.py` đã dùng static images — không cần Unity.

## 6.3 GlitchBench (Tertiary — Case Study)

**Tại sao không dùng làm benchmark chính:**
- Chủ yếu static/image-based (không temporal).
- GlitchBench CVPR 2024: 513 images + 75 synthetic Unity frames.
- "Second criterion: potential for humans to detect glitch from a single frame" — thiết kế cho static detection.

**Cách dùng phù hợp:**
- Image-level baseline comparison.
- Qualitative case study.
- Không dùng để claim temporal performance.

**Script hiện có:** `scripts/download_glitchbench_subset.py --limit 12`.

## 6.4 Synthetic Data (Sanity Check Only)

**Chỉ dùng cho:**
- Verify pipeline mechanics.
- Debug scorer behavior.
- Unit tests.

**Tuyệt đối không dùng để claim:**
- Performance trên real gameplay.
- SOTA results.
- Generalization.

---

# PHẦN 7 — METHODOLOGY IMPLEMENTATION PLAN

## Module Map

| Module/File | Purpose | Input | Output | Depends on | Done criteria |
|-------------|---------|-------|--------|------------|---------------|
| `preprocess.py` | Video/frames → clips | Video hoặc frame folder | `manifest.csv` + clip dirs | PIL, numpy | clips + manifest tồn tại |
| `manifest.py` | CSV read/write, label overlap | CSV files | ClipRecord, LabelInterval | stdlib | Tests pass |
| `frame_diff.py` | Frame difference baseline | manifest.csv | scores.csv | numpy, PIL | AUROC > 0 trên synthetic |
| `feature_distance.py` | RGB feature baseline | manifest.csv, labels.csv | scores.csv | numpy | Score glitch > normal |
| `mini_latent.py` | PCA + transition model | manifest.csv, labels.csv | scores.csv | numpy | Transition error > 0 |
| `lewm_latent.py` | LeWM latent prediction | manifest.csv, checkpoint | scores.csv | le-wm, torch | Encode 1 clip thành công |
| `evaluate.py` | Metrics computation | scores.csv, labels.csv | metrics.json | sklearn nếu muốn; hiện tại pure python | AUROC, F1 đúng |
| `smooth_scores()` | Temporal smoothing | scores.csv | smoothed_scores.csv | numpy | AUROC cải thiện trên noisy data |
| `threshold_calibration()` | Chọn threshold trên val | val scores + labels | threshold float | evaluate.py | Không dùng test labels |
| `event_extractor()` | Convert clip scores → events | scores.csv, threshold | events.csv (start, end, score) | — | Events có temporal span |
| `per_category_eval()` | Breakdown metrics by glitch type | scores.csv, labels với category | per_category_metrics.json | evaluate.py | Per-category F1 dict |
| `compare_experiments.py` | So sánh nhiều experiments | list of metrics.json | comparison.md | — | Table đúng format |
| `plot_scores.py` | Score timeline | scores.csv | PNG plot | PIL | Plot đẹp, có glitch interval marked |
| `generate_paper_figures.py` | Tạo figures cho paper | metrics, scores | SVG/PNG figures | matplotlib | Figures chất lượng paper |
| `dataset_report.py` | Markdown report | manifest, labels, scores, metrics | report.md | — | Report có đủ sections |

---

# PHẦN 8 — BASELINE PLAN

## Mức bắt buộc (phải có trong paper)

### 1. Frame Difference (`frame_diff`)
- **Tại sao:** Simplest temporal baseline. Bắt sudden visual changes.
- **Implementation:** Đã có trong `frame_diff.py`.
- **Compute cost:** CPU, <1 giây/clip.
- **Expected weakness:** False positives trên high-motion normal gameplay. Miss semantic/logic glitches.
- **Script:** `python -m glitch_detection.run_baseline --scorer frame_diff`
- **Khi nào bỏ:** Không bỏ — dùng làm lower-bound reference.

### 2. Feature Distance (`feature_distance`)
- **Tại sao:** RGB mean/std distance — captures appearance-level anomalies.
- **Implementation:** Đã có trong `feature_distance.py`.
- **Compute cost:** CPU, <1 giây/clip.
- **Expected weakness:** Weak temporal understanding.
- **Script:** `python -m glitch_detection.run_baseline --scorer feature_distance`

### 3. Mini Latent (`mini_latent`)
- **Tại sao:** Lightweight proxy cho latent world model hypothesis. Main method nếu LeWM không tích hợp được.
- **Implementation:** Đã có trong `mini_latent.py`.
- **Compute cost:** CPU, ~2-5 giây/clip tùy latent_dim.
- **Expected weakness:** Linear PCA + linear transition → limited capacity.
- **Script:** `python -m glitch_detection.run_baseline --scorer mini_latent`
- **Khi nào bỏ:** Không bỏ — đây là main contribution nếu LeWM unavailable.

## Mức nên có (nếu còn thời gian, trước 05/07)

### 4. Video Autoencoder
- **Tại sao:** Classic video anomaly detection baseline.
- **Implementation đơn giản nhất:** Conv3D autoencoder train trên normal clips, reconstruction error làm score.
- **Compute cost:** GPU (T4 Colab), ~30 phút train trên TempGlitch normal subset.
- **Script cần tạo:** `src/glitch_detection/video_autoencoder.py`
- **Khi nào bỏ:** Nếu sau ngày 05/07 chưa implement → skip, chú thích là "future work".

### 5. CNN-LSTM (AstroBug-style)
- **Tại sao:** Supervised temporal classifier — thường dùng trong game QA.
- **Implementation:** PyTorch CNN encoder + LSTM trên clip sequences.
- **Compute cost:** GPU, cần labeled data để train.
- **Khi nào bỏ:** Nếu không đủ labeled data → skip. Chỉ add nếu TempGlitch có đủ data.

## Mức nếu còn thời gian (sau ngày 10/07 — rất unlikely)

### 6. VLM Baseline (LLaVA / GPT-4V)
- **Tại sao:** Comparison point với TempGlitch paper results (VLMs near chance).
- **Cách triển khai:** Prompt VLM với clips, hỏi "is this a glitch?"
- **Khi nào bỏ:** Nếu không có API key hoặc sau 10/07 → skip. TempGlitch paper đã có VLM results → cite từ paper.

---

# PHẦN 9 — LEWM INTEGRATION PLAN

## Stage-by-Stage Plan

| Stage | Task | Estimated Time | Go/No-Go |
|-------|------|---------------|----------|
| **Stage 1** | `git submodule update --init external/le-wm` → đọc README, structure | 2h | Proceed nếu README clear |
| **Stage 2** | Identify encoder, predictor, checkpoint format từ code | 4h | Proceed nếu API có thể wrap |
| **Stage 3** | Tạo adapter wrapper trong `lewm_latent.py` (không breaking) | 4h | Proceed nếu không OOM |
| **Stage 4** | Load checkpoint hoặc train small model trên normal gameplay clips | 1 ngày | Proceed nếu T4/P100 đủ VRAM |
| **Stage 5** | Encode clips thành latent sequences z_t | 2h | Verify z_t shape là (T, D) |
| **Stage 6** | Predict next latent: zhat_{t+1} = predictor(z_t) | 2h | Verify error computation |
| **Stage 7** | Export scores.csv với score = mean ||z_{t+1} - zhat_{t+1}||_2 | 1h | scores.csv đúng format |
| **Stage 8** | Validate trên synthetic/dynamics data | 2h | Glitch clips score > normal |
| **Stage 9** | Run trên TempGlitch subset (≥ 50 clips) | 4h | AUROC > mini_latent |

## Khi nào mini_latent đủ để claim?

**mini_latent là acceptable primary method nếu:**
- Kết quả rõ ràng hơn frame_diff và feature_distance.
- Paper honest về limitation: "We use a linear PCA-based transition model as a lightweight proxy for JEPA-style latent world models."
- Future work section đề cập LeWM integration.

**Khi nào proxy KHÔNG đủ để claim LeWorldModel:**
- Không được viết "we use LeWorldModel" nếu chỉ dùng mini_latent.
- Phải viết "we use a lightweight latent dynamics proxy inspired by JEPA objectives."
- LeWM chỉ được mention là future work hoặc failed integration attempt (với lý do rõ).

## Cách viết paper trung thực nếu chỉ có proxy results

```latex
% Methodology section
We instantiate the latent anomaly scorer with a lightweight proxy:
a PCA encoder fitted on normal clips and a linear transition model
predicting the next latent state from current state and latent velocity.
This proxy tests the core hypothesis---temporal glitches produce higher
next-state prediction error---without requiring a pre-trained JEPA checkpoint.
Full integration of LeWorldModel is left as future work (see Section 7).
```

---

# PHẦN 10 — EVALUATION & METRICS PLAN

## 10.1 Frame-level AUROC

```python
# Mỗi clip có 1 score và 1 binary label (0=normal, 1=glitch)
# AUROC = P(score_glitch > score_normal) over all (glitch, normal) pairs

labels = [0, 0, 1, 1]   # 0=normal, 1=glitch
scores = [0.1, 0.2, 0.8, 0.9]
# evaluate.py auroc() function đã implement: wins/total
```

**Code đã có trong `evaluate.py`:** `auroc(labels, scores)`.

## 10.2 Event Macro-F1

Nếu TempGlitch có temporal span annotations (start/end second):
```
1. Convert scores.csv thành event sequence với threshold
2. Mỗi predicted event = [start_frame, end_frame]
3. Match predicted events với ground truth events (IoU > 0.5 = true positive)
4. Tính F1 per glitch category, average → Macro-F1
```

**Script cần viết:** `src/glitch_detection/event_metrics.py`

## 10.3 Temporal mIoU

```
mIoU = mean over all (predicted, gt) matched pairs of:
  IoU = intersection_frames / union_frames
```

## 10.4 Detection Delay

```
delay = first_frame_predicted_glitch - first_frame_actual_glitch
```
Chỉ tính được nếu có temporal span labels.

## 10.5 Inference FPS

```bash
time python -m glitch_detection.run_baseline --scorer mini_latent --input data/raw/tempglitch/frames ...
# FPS = total_clips / total_time
```

Đo trên CPU (Colab T4 CPU mode) để claim "runs in real-time on consumer hardware."

## 10.6 Chọn Threshold (Không Data Leakage)

```
Procedure:
1. Split TempGlitch: 70% train/val, 30% test (split by VIDEO, không split by clip)
2. Chạy scorer trên train/val → scores_val.csv
3. Chọn threshold bằng best F1 trên val set
4. Apply threshold trên test set → test metrics
5. Báo cáo test metrics trong paper
```

**Cách split theo video:**
```python
# Trong manifest.csv, "source" field = video name
# Split video names, không split clips
import random
random.seed(42)
all_videos = list(set(record.source for record in manifest))
random.shuffle(all_videos)
test_videos = all_videos[:int(0.3 * len(all_videos))]
```

---

# PHẦN 11 — ABLATION STUDY PLAN

## Ablation 1: Latent Error vs Pixel Reconstruction Error

| Item | Detail |
|------|--------|
| **Research question** | Latent error có tốt hơn pixel error không? |
| **Setup** | mini_latent (latent error) vs frame_diff (pixel error) |
| **Expected result** | mini_latent tốt hơn trên temporal glitches |
| **Metric** | AUROC, F1 trên TempGlitch |
| **Risk** | frame_diff có thể ngang hoặc tốt hơn |
| **Minimum viable** | Report cả hai, analyze khi nào latent tốt hơn |

## Ablation 2: Temporal Smoothing

| Item | Detail |
|------|--------|
| **Research question** | Smoothing có giảm false positives không? |
| **Setup** | mini_latent với window={1, 3, 5, 9} |
| **Expected result** | Window=3 hoặc 5 cho AUROC tốt nhất |
| **Metric** | AUROC, F1 |
| **Risk** | Smoothing có thể làm mờ short glitches |
| **Minimum viable** | Chạy 3 window sizes |

## Ablation 3: Clip Length và Stride

| Item | Detail |
|------|--------|
| **Research question** | Clip length ảnh hưởng thế nào đến detection? |
| **Setup** | clip_length ∈ {8, 16, 32}, stride ∈ {4, 8} |
| **Expected result** | Clip_length=16 balance tốt nhất |
| **Metric** | AUROC |
| **Risk** | Compute cost tăng với clip_length=32 |
| **Minimum viable** | Clip_length ∈ {8, 16} |

## Ablation 4: Latent Dimension

| Item | Detail |
|------|--------|
| **Research question** | Latent dim tối ưu cho mini_latent? |
| **Setup** | latent_dim ∈ {4, 8, 16, 32} |
| **Expected result** | Giảm dần variance sau dim=16 |
| **Metric** | AUROC |
| **Minimum viable** | 3 values: {4, 8, 16} |

## Ablation 5: SIGReg On/Off (Chỉ nếu LeWM tích hợp)

| Item | Detail |
|------|--------|
| **Research question** | SIGReg có ngăn representation collapse không? |
| **Setup** | LeWM với/không SIGReg regularization |
| **Expected result** | LeWM với SIGReg có latent distribution ít collapsed hơn |
| **Risk** | Cần train 2 LeWM models → expensive |
| **Minimum viable** | Skip nếu LeWM không tích hợp được |

---

# PHẦN 12 — FIGURE & TABLE PLAN

## Figures cần có trong paper

| Figure | Nội dung | Cần dữ liệu gì | Script | Fallback |
|--------|----------|----------------|--------|---------|
| **Fig 1: Architecture** | Diagram: frames → clips → encoder → predictor → score → threshold | Không cần experiment | `draw.io` hoặc `matplotlib` | ASCII art trong paper |
| **Fig 2: Score Timeline** | Score theo thời gian với glitch interval marked | scores.csv + labels.csv | `plot_scores.py` mở rộng | Hiện tại plot_scores.py chưa vẽ GT intervals |
| **Fig 3: Qualitative Examples** | 2-4 frames từ glitch clip với cao score | TempGlitch frames | Manual selection | Dùng synthetic dynamics frames |
| **Fig 4: Per-category Breakdown** | Bar chart F1 theo 5 glitch categories | Per-category metrics | `matplotlib` bar chart | Skip nếu không có category labels |

### Cải tiến cần làm cho `plot_scores.py`:
```python
# Thêm argument: --labels để overlay glitch intervals lên plot
# Thêm shading cho glitch intervals
# Thêm dotted line cho threshold
```

## Tables cần có trong paper

| Table | Nội dung | Cần dữ liệu gì | Format | Fallback |
|-------|----------|----------------|--------|---------|
| **Table 1: Dataset Summary** | Tên dataset, #videos, #glitch types, temporal labels? | Từ TempGlitch paper | Markdown → LaTeX | Dùng GlitchBench stats |
| **Table 2: Main Results** | AUROC, F1, Precision, Recall × {frame_diff, feature_dist, mini_latent} | outputs/metrics.json | LaTeX tabular | CSV export |
| **Table 3: Ablation — Smoothing** | AUROC/F1 với window ∈ {1,3,5,9} | Ablation experiments | LaTeX | Inline trong text |
| **Table 4: Ablation — Latent Dim** | AUROC vs latent_dim | Ablation experiments | LaTeX | Inline trong text |
| **Table 5: Inference Efficiency** | FPS, VRAM, latency × methods | `time` command | LaTeX | Chỉ report FPS |

---

# PHẦN 13 — PAPER WRITING ROADMAP

**Viết theo thứ tự này (không phải thứ tự section trong paper):**

## Bước 1: Problem Formulation (Ngày 26-27/06)

- **Mục tiêu:** Định nghĩa formal bài toán.
- **Nội dung:** Input = clip sequence. Output = anomaly score. Label = binary. Formal definition.
- **Độ dài đề xuất:** 0.5 cột.
- **Reviewer attack:** "Sao không dùng frame-level annotation?" → defense: clip-level đủ cho detection task.

## Bước 2: Related Work (Ngày 27-28/06)

- **Mục tiêu:** Position work so với literature.
- **4 subsections:** (1) Game bug detection. (2) Video anomaly detection. (3) JEPA/latent world models. (4) Temporal game glitch benchmarks.
- **Evidence cần:** Ít nhất 8 cited papers với verified URLs.
- **Độ dài:** 1-1.5 cột.
- **Reviewer attack:** "Related work incomplete" → cite GlitchBench, TempGlitch, World of Bugs, VideoGlitchBench, LeWM, V-JEPA, future-frame prediction (Liu 2018).

## Bước 3: Methodology (Ngày 28-29/06)

- **Mục tiêu:** Mô tả pipeline, method.
- **Nội dung:** Preprocessing. Latent encoding (PCA). Transition model. Scoring. Thresholding.
- **Figure:** Architecture diagram.
- **Độ dài:** 1.5-2 cột.
- **Reviewer attack:** "PCA không phải world model" → defense: "lightweight proxy for testing the latent dynamics hypothesis; full LeWM integration deferred."

## Bước 4: Experimental Setup (Ngày 29-30/06)

- **Mục tiêu:** Reproducible setup.
- **Nội dung:** Dataset (TempGlitch), splits, hyperparameters, compute environment, evaluation protocol.
- **Không được:** Claim train/test split không rõ.
- **Độ dài:** 0.5-1 cột.

## Bước 5: Results (Ngày 30/06-01/07)

- **Mục tiêu:** Main quantitative results.
- **Table:** Main results table.
- **Text:** Highlight key findings. Không overclaim.
- **Độ dài:** 1 cột.

## Bước 6: Ablation (Ngày 01/07)

- **Mục tiêu:** Justify design choices.
- **Nội dung:** Smoothing ablation + latent dim ablation.
- **Độ dài:** 0.5-1 cột.

## Bước 7: Discussion (Ngày 02/07)

- **Mục tiêu:** Interpret results, failure cases.
- **Nội dung:** Khi nào latent approach tốt hơn. Khi nào frame_diff đủ. False positives from high-motion.
- **Độ dài:** 0.5 cột.

## Bước 8: Limitations (Ngày 02/07)

- **Nội dung:** Linear proxy. Dataset. No full LeWM integration. GPU requirements for real LeWM.
- **Độ dài:** 3-5 câu.

## Bước 9: Abstract (Ngày 03/07)

- **Viết sau** khi có results — dễ hơn khi biết kết quả thực.
- **Cấu trúc:** Problem (1 câu). Gap (1 câu). Method (2 câu). Results (2 câu). Significance (1 câu).
- **Độ dài:** 150-200 từ.

## Bước 10: Introduction (Ngày 03-04/07)

- **Nội dung:** Motivation → Problem → Gap → Contribution. Không để intro dài hơn 1 cột.
- **Reviewer attack:** "Motivation không rõ" → cite số liệu industry về game bugs.

## Bước 11: Conclusion (Ngày 04/07)

- **Nội dung:** Summarize. Không add thông tin mới. Future work: LeWM integration, cross-game generalization.

---

# PHẦN 14 — REVIEWER DEFENSE PLAN

| Reviewer concern | Tại sao họ hỏi | Defense | Evidence cần | Nếu thiếu evidence |
|-----------------|----------------|---------|--------------|-------------------|
| "Dataset có public không?" | Reproducibility concern | "TempGlitch: code and data at project website (Yu et al., 2026). GlitchBench: HuggingFace public." | URLs verify được | Thêm footnote: "accessed June 2026" |
| "Tại sao không dùng VLM?" | TempGlitch paper dùng VLM | "VLMs near chance on TempGlitch (Yu et al. show this). Our lightweight approach is 10-100x faster." | TempGlitch paper results | Cite paper; dùng inference speed comparison |
| "Tại sao latent tốt hơn pixel?" | Fundamental question | "Pixel baselines confuse high-motion normal gameplay with glitches. Latent error captures dynamics violation." | AUROC gap trên TempGlitch | Analysis of failure cases |
| "Có data leakage không?" | Evaluation concern | "Threshold selected on validation videos; test videos held out. Split by video, not clip." | Clear description trong paper | Thêm pseudocode cho split procedure |
| "Kết quả có hơn baseline không?" | Main claim | Report exact numbers; không overclaim | Final metrics table | Honest về khi nào không hơn |
| "Nếu không hơn VLM thì contribution ở đâu?" | Fair question | "Contribution là: reproducible pipeline, lightweight CPU-deployable method, latent dynamics analysis for temporal glitches." | Pipeline + ablation | Emphasize pipeline + analysis |
| "Có quá phụ thuộc vào 1 dataset không?" | Generalizability | "Additionally validated on GlitchBench image subset and synthetic dynamics data." | 2+ dataset results | Synthetic results clearly labeled |
| "Chạy real-time thật không?" | Practical claim | Report FPS explicitly; "mini_latent runs at Xfps on CPU" | `time` measurement | Không claim "real-time" nếu không đo |
| "Mô hình phát hiện loại bug nào?" | Scope concern | "Focused on temporal glitches: teleport, freeze, physics violation, flicker. Not semantic/logic bugs." | Per-category results | Per-category analysis trong Ablation |
| "PCA không phải JEPA" | Method concern | "We present PCA proxy as hypothesis validation. Full JEPA integration is left as future work." | Honest framing trong paper | Clear limitation statement |

---

# PHẦN 15 — RISK REGISTER & BACKUP PLAN

| Risk | Probability | Impact | Early Warning Sign | Mitigation | Backup Plan | Decision Point |
|------|-------------|--------|-------------------|------------|-------------|----------------|
| TempGlitch không tải được | Medium | High | Project website down, authors không respond | Email authors ngay (12/06), search GitHub | GlitchBench + World of Bugs làm primary | 15/06: nếu chưa có data → switch |
| LeWM code quá khó tích hợp | High | Medium | OOM, API mismatch, 3+ ngày không xong | Stage-by-stage audit, CPU test trước | mini_latent làm primary method | 02/07: nếu chưa có lewm scores → skip |
| OOM GPU trên T4/P100 | Medium | Medium | CUDA OOM error | Giảm batch size, giảm image_size, FP16 | mini_latent CPU mode | Ngay khi gặp OOM |
| Results thấp hơn frame_diff | Medium | High | AUROC < 0.5 cho mini_latent | Debug label alignment, tune hyperparams | Vẫn report, phân tích failure modes | Sau 20/06 |
| False positives do scene cut | High | Low | Spikes ở mọi scene transition | Scene cut detection, temporal smoothing | Thêm pre-filtering step | Sau Phase 3 |
| Không đủ thời gian VLM baseline | High | Low | Sau 10/07 không có VLM results | Cite TempGlitch paper VLM results | Skip VLM; cite từ paper | 05/07 |
| Không đủ số liệu claim real-time | Medium | Low | FPS < 5 | Optimize code, report as "CPU-deployable" | Không claim real-time | 30/06 |
| Citation source không verify được | Low | High | Broken URL | Verify mọi URL trước khi cite | Dùng arXiv persistent URL | Khi viết references |
| Paper scope quá rộng | High | High | Phần Method quá dài, contributions mơ hồ | Scope check hàng tuần | Cut scope mạnh, focus TempGlitch + 3 baselines | 01/07 |
| FISAT submission system lỗi | Low | High | Portal down gần deadline | Submit sớm (19/07), backup PDF | Email organizer ngay | 19/07 |

---

# PHẦN 16 — DEFINITION OF DONE

## Minimum Viable FISAT Submission

```
[ ] docs/research/ có đủ các file:
    [ ] 00_research_overview.md
    [ ] 01_problem_statement.md
    [ ] 02_literature_matrix.md (không còn TBD quan trọng)
    [ ] 04_dataset_benchmark_map.md (TempGlitch confirmed)
    [ ] 05_methodology_v0.md
    [ ] 06_experiment_plan.md
    [ ] 07_baseline_plan.md
    [ ] 08_reproducibility_checklist.md (filled out)
    [ ] 09_risks_and_limitations.md
    [ ] 10_paper_outline.md
    [ ] 12_experiment_results_log.md (actual numbers)

[ ] Baseline experiments:
    [ ] frame_diff trên TempGlitch (hoặc GlitchBench): metrics.json exist
    [ ] feature_distance trên TempGlitch: metrics.json exist
    [ ] mini_latent trên TempGlitch: metrics.json exist
    [ ] outputs/baseline_comparison.md exist

[ ] Results:
    [ ] Ít nhất 1 baseline có AUROC > 0.5
    [ ] Ablation table ≥ 2 rows

[ ] Figures:
    [ ] Architecture diagram (SVG hoặc PNG)
    [ ] Score timeline plot ≥ 1 example

[ ] Paper:
    [ ] paper/main.tex compilable
    [ ] paper/main.pdf ≥ 6 trang
    [ ] Springer format (LNCS)
    [ ] Tiếng Anh
    [ ] References đủ và verified

[ ] Code:
    [ ] README.md có reproduction commands
    [ ] GitHub repo clean (không commit data/outputs/checkpoints)
    [ ] Tests pass (hoặc skip documented)
    [ ] AGENTS.md updated

[ ] Submission:
    [ ] slides/ có presentation ≥ 10 trang
    [ ] Submit lên EAI system trước 20/07/2026 23:59 AoE
```

## Strong Paper Version (nếu còn thời gian)

```
[ ] Real LeWM integration với checkpoint
[ ] VideoGlitchBench subset (≥ 100 videos) results
[ ] CNN-LSTM baseline results
[ ] Event-level Macro-F1 và temporal mIoU (nếu TempGlitch có temporal spans)
[ ] Inference FPS table (CPU vs GPU)
[ ] Qualitative examples table (≥ 4 glitch types với score visualization)
[ ] Cross-game generalization experiment
[ ] Reproducibility: DVC hoặc MLflow cho experiment tracking
```

---

# PHẦN 17 — IMMEDIATE NEXT ACTIONS (48h)

Dưới đây là **10 việc phải làm ngay trong 48 giờ tới** (08-10/06/2026):

---

### Action 1: Environment Verify
**Thời lượng:** 30 phút
```bash
cd glitch-world-model
git pull origin main
git submodule update --init
python -m pip install -e .[dev]
python -m pytest
python scripts/run_synthetic_demo.py
```
**Output:** pytest kết quả (pass/fail). `outputs/synthetic_scores.csv`.
**Tiêu chí hoàn thành:** pytest không có lỗi import. F1 > 0 trên synthetic demo.

---

### Action 2: Run Existing Dynamics Experiments
**Thời lượng:** 30 phút
```bash
python scripts/run_dynamics_experiments.py
python scripts/run_hard_dynamics_experiments.py
python scripts/summarize_all_experiments.py
```
**Output:** `outputs/summary_all_experiments.md` với F1 và AUROC cho tất cả baselines.
**Tiêu chí:** File tồn tại. MiniLatent có F1 > 0.5 trên dynamics easy.

---

### Action 3: Find TempGlitch Project Website
**Thời lượng:** 30 phút
```bash
# Tìm project website từ paper
curl -s "https://arxiv.org/abs/2605.21443" | grep -i "github\|project\|homepage\|data"
# Hoặc fetch HTML
```
**Output:** TempGlitch project URL trong `docs/research/11_tempglitch_integration_plan.md`.
**Tiêu chí:** URL tìm được. Check accessibility.

---

### Action 4: Create tempglitch_integration_plan.md
**Thời lượng:** 30 phút

Tạo file `docs/research/11_tempglitch_integration_plan.md` với:
- TempGlitch URL (nếu đã tìm được)
- Annotation format dự kiến
- Conversion plan sang labels.csv
- Command sẽ chạy

**Output:** File tồn tại với đầy đủ sections.
**Tiêu chí:** File không có mục nào trống mà chỉ viết "TBD" — phải có best guess hoặc question.

---

### Action 5: Download TempGlitch (nếu available)
**Thời lượng:** 1-2 giờ (bao gồm download time)

```bash
# Tùy URL từ Action 3
# Ví dụ nếu là HuggingFace:
# pip install datasets
# python -c "from datasets import load_dataset; ds = load_dataset('...')"
# Ví dụ nếu là GitHub:
# git clone https://github.com/.../tempglitch
```
**Output:** `data/raw/tempglitch/` với ít nhất sample videos/frames.
**Tiêu chí:** Ít nhất 10 videos/clips có thể inspect được.
**Fallback nếu không tải được:** Chạy GlitchBench: `python scripts/download_glitchbench_subset.py --limit 24`

---

### Action 6: Inspect TempGlitch Format
**Thời lượng:** 30 phút

Sau khi tải, chạy:
```bash
ls data/raw/tempglitch/
# Identify: video files? frame folders? annotation JSON/CSV?
head -20 data/raw/tempglitch/annotations.csv  # hoặc tương tự
```
**Output:** `docs/research/11_tempglitch_integration_plan.md` update với format thực tế.
**Tiêu chí:** Biết được annotation format và conversion plan.

---

### Action 7: Create run_tempglitch_experiments.py Script
**Thời lượng:** 1 giờ

```python
# scripts/run_tempglitch_experiments.py
# Clone từ scripts/run_dynamics_experiments.py
# Điều chỉnh:
# - input_path = ROOT / "data" / "raw" / "tempglitch_frames"
# - labels_path = ROOT / "data" / "raw" / "tempglitch_labels.csv"
# - experiments = [("TempGlitchFrameDiff", ...), ("TempGlitchFeature", ...), ("TempGlitchMiniLatent", ...)]
```
**Output:** `scripts/run_tempglitch_experiments.py` chạy được.
**Tiêu chí:** Script không crash khi import. Chạy được trên synthetic data test.

---

### Action 8: Update Literature Matrix
**Thời lượng:** 1 giờ

```bash
# Verify từng URL trong docs/research/02_literature_matrix.md
# TempGlitch: arxiv.org/abs/2605.21443 ✓
# VideoGlitchBench: arxiv.org/abs/2604.07818 ✓
# GlitchBench: arxiv.org/abs/2312.05291 ✓
# LeWM: arxiv.org/abs/2603.19312 → verify
# World of Bugs: arxiv.org/abs/2206.11037 → verify
```
**Output:** `docs/research/02_literature_matrix.md` với TBD → confirmed/not-available.
**Tiêu chí:** ≥ 5 papers verified. Không còn TBD cho papers quan trọng.

---

### Action 9: Create experiment_results_log.md
**Thời lượng:** 20 phút

Tạo `docs/research/12_experiment_results_log.md`:
```markdown
# Experiment Results Log
## Date: 2026-06-08

### Dynamics Easy (synthetic)
| Scorer | F1 | AUROC | Note |
| FrameDiff | [paste from summary] | ... | |
| FeatureDistance | ... | ... | |
| MiniLatent | ... | ... | |

### Hard Dynamics (synthetic)
...

### TempGlitch (TODO — pending download)
...
```
**Output:** File với kết quả synthetic đã có.
**Tiêu chí:** Tất cả synthetic results được paste vào. TempGlitch section là "TODO".

---

### Action 10: Plan 6-week Sprint Calendar
**Thời lượng:** 20 phút

Tạo `docs/research/15_sprint_calendar.md`:
```markdown
# 6-Week Sprint to FISAT 2026

| Week | Dates | Focus | Must Complete |
|------|-------|-------|---------------|
| 1 | 08-14/06 | TempGlitch setup | Dataset accessible |
| 2 | 15-21/06 | Baseline results | 3 baselines on TempGlitch |
| 3 | 22-28/06 | Ablation + LeWM audit | Ablation table |
| 4 | 29/06-05/07 | Figures + consolidation | All figures for paper |
| 5 | 06-12/07 | Paper writing | Draft 6 pages |
| 6 | 13-20/07 | Polish + submit | Submit 20/07 |
```
**Output:** Calendar file committed.
**Tiêu chí:** File tồn tại với dates và milestones rõ ràng.

---

# APPENDIX: Lưu Ý Quan Trọng

## Về FISAT Formatting
- Template: Springer LNCS (không phải ACM). Tải tại: `https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines`
- Language: **Tiếng Anh** (bắt buộc).
- Length: Thường 10-15 trang cho full paper. Với student research, 6-8 trang là tốt.
- Submit qua EAI online system: `https://daihoc.fpt.edu.vn/hcm/fisat/`
- Indexed: Scopus Q4 (EAI/Springer Innovations in Communication and Computing, ISSN 2522-8609).

## Về Presentation tại Conference
- Accepted papers must be presented (oral or poster) — November 25-27, 2026.
- Submit camera-ready final paper by October 15, 2026 sau khi accept (September 15).

## Về Repo Hygiene
- Không commit: data/, outputs/, checkpoints, .test-tmp/
- Commit: docs/research/, scripts/, src/, tests/, paper/ (chỉ .tex và .bib, không .pdf lớn)
- Dùng `outputs/.gitkeep` và `data/.gitkeep`

## Về Claim Integrity
- Nếu AUROC thấp: vẫn report trung thực. Contribute là pipeline + analysis, không phải SOTA.
- Nếu mini_latent tệt hơn frame_diff: phân tích tại sao. Contribution vẫn có giá trị.
- Không viết "state-of-the-art" trừ khi có số liệu so sánh trực tiếp trên cùng benchmark.

---

*Document này được tạo ngày 08/06/2026 dựa trên báo cáo phân tích chi tiết và toàn bộ codebase hiện tại của repo glitch-world-model. Cập nhật kết quả thực nghiệm vào `docs/research/12_experiment_results_log.md` sau mỗi lần chạy experiment.*
