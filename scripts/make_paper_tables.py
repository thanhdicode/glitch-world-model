from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "paper" / "tables"

PHASE6D_TEX = r"""\begin{table}[t]
\centering
\caption{Phase 6D repeated grouped selected-pipeline results.}
\begin{tabular}{lcc}
\hline
Metric & Mean & Population SD \\
\hline
Locked-test AUROC & 0.573170 & 0.117582 \\
Locked-test F1 & 0.562925 & 0.051708 \\
\hline
\end{tabular}
\label{tab:phase6d}
\end{table}
"""

PHASE6E_TEX = r"""\begin{table}[t]
\centering
\caption{Phase 6E Conv3D validation-only metrics.}
\begin{tabular}{lc}
\hline
Metric & Validation value \\
\hline
AUROC & 0.403865 \\
F1 & 0.605263 \\
Precision & 0.434372 \\
Recall & 0.997831 \\
Accuracy & 0.439776 \\
\hline
\end{tabular}
\label{tab:phase6e-validation}
\end{table}
"""

PHASE6E_MD = """# Phase 6E Conv3D Validation Metrics

Validation only. Locked test remains untouched.

| Metric | Value |
| --- | ---: |
| AUROC | 0.403865 |
| F1 | 0.605263 |
| Precision | 0.434372 |
| Recall | 0.997831 |
| Accuracy | 0.439776 |
"""


def write_tables(output_root: Path) -> list[Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    payloads = {
        "phase6d_results.tex": PHASE6D_TEX,
        "phase6e_validation_metrics.tex": PHASE6E_TEX,
        "phase6e_validation_metrics.md": PHASE6E_MD,
    }
    written: list[Path] = []
    for name, content in payloads.items():
        path = output_root / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate paper tables from documented metrics.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    for path in write_tables(args.output_root):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
