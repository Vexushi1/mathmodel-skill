from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import matplotlib.pyplot as plt
import matplotlib as mpl


def setup_academic_style(font_candidates: Optional[Iterable[str]] = None) -> None:
    """Apply a clean paper-oriented Matplotlib style.

    The function intentionally avoids hard-coded decorative colors. It focuses on
    font, line width, grid, dpi, and export quality. Users can set problem-specific
    palettes in the plotting function when necessary.
    """
    if font_candidates is None:
        font_candidates = [
            "SimHei", "Microsoft YaHei", "Noto Sans CJK SC",
            "Source Han Sans SC", "Arial Unicode MS", "DejaVu Sans"
        ]
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": list(font_candidates),
        "axes.unicode_minus": False,
        "figure.dpi": 160,
        "savefig.dpi": 300,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.4,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "legend.frameon": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def save_figure(fig: plt.Figure, path_stem: Path, save_pdf: bool = True) -> None:
    path_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path_stem.with_suffix(".png"), bbox_inches="tight", dpi=300)
    if save_pdf:
        fig.savefig(path_stem.with_suffix(".pdf"), bbox_inches="tight")


# For higher-polish Nature/SCI figures, see templates/shared/hsk_nature_style.py.
# It provides setup_hsk_nature_style(), save_hsk_nature_figure(), panel labels, and semantic palettes.
