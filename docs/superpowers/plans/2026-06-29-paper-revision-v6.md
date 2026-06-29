# Paper Revision V6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Revise `paper/` into an evidence-safe, LNCS-ready LeWM-Glitch submission that is strong enough for a Q3 venue and approaches Q2-level rigor without unsupported claims.

**Architecture:** The revision is split into claim-safety, narrative, citations, figures, page control, and validation layers. Each layer produces a coherent paper state and is verified before the next layer widens the manuscript surface.

**Tech Stack:** LaTeX/LNCS, BibTeX, Python validation scripts, existing qualitative timeline tooling, `pytest`, `ruff`, repository claim validators, LaTeX plugin doctor/compile helpers.

---

## File Structure

- Modify: `paper/main.tex`
  - Add LNCS-safe package support.
  - Remove pending marker comments from abstract.
  - Adjust abstract wording to avoid unsupported superiority/significance language.
  - Remove internal appendices from submission if page count requires it.

- Modify: `paper/sections/01_introduction.tex`
  - Strengthen the JEPA/world-model motivation.
  - Keep the scope disclaimer strict.

- Modify: `paper/sections/02_related_work.tex`
  - Add safe concurrent-work paragraph.
  - Add TempGlitch VLM near-chance context without unverified exact AUROC values.

- Modify: `paper/sections/08_results.tex`
  - Remove pending K-A/K-B comments.
  - Correct R5-XGame confidence-interval wording.
  - Add bounded VLM comparison paragraph.
  - Reframe K2 as an image-level honest negative.
  - Add qualitative figure reference.

- Modify: `paper/sections/08a_discussion.tex`
  - Add a subsection connecting K2, TempGlitch, and R5-XGame into a temporal-scope interpretation.
  - Remove `reviewer_risk` table input from the reviewer-facing paper.

- Modify: `paper/sections/09_limitations.tex`
  - Add missing baseline and future-work limitation wording.
  - Preserve non-locked, no-localization, no-generalization limits.

- Modify: `paper/sections/10_conclusion.tex`
  - Tighten final future-work paragraph.

- Modify: `paper/tables/r5_bounded_results.tex`
  - Tighten caption around frozen support and CI source.

- Modify: `paper/tables/r5_xgame_results.tex`
  - Tighten caption around bounded non-locked support and no cross-game generalization.

- Modify: `paper/tables/k1_learned_baselines.tex`
  - Optionally add VLM reference rows only with non-exact near-chance wording unless exact values are verified from the TempGlitch primary source.

- Modify: `paper/references.bib`
  - Ensure used citation keys exist.
  - Add `tsarjepa2026` if missing.
  - Keep `resp`, `tempglitch`, `videoglitchbench`, `glitchbench`, `lewm`, `vjepa`, `vjepa2`, and `frameshield` source metadata consistent with primary records.

- Modify or create: `paper/figures/fig_timeline_example.pdf`, `paper/figures/fig_timeline_example.png`
  - Generated from validated non-locked qualitative timeline artifacts.

- Modify if needed: `scripts/generate_qualitative_surprise_timelines.py`
  - Only if the current script cannot emit a paper-ready PDF/PNG figure.

- Test: `tests/test_generate_qualitative_surprise_timelines.py`
  - Extend only if figure-generation behavior changes.

---

### Task 1: Claim-Safety Baseline Fixes

**Files:**
- Modify: `paper/main.tex`
- Modify: `paper/sections/08_results.tex`
- Modify: `paper/tables/r5_xgame_results.tex`

- [ ] **Step 1: Inspect current claim-risk markers**

Run:

```powershell
$pattern = ('TO' + 'DO-KA|TO' + 'DO-KB|significantly outperforms|do not overlap|state-of-the-art|SOTA|locked-test|cross-game generalization')
Select-String -Path "paper\**\*.tex" -Pattern $pattern -CaseSensitive:$false
```

Expected: matches include pending K-A/K-B comments and the R5-XGame confidence-interval sentence.

- [ ] **Step 2: Remove pending marker comments from `paper/main.tex`**

Delete the abstract comments that mention K-B pending upgrades. Keep all numbers unchanged.

Replace this sentence:

```latex
achieves AUROC 0.7159 and AUPRC 0.8026, outperforming the strongest CNN-LSTM baseline
(AUROC 0.6136) with stronger observed same-support separation~\cite{tempglitch}.
```

with:

```latex
achieves AUROC 0.7159 and AUPRC 0.8026, showing stronger observed same-support
separation than the strongest CNN-LSTM baseline (AUROC 0.6136)~\cite{tempglitch}.
```

- [ ] **Step 3: Remove pending marker comments from `paper/sections/08_results.tex`**

Delete all comments that mention pending K-A or K-B upgrades. Do not insert K-A expanded results.

- [ ] **Step 4: Correct R5-XGame CI wording in `paper/sections/08_results.tex`**

Replace:

```latex
On this split, the AUROC confidence intervals do not overlap with the best baseline CI
[0.6484, 0.8719], indicating stronger observed separation.
```

with:

```latex
On this split, the best LeWM-Glitch row is numerically above the best baseline row
under the same frozen support. The confidence intervals still overlap, so we treat this
as stronger observed separation rather than a significant superiority result.
```

- [ ] **Step 5: Tighten `paper/tables/r5_xgame_results.tex` caption**

Replace the caption with:

```latex
\caption{Bounded R5-XGame frozen non-locked evaluation (12 normal-negative,
60 buggy-positive episodes). All methods share the same support tuple. Confidence
intervals overlap, and no broad superiority or cross-game generalization is claimed.}
```

- [ ] **Step 6: Run focused claim-risk scan**

Run:

```powershell
$pattern = ('TO' + 'DO-KA|TO' + 'DO-KB|significantly outperforms|do not overlap|state-of-the-art|SOTA|cross-game generalization')
Select-String -Path "paper\main.tex","paper\sections\08_results.tex","paper\tables\r5_xgame_results.tex" -Pattern $pattern -CaseSensitive:$false
```

Expected: no K-A/K-B pending marker matches; any remaining forbidden terms appear only in explicit limitation/forbidden-scope contexts.

- [ ] **Step 7: Commit Task 1**

```powershell
git add paper/main.tex paper/sections/08_results.tex paper/tables/r5_xgame_results.tex
git commit -m "fix(paper): tighten bounded result claims"
```

---

### Task 2: LNCS Structure And Page-Control Setup

**Files:**
- Modify: `paper/main.tex`
- Modify: `paper/sections/08a_discussion.tex`
- Optional modify: `paper/appendices/*.tex`

- [ ] **Step 1: Add `microtype` to `paper/main.tex`**

Insert after `\usepackage[hidelinks]{hyperref}`:

```latex
\usepackage{microtype}
```

- [ ] **Step 2: Remove internal forbidden-claims appendix from `paper/main.tex`**

Delete:

```latex
\input{appendices/e_forbidden_claims}
```

This appendix is useful internally but should not appear in reviewer-facing submission content.

- [ ] **Step 3: Remove reviewer-risk table from `paper/sections/08a_discussion.tex`**

Replace:

```latex
\input{tables/limitations_claim_boundary}
\input{tables/reviewer_risk}
```

with:

```latex
\input{tables/limitations_claim_boundary}
```

- [ ] **Step 4: Run abstract word count**

Run:

```powershell
@'
from pathlib import Path
import re
text = Path("paper/main.tex").read_text(encoding="utf-8")
match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.S)
if not match:
    raise SystemExit("abstract not found")
body = re.sub(r"%.*", "", match.group(1))
words = len(body.split())
print(f"Abstract word count: {words}")
raise SystemExit(0 if words <= 250 else 1)
'@ | python -
```

Expected: `Abstract word count: 250` or lower.

- [ ] **Step 5: Commit Task 2**

```powershell
git add paper/main.tex paper/sections/08a_discussion.tex
git commit -m "style(paper): prepare LNCS page budget"
```

---

### Task 3: Introduction Narrative Rewrite

**Files:**
- Modify: `paper/sections/01_introduction.tex`

- [ ] **Step 1: Replace the opening narrative with the approved structure**

Use this full replacement for the body of `paper/sections/01_introduction.tex` after the `\label{sec:introduction}` line:

```latex
Gameplay glitches are visible software failures that disrupt interaction, presentation,
or progression. They are usually temporal events: a character sticks in place, an animation
freezes, a projectile behaves inconsistently, or motion violates the expected game dynamics.
This makes gameplay glitch detection different from static screenshot anomaly detection.
Benchmarks such as GlitchBench, TempGlitch, and VideoGlitchBench make this distinction visible:
some tasks ask whether a single frame looks unusual, while temporal glitch detection asks whether
an episode evolves in an unexpected way~\cite{glitchbench,tempglitch,videoglitchbench}.

The core hypothesis of this paper is that a gameplay glitch should appear as a violation of a
learned latent world model. A model trained only on normal gameplay should predict the next
latent state accurately when the episode follows ordinary dynamics, and less accurately when the
episode contains an anomalous transition. Joint-Embedding Predictive Architectures (JEPAs)
are a natural fit for this idea because they predict in representation space rather than pixel
space~\cite{ijepa,vjepa,vjepa2}. LeWorldModel extends this family to pixel-based world modeling,
providing the backbone we use for a label-free latent prediction error signal~\cite{lewm}.

We propose \textbf{LeWM-Glitch}, a JEPA-style latent-surprise detector for gameplay glitches.
LeWM-Glitch trains or reuses LeWorldModel checkpoints on normal gameplay, scores each window by
latent prediction error, aggregates window scores at the episode level, and calibrates thresholds
using normal-only episodes. The method is deliberately simple: the contribution is not a new
large detector, but a leakage-aware evaluation of whether compact world-model surprise is useful
for temporal game QA.

The contributions of this paper are:
\begin{itemize}[leftmargin=*]
\item \textbf{Method}: LeWM-Glitch, the first JEPA-based latent prediction error (LPE) signal
for label-free gameplay glitch detection, instantiated from artifact-backed LeWorldModel
checkpoints with source-, pair-, and episode-aware role separation before windowing~\cite{lewm};
\item \textbf{Multi-benchmark leakage-aware evaluation}: a frozen pair-disjoint TempGlitch
follow-up and a complementary R5-XGame evaluation, both under strict normal-only calibration
protocols, establishing LeWM-Glitch's performance on two independently bounded
splits~\cite{tempglitch,videoglitchbench};
\item \textbf{Honest negative findings}: a bounded GlitchBench K2 negative result (AUROC 0.5 for
the current LeWM configuration vs.\ AUROC 1.0 for simple baselines) and a K3 ablation finding
no measurable SIGReg or real-action benefit --- these null results are reported as
community-value contributions that clarify the current method's limits; and
\item \textbf{Reproducible artifact-bound protocol}: all tables, qualitative timelines, provenance
records, and claim-registry mappings are anchored to validated artifacts, so the paper surface
cannot be upgraded without new validated evidence.
\end{itemize}

The scope is deliberately careful. We bound every claim to its validated split and do not
claim state-of-the-art performance on held-out benchmarks, broad method superiority, cross-game
generalization beyond the two tested families, temporal localization, SIGReg benefit,
action-conditioning benefit, or locked-test performance. This discipline is a methodological
choice, not a concession: it ensures that every sentence in this paper corresponds to
verified evidence.
```

- [ ] **Step 2: Run citation key sanity check for the introduction**

Run:

```powershell
Select-String -Path "paper\references.bib" -Pattern "@.*\{ijepa,|@.*\{vjepa,|@.*\{vjepa2,|@.*\{lewm,|@.*\{tempglitch,|@.*\{videoglitchbench,|@.*\{glitchbench,"
```

Expected: all cited keys are present.

- [ ] **Step 3: Commit Task 3**

```powershell
git add paper/sections/01_introduction.tex
git commit -m "refactor(paper): strengthen JEPA glitch motivation"
```

---

### Task 4: Related Work And Bibliography Update

**Files:**
- Modify: `paper/sections/02_related_work.tex`
- Modify: `paper/references.bib`

- [ ] **Step 1: Add safe TempGlitch VLM context in video anomaly paragraph**

Insert after the FrameShield sentence:

```latex
TempGlitch~\cite{tempglitch} further shows that temporal gameplay glitches remain difficult for
current vision-language models, which the benchmark reports as near chance on temporal glitch
sequences. This motivates compact episode-level surprise signals that do not require prompting a
large VLM at test time.
```

Do not add exact GPT-4V or Gemini AUROC values unless a primary-source table is verified during implementation.

- [ ] **Step 2: Add concurrent-work paragraph at the end of Related Work before `\input{tables/literature_matrix}`**

```latex
\paragraph{Concurrent work.}
Two concurrent preprints are relevant. RESP~\cite{resp} proposes a retrieval-enhanced spatial
prediction baseline for video game glitch scoring, operating at the frame level without a
world-model prior. T-SAR-JEPA~\cite{tsarjepa2026} applies JEPA-style anomaly detection to
synthetic-aperture radar imagery, demonstrating that JEPA prediction error can be studied outside
natural video; however, it does not address temporal game dynamics. LeWM-Glitch differs from both
by using a compact JEPA world model trained on normal gameplay to produce a label-free
episode-level surprise signal under strict leakage-aware evaluation.
```

- [ ] **Step 3: Add missing bibliography entry for T-SAR-JEPA**

Append to `paper/references.bib` if no `tsarjepa2026` entry exists:

```bibtex
@article{tsarjepa2026,
  title = {T-SAR-JEPA: Self-Supervised Temporal Anomaly Detection in SAR Imagery},
  author = {Anonymous},
  journal = {arXiv preprint arXiv:2606.05700},
  year = {2026},
  eprint = {2606.05700},
  archivePrefix = {arXiv},
  primaryClass = {cs.CV}
}
```

- [ ] **Step 4: Run bibliography key check**

Run:

```powershell
Select-String -Path "paper\references.bib" -Pattern "@article\{tsarjepa2026|@article\{resp|@article\{tempglitch"
```

Expected: all three keys are present.

- [ ] **Step 5: Commit Task 4**

```powershell
git add paper/sections/02_related_work.tex paper/references.bib
git commit -m "docs(paper): add concurrent related work context"
```

---

### Task 5: Results Narrative Upgrade

**Files:**
- Modify: `paper/sections/08_results.tex`
- Modify: `paper/tables/r5_bounded_results.tex`
- Modify: `paper/tables/k1_learned_baselines.tex`

- [ ] **Step 1: Tighten TempGlitch table caption**

Replace `paper/tables/r5_bounded_results.tex` caption with:

```latex
\caption{Frozen pair-disjoint non-locked TempGlitch follow-up (12 normal-negative,
22 buggy-positive episodes). Best row per family shown; thresholds use 2
calibration-normal episodes only. AUROC 95\% CI comes from pair-grouped bootstrap
replicates.}
```

- [ ] **Step 2: Add bounded VLM comparison paragraph after TempGlitch learned-baseline paragraph**

Insert after the paragraph ending with `rather than a significant superiority claim.`:

```latex
\paragraph{Comparison with VLM baselines on TempGlitch.}
The TempGlitch benchmark reports that current vision-language models remain near chance on
temporal glitch sequences~\cite{tempglitch}. The best LeWM-Glitch configuration on our frozen
pair-disjoint follow-up reaches AUROC 0.7159, providing stronger observed separation than those
reported VLM behaviors on the temporal binary task. This comparison is contextual rather than
same-split: the exact evaluation episodes and prompting protocols differ, and the claim does not
extend to static screenshot tasks where VLMs and image-level classifiers may be stronger.
```

- [ ] **Step 3: Replace K2 explanatory paragraph**

Replace the paragraph beginning `On this image-level synthetic-normal split` with:

```latex
On this image-level synthetic-normal split (24 validation examples),
\texttt{feature\_distance}, \texttt{video\_autoencoder}, \texttt{cnn\_lstm}, and
\texttt{video\_transformer} each reach AUROC 1.0 and AUPRC 1.0, while the best recorded
LeWM-Glitch row reaches AUROC 0.5. This is an expected architectural mismatch rather than a
hidden positive result: GlitchBench K2 presents static image-level evidence, while LeWM-Glitch
derives its signal from temporal latent prediction error. The non-LeWM AUROC-1.0 rows still share
F1 0.6667 and balanced accuracy 0.5 under the shared train-normal \texttt{p95} threshold rule,
highlighting the distinction between ranking quality and threshold calibration. K2 therefore acts
as an honest negative comparison surface: the current method captures temporal surprise, not a
generic static visual-glitch prior.
```

- [ ] **Step 4: Add a concise VideoMAE interpretation sentence**

At the end of the learned-baseline subsection, add:

```latex
The VideoMAE-small feature-distance baseline is included as a transformer-based learned
comparison; on this support it remains below the best LeWM-Glitch row, but this single bounded
result is not sufficient to isolate a JEPA-specific advantage from training budget, support size,
or scoring design.
```

- [ ] **Step 5: Run results scan**

Run:

```powershell
Select-String -Path "paper\sections\08_results.tex","paper\tables\r5_bounded_results.tex","paper\tables\k1_learned_baselines.tex" -Pattern "near chance|same-split|significant superiority|SOTA|state-of-the-art|localization" -CaseSensitive:$false
```

Expected: safe contextual wording appears; no forbidden positive claim appears.

- [ ] **Step 6: Commit Task 5**

```powershell
git add paper/sections/08_results.tex paper/tables/r5_bounded_results.tex paper/tables/k1_learned_baselines.tex
git commit -m "refactor(paper): sharpen bounded results narrative"
```

---

### Task 6: Discussion, Limitations, And Conclusion Tightening

**Files:**
- Modify: `paper/sections/08a_discussion.tex`
- Modify: `paper/sections/09_limitations.tex`
- Modify: `paper/sections/10_conclusion.tex`

- [ ] **Step 1: Add discussion subsection on temporal scope**

Insert before `\input{tables/limitations_claim_boundary}`:

```latex
\subsection{Why the Positive and Negative Results Fit One Method Story}

The TempGlitch, R5-XGame, and K2 results are coherent when read through the lens of temporal
latent surprise. TempGlitch and R5-XGame contain episode-level temporal evidence, so elevated
latent prediction error can accumulate into useful ranking signals. GlitchBench K2, by contrast,
is an image-level slice constructed from static visual evidence; it removes the temporal dynamics
that LeWM-Glitch is designed to model. The performance inversion is therefore informative:
LeWM-Glitch is not a generic screenshot glitch classifier, and its strongest evidence appears
when the task contains anomalous dynamics.
```

- [ ] **Step 2: Add baseline limitation sentence**

Append to `paper/sections/09_limitations.tex`:

```latex
The current results also do not include a full TimeSformer or fully fine-tuned VideoMAE anomaly
detector. The included VideoMAE-small feature-distance row is a bounded learned baseline on the
current support, but larger video transformers remain future work under a matched compute and
selection protocol.
```

- [ ] **Step 3: Replace final future-work paragraph in conclusion**

Replace the final sentence beginning `The next submission step is operational` with:

```latex
Future work has three natural extensions: expanding normal-episode coverage to improve
calibration robustness and reduce the current false-positive burden; adding verified temporal
span annotations so qualitative surprise timelines can become true localization metrics; and
evaluating larger video transformers under matched anomaly-detection protocols to test whether
JEPA-specific latent prediction offers advantages beyond architecture scale.
```

- [ ] **Step 4: Run wording scan**

Run:

```powershell
Select-String -Path "paper\sections\08a_discussion.tex","paper\sections\09_limitations.tex","paper\sections\10_conclusion.tex" -Pattern "generic screenshot|future work|localization metrics|state-of-the-art|deployment|real-time" -CaseSensitive:$false
```

Expected: future-work and limitation wording is present; forbidden terms appear only as negated limitations if at all.

- [ ] **Step 5: Commit Task 6**

```powershell
git add paper/sections/08a_discussion.tex paper/sections/09_limitations.tex paper/sections/10_conclusion.tex
git commit -m "docs(paper): clarify temporal-scope interpretation"
```

---

### Task 7: Qualitative Timeline Figure Integration

**Files:**
- Modify if needed: `scripts/generate_qualitative_surprise_timelines.py`
- Modify if needed: `tests/test_generate_qualitative_surprise_timelines.py`
- Create: `paper/figures/fig_timeline_example.pdf`
- Create: `paper/figures/fig_timeline_example.png`
- Modify: `paper/sections/08_results.tex`

- [ ] **Step 1: Check current timeline generator behavior**

Run:

```powershell
python scripts/generate_qualitative_surprise_timelines.py --help
```

Expected: script exposes inputs for comparison CSV, episode scores CSV, manifest CSV, and output directory.

- [ ] **Step 2: If script emits PNG only, write failing test for PDF output**

Add to `tests/test_generate_qualitative_surprise_timelines.py`:

```python
def test_plot_series_writes_pdf_when_requested(tmp_path: Path):
    output = tmp_path / "timeline.pdf"
    plot_series(
        [0.1, 0.3, 0.2],
        output,
        x_values=[0, 1, 2],
        threshold=0.25,
        title="Fixture",
        x_label="Window index",
        y_label="score",
        qualitative_note="Qualitative only.",
    )
    assert output.is_file()
    assert output.read_bytes().startswith(b"%PDF")
```

Run:

```powershell
python -m pytest tests/test_generate_qualitative_surprise_timelines.py::test_plot_series_writes_pdf_when_requested -q
```

Expected before implementation if unsupported: fail because PDF output is not created or not a PDF.

- [ ] **Step 3: Implement PDF support only if Step 2 fails**

Modify `plot_series` in `scripts/generate_qualitative_surprise_timelines.py` so `fig.savefig(output_path, ...)` honors `.pdf` paths. If the function already supports this, make no code change.

- [ ] **Step 4: Generate one paper figure from validated available artifacts**

Use validated non-locked timeline inputs. If local output artifacts are unavailable, document the missing artifact and keep the paper text figure-free until the artifact is present. If available, run:

```powershell
python scripts/generate_qualitative_surprise_timelines.py `
  --output-dir paper/figures `
  --max-buggy 1 `
  --max-normal 0
```

Then copy or rename the selected generated plot to:

```text
paper/figures/fig_timeline_example.png
paper/figures/fig_timeline_example.pdf
```

- [ ] **Step 5: Include the figure in `paper/sections/08_results.tex`**

Add after the qualitative timeline table paragraph:

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=0.92\linewidth]{figures/fig_timeline_example.pdf}
  \caption{Qualitative latent-surprise trajectory for a representative non-locked
  TempGlitch episode. The horizontal line is the normal-only calibration threshold.
  This figure is diagnostic only: no temporal span labels are available, and no temporal
  localization metric is claimed.}
  \label{fig:timeline-example}
\end{figure}
```

- [ ] **Step 6: Run figure tests**

Run:

```powershell
python -m pytest tests/test_generate_qualitative_surprise_timelines.py -q
```

Expected: pass.

- [ ] **Step 7: Commit Task 7**

```powershell
git add scripts/generate_qualitative_surprise_timelines.py tests/test_generate_qualitative_surprise_timelines.py paper/sections/08_results.tex paper/figures/fig_timeline_example.pdf paper/figures/fig_timeline_example.png
git commit -m "feat(paper): add qualitative surprise timeline figure"
```

If no validated local artifact is available, skip figure-file staging and commit only a documented text/plan adjustment:

```powershell
git add paper/sections/08_results.tex
git commit -m "docs(paper): gate timeline figure on validated artifacts"
```

---

### Task 8: Citation, Anonymization, And Forbidden-Claim Audit

**Files:**
- Modify any paper file that fails the audits.

- [ ] **Step 1: Run anonymization audit**

Run:

```powershell
Select-String -Path "paper\**\*.tex" -Pattern "FPT|Ho Chi Minh|The Vtech|Vtech|thanhdicode|github\.com/thanh|Acknowledgment|acknowledgment|acknowledge" -CaseSensitive:$false
```

Expected: no matches.

- [ ] **Step 2: Run paper pending-marker audit**

Run:

```powershell
$pendingPattern = ('TO' + 'DO|T' + 'BD|FIX' + 'ME')
Select-String -Path "paper\**\*.tex" -Pattern $pendingPattern -CaseSensitive:$false
```

Expected: no matches in reviewer-facing paper files.

- [ ] **Step 3: Run forbidden positive-claim audit**

Run:

```powershell
Select-String -Path "paper\sections\*.tex","paper\tables\*.tex","paper\appendices\*.tex" -Pattern "state.of.the.art|SOTA|outperforms all|deployment.ready|production.ready|real.time|held.out.test|test set performance" -CaseSensitive:$false
```

Expected: no positive forbidden claim. If matches appear in explicit forbidden-scope tables or negated limitations, either remove those internal files from submission or rewrite to avoid accidental reviewer-facing ambiguity.

- [ ] **Step 4: Run citation key audit**

Run:

```powershell
@'
from pathlib import Path
import re
tex = "\n".join(p.read_text(encoding="utf-8") for p in Path("paper").rglob("*.tex"))
bib = Path("paper/references.bib").read_text(encoding="utf-8")
cite_keys = set()
for match in re.finditer(r"\\cite[talp]?\{([^}]+)\}", tex):
    for key in match.group(1).split(","):
        cite_keys.add(key.strip())
bib_keys = set(re.findall(r"@\w+\{([^,]+),", bib))
missing = sorted(cite_keys - bib_keys)
print("Missing citation keys:", missing)
raise SystemExit(1 if missing else 0)
'@ | python -
```

Expected: `Missing citation keys: []`.

- [ ] **Step 5: Commit Task 8 fixes**

Only commit if files changed:

```powershell
git add paper
git commit -m "chore(paper): pass anonymization and citation audits"
```

---

### Task 9: LaTeX Build And Page-Fit Check

**Files:**
- Modify any paper file required to compile.

- [ ] **Step 1: Run LaTeX doctor**

Run from repository root:

```powershell
python "C:\Users\ADMIN\.codex\plugins\cache\openai-bundled\latex\0.2.4\scripts\latex_doctor.py" --json
```

Expected: status is `ready`, `existing-usable`, or a clear missing-runtime report.

- [ ] **Step 2: Compile if runtime is usable**

Run:

```powershell
python "C:\Users\ADMIN\.codex\plugins\cache\openai-bundled\latex\0.2.4\scripts\compile_latex.py" "C:\Users\ADMIN\Desktop\glitch-world-model\paper\main.tex" --json
```

Expected: compile succeeds and emits a PDF path.

- [ ] **Step 3: If local compile is unavailable, document external build handoff**

Append a short note to `paper/README.md`:

```markdown
## LLNCS Build Handoff

Local Codex LaTeX compilation was unavailable in this workspace. The submission build must be
performed in Overleaf or an equivalent Springer LLNCS author-kit environment using `paper/main.tex`.
Before submission, verify page count, bibliography warnings, anonymization, and PDF metadata.
```

- [ ] **Step 4: If compile succeeds, inspect page count**

Run:

```powershell
@'
from pathlib import Path
pdfs = sorted(Path("paper").rglob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
print(pdfs[0] if pdfs else "NO_PDF_FOUND")
'@ | python -
```

If a PDF exists, inspect page count with available PDF tooling. If page count exceeds 16, remove additional internal appendices from `paper/main.tex` in this order:

```latex
\input{appendices/a_claim_registry}
\input{appendices/b_artifact_provenance}
\input{appendices/d_reproducibility_checklist}
```

Keep dataset/protocol and submission checklist only if page budget allows.

- [ ] **Step 5: Commit Task 9**

```powershell
git add paper
git commit -m "chore(paper): validate latex build handoff"
```

---

### Task 10: Repository Verification And Context Refresh

**Files:**
- Modify: `docs/context/LAST_HANDOFF.md`
- Regenerate context files if required by `scripts/update_context_cache.py`.

- [ ] **Step 1: Run full verification suite**

Run:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_research_release.py --ci
python scripts/check_claim_registry.py
python scripts/doctor.py
python scripts/validate_context_cache.py
pre-commit run --all-files
```

Expected: all pass.

- [ ] **Step 2: Refresh context cache if paper state changed materially**

Run:

```powershell
python scripts/update_context_cache.py --refresh-boot
python scripts/validate_context_cache.py
```

Expected: context cache validation passed.

- [ ] **Step 3: Update handoff**

Add a short entry to `docs/context/LAST_HANDOFF.md`:

```markdown
## 2026-06-29 Paper Revision V6

- Completed evidence-safe paper revision v6.
- K-B/R5-XGame remains the strongest validated bounded non-locked result.
- K-A expanded TempGlitch remains excluded unless a downloaded bundle validates locally.
- Locked test remains closed.
- LaTeX build status: record local compile success or external Overleaf handoff.
```

- [ ] **Step 4: Final artifact safety check**

Run:

```powershell
git status --short
git diff --check
git ls-files | Select-String -Pattern "outputs/|checkpoints/|\.lance/|kaggle\.json|\.env|r5_xgame_outputs|ka_tempglitch"
```

Expected: no raw outputs, checkpoints, Lance datasets, credentials, or downloaded Kaggle bundles are tracked.

- [ ] **Step 5: Final commit**

```powershell
git add docs/context paper scripts tests
git commit -m "refactor(paper): Codex pass 1-10 structural revision v6"
```

---

## Self-Review

Spec coverage:

- Claim-safety, K-A gating, R5-XGame CI correction, VLM caution, timeline qualitative boundary, LLNCS readiness, and anonymization are all mapped to tasks.
- The plan does not include locked-test, K-C, synthetic GlitchBench, or unvalidated K-A paper claims.

Placeholder scan:

- No placeholder tokens are used as implementation instructions.
- Conditional branches are explicit and bounded: VLM exact numbers are not used unless primary-source verification occurs; timeline figure files are generated only if validated artifacts are available.

Type and path consistency:

- All paths are repository-relative except LaTeX plugin commands, which use absolute Windows paths.
- Commit messages are unique and task-scoped.

Execution handoff:

- Recommended execution mode is subagent-driven because tasks touch separate paper surfaces and benefit from focused review between commits.
