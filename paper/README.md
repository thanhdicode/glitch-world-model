# Paper Scaffold

The paper is deliberately cautious: Phase 6E is validation-only and negative; real LeWM is
future work.

Generate documented tables:

```powershell
python scripts\make_paper_tables.py
```

Compile when a LaTeX distribution and `latexmk` are installed:

```powershell
latexmk -pdf -cd paper/main.tex
```

Generated LaTeX build files are gitignored. Update claims and source documents before changing
paper results.
