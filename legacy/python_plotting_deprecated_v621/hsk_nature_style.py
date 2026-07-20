from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt

# Nature / SCI restrained palettes for HSK mathematical modeling figures.
# Use the same semantic color for the same method or solution across all panels.
PALETTE_NATURE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE",
    "green_2": "#AADCA9",
    "green_3": "#8BCF8B",
    "red_1": "#F6CFCB",
    "red_2": "#E9A6A1",
    "red_strong": "#B64342",
    "neutral_light": "#CFCECE",
    "neutral_mid": "#767676",
    "neutral_dark": "#4D4D4D",
    "neutral_black": "#272727",
    "gold": "#FFD700",
    "teal": "#42949E",
    "violet": "#9A4D8E",
    "magenta": "#EA84DD",
}

PALETTE_NMI_PASTEL = {
    "baseline_dark": "#484878",
    "baseline_mid": "#7884B4",
    "baseline_soft": "#B4C0E4",
    "ours_tiny": "#E4E4F0",
    "ours_base": "#E4CCD8",
    "ours_large": "#F0C0CC",
    "delta_up": "#2E9E44",
    "delta_down": "#E53935",
}

DEFAULT_COLOR_ORDER = [
    PALETTE_NATURE["blue_main"],
    PALETTE_NATURE["green_3"],
    PALETTE_NATURE["red_strong"],
    PALETTE_NATURE["teal"],
    PALETTE_NATURE["violet"],
    PALETTE_NATURE["neutral_light"],
]

DEFAULT_COLOR_ORDER_NMI = [
    PALETTE_NMI_PASTEL["baseline_dark"],
    PALETTE_NMI_PASTEL["baseline_mid"],
    PALETTE_NMI_PASTEL["baseline_soft"],
    PALETTE_NMI_PASTEL["ours_tiny"],
    PALETTE_NMI_PASTEL["ours_base"],
    PALETTE_NMI_PASTEL["ours_large"],
]


def setup_hsk_nature_style(font_candidates: Optional[Iterable[str]] = None, *, large: bool = False) -> None:
    """Apply a Nature/SCI-style Matplotlib theme for HSK modeling papers.

    The default is sized for LaTeX paper figures. Set ``large=True`` only for
    slide-sized preview panels. Do not call this as a substitute for choosing
    the correct chart type and evidence structure.
    """
    if font_candidates is None:
        font_candidates = [
            "Arial", "Helvetica", "Microsoft YaHei", "SimHei",
            "Noto Sans CJK SC", "Source Han Sans SC", "DejaVu Sans", "sans-serif"
        ]
    base_font = 9 if large else 7.5
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": list(font_candidates),
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "figure.dpi": 180,
        "savefig.dpi": 300,
        "font.size": base_font,
        "axes.titlesize": base_font + 0.8,
        "axes.labelsize": base_font,
        "xtick.labelsize": base_font - 0.6,
        "ytick.labelsize": base_font - 0.6,
        "legend.fontsize": base_font - 0.6,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.4,
        "lines.markersize": 4.5,
        "patch.linewidth": 0.7,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.prop_cycle": mpl.cycler(color=DEFAULT_COLOR_ORDER),
    })


def save_hsk_nature_figure(
    fig: plt.Figure,
    path_stem: Path | str,
    *,
    png_dpi: int = 300,
    tiff: bool = False,
    svg: bool = True,
    pdf: bool = True,
) -> None:
    """Save a paper figure to PNG plus vector formats.

    ``path_stem`` should normally live under ``figures/`` and use English or
    pinyin filenames for LaTeX compatibility.
    """
    stem = Path(path_stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".png"), bbox_inches="tight", dpi=png_dpi)
    if pdf:
        fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    if svg:
        fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    if tiff:
        fig.savefig(stem.with_suffix(".tiff"), bbox_inches="tight", dpi=600)


def add_panel_label(ax: plt.Axes, label: str, *, x: float = -0.12, y: float = 1.08) -> None:
    """Add a small bold lower-case panel label like a, b, c, d."""
    ax.text(x, y, label, transform=ax.transAxes, fontsize=9, fontweight="bold", va="top", ha="left")


def soften_axes(ax: plt.Axes, *, grid: bool = False) -> None:
    """Apply minimal Nature-style axis cleanup to an existing axis."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(axis="y", color="#E6E6E6", linewidth=0.6, alpha=0.8)
        ax.set_axisbelow(True)
    else:
        ax.grid(False)


def semantic_colors(names: Sequence[str]) -> dict[str, str]:
    """Return stable semantic colors for a list of method or scheme names."""
    order = DEFAULT_COLOR_ORDER_NMI if len(names) > 5 else DEFAULT_COLOR_ORDER
    return {name: order[i % len(order)] for i, name in enumerate(names)}
