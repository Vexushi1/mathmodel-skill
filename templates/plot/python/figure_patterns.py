"""Optional Python implementations of the single Module 04 Figure Authority.

Use the accepted Figure Contract to select *which* pattern is appropriate.
Functions here implement rendering mechanisms; they do not choose graph types,
read/unlock workbooks, infer uncertainty, approve Figures, or run a solver.
Individual qN_plot.py files remain self-contained unless the user deliberately
copies a suitable function and records its source dependency.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
import math

import matplotlib.pyplot as plt
import numpy as np


def _rgb(value: Sequence[float]) -> tuple[float, float, float]:
    """Every data-series color is explicitly selected; no default color cycle."""
    if len(value) != 3 or any(
        not isinstance(c, (float, int, np.floating, np.integer))
        or not math.isfinite(float(c)) or not 0 <= float(c) <= 1 for c in value
    ):
        raise ValueError("Each color must be three finite RGB components in [0,1]")
    return tuple(float(c) for c in value)


def _vector(values, *, name: str, allow_nan: bool = False) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name}: nonempty 1-D vector required")
    if np.isinf(array).any() or (not allow_nan and not np.isfinite(array).all()):
        raise ValueError(f"{name}: nonfinite values violate the declared evidence scope")
    return array


def apply_publication_frame(ax, *, font_family: str | None = None,
                            axis_font_size: float = 11, label_font_size: float = 12,
                            axis_line_width: float = .8, grid: bool = False,
                            keep_top_right: bool = False):
    """Apply frame and typography *after* data elements exist; never recolor data.

    The selected font must exist in the user's actual environment; leave None
    to use the current Matplotlib font without pretending CJK support.
    """
    if not all(math.isfinite(float(v)) and float(v) > 0
               for v in (axis_font_size, label_font_size, axis_line_width)):
        raise ValueError("Positive typography/frame sizes required")
    ax.tick_params(labelsize=axis_font_size, direction="out")
    ax.xaxis.label.set_fontsize(label_font_size)
    ax.yaxis.label.set_fontsize(label_font_size)
    for side, spine in ax.spines.items():
        spine.set_linewidth(axis_line_width)
        if side in ("top", "right") and not keep_top_right:
            spine.set_visible(False)
    ax.grid(grid, axis="both", linewidth=.5, alpha=.25 if grid else 0)
    if grid:
        ax.set_axisbelow(True)
    if font_family:
        for label in [ax.xaxis.label, ax.yaxis.label, *ax.get_xticklabels(),
                      *ax.get_yticklabels()]:
            label.set_fontfamily(font_family)
    legend = ax.get_legend()
    if legend is not None:
        legend.set_frame_on(False)
        if font_family:
            for label in legend.get_texts():
                label.set_fontfamily(font_family)
    return ax


def box_with_raw_points(ax, groups: Mapping[str, Sequence[float]], *,
                        colors: Sequence[Sequence[float]], point_size: float = 16,
                        box_width: float = .5):
    """Distribution profile C1: box and actual raw samples, no fake violin/KDE.

    Deterministic jitter is a display offset only, not a change to measurements.
    """
    if not groups or len(colors) != len(groups):
        raise ValueError("One explicit color is required for each nonempty group")
    values = [_vector(v, name=f"group {k}") for k, v in groups.items()]
    xs = np.arange(1, len(values) + 1, dtype=float)
    palette = [_rgb(c) for c in colors]
    box = ax.boxplot(values, positions=xs, widths=box_width, patch_artist=True,
                     showfliers=False, medianprops={"color": "black", "linewidth": 1.1})
    for patch, color in zip(box["boxes"], palette):
        patch.set_facecolor((*color, .18))
        patch.set_edgecolor(color)
    for index, (data, color) in enumerate(zip(values, palette), 1):
        jitter = .065 * np.sin(np.arange(len(data), dtype=float) * 2.399963)
        ax.scatter(index + jitter, data, s=point_size, color=color, alpha=.62,
                   zorder=3, edgecolors="none")
    ax.set_xticks(xs, list(groups))
    return ax


def line_with_recorded_interval(ax, x, y, lower, upper, *,
                                color: Sequence[float], name: str,
                                lower_upper_name: str = "记录区间",
                                show_markers: bool = False):
    """Dynamic/Regression C3: render stored interval, never synthesize a CI.

    NaNs remain in position and separate line and interval polygons.
    """
    x = _vector(x, name="x")
    y = _vector(y, name="y", allow_nan=True)
    lo = _vector(lower, name="lower", allow_nan=True)
    hi = _vector(upper, name="upper", allow_nan=True)
    if not (len(x) == len(y) == len(lo) == len(hi)):
        raise ValueError("X/Y/interval must share the original record alignment")
    mask = np.isfinite(lo) & np.isfinite(hi)
    if (lo[mask] > hi[mask]).any():
        raise ValueError("Recorded lower bounds exceed upper bounds")
    rgb = _rgb(color)
    ax.fill_between(x, lo, hi, color=rgb, alpha=.15, label=lower_upper_name)
    ax.plot(x, y, color=rgb, linewidth=1.6,
            marker="o" if show_markers else None,
            markersize=3.5, label=name)
    return ax


def heatmap_with_real_boundary(ax, x, y, z, *,
                               cmap: str, boundary_level: float | None = None,
                               boundary_color: Sequence[float] | None = None,
                               colorbar_label: str | None = None):
    """Parameter Surface C5: genuine rectangular sampled field and contour.

    Coordinates, Z and threshold must be actual accepted evidence; no new
    gridding/interpolation or smoothing occurs inside this function.
    """
    x = _vector(x, name="x")
    y = _vector(y, name="y")
    field = np.asarray(z, dtype=float)
    if field.shape != (len(y), len(x)) or not np.isfinite(field).all():
        raise ValueError("Z must be a real finite (len(y), len(x)) accepted grid")
    mesh = ax.pcolormesh(x, y, field, shading="nearest", cmap=cmap)
    if boundary_level is not None:
        if boundary_color is None or not math.isfinite(boundary_level):
            raise ValueError("Contour needs an evidence-grounded threshold and RGB")
        ax.contour(x, y, field, levels=[float(boundary_level)],
                   colors=[_rgb(boundary_color)], linewidths=1.2)
    if colorbar_label is not None:
        bar = ax.figure.colorbar(mesh, ax=ax)
        bar.set_label(colorbar_label)
    return mesh


def pareto_with_choice(ax, objective_x, objective_y, *, color: Sequence[float],
                       selected: int | None = None,
                       selected_color: Sequence[float] | None = None,
                       labels: Sequence[str] | None = None):
    """Optimization C6: plot only already-qualified Pareto candidates and choice.

    Does NOT compute dominance, Pareto front, weighted scoring or recommendation.
    """
    x = _vector(objective_x, name="objective_x")
    y = _vector(objective_y, name="objective_y")
    if len(x) != len(y):
        raise ValueError("Both objective columns must have the same samples")
    ax.scatter(x, y, s=27, color=_rgb(color), label="已验收候选方案")
    if selected is not None:
        if not isinstance(selected, int) or selected < 0 or selected >= len(x):
            raise ValueError("Selected recommendation must refer to an actual row")
        if selected_color is None:
            raise ValueError("An emphasized recommendation requires explicit RGB")
        ax.scatter([x[selected]], [y[selected]], s=100, marker="*",
                   color=_rgb(selected_color), edgecolor="black",
                   linewidth=.5, label="已确认推荐方案", zorder=4)
        if labels is not None:
            if len(labels) != len(x):
                raise ValueError("Candidate labels must align with actual sample rows")
            ax.annotate(str(labels[selected]), (x[selected], y[selected]),
                        xytext=(7, 7), textcoords="offset points")
    return ax


def inset_with_grounded_limits(ax, x_limits: tuple[float, float],
                              y_limits: tuple[float, float], *,
                              relative_bounds: tuple[float, float, float, float]):
    """Local Zoom Z1: provide only frame geometry, not invented ROI selection.

    Draw the actual evidence in the returned inset using the *same* source rows.
    """
    if (not len(x_limits) == len(y_limits) == 2 or
            not x_limits[0] < x_limits[1] or not y_limits[0] < y_limits[1]):
        raise ValueError("A meaningful recorded ROI must have finite ordered limits")
    if not all(math.isfinite(float(v)) for v in (*x_limits, *y_limits)):
        raise ValueError("Zoom bounds must be finite")
    x0, y0, width, height = relative_bounds
    if not (0 <= x0 < 1 and 0 <= y0 < 1 and 0 < width <= 1 - x0
            and 0 < height <= 1 - y0):
        raise ValueError("Inset rectangle must fit inside parent axes")
    inset = ax.inset_axes(relative_bounds)
    inset.set_xlim(*x_limits)
    inset.set_ylim(*y_limits)
    ax.indicate_inset_zoom(inset, edgecolor=".35")
    return inset



def small_multiples_lines(series: Mapping[str, tuple[Sequence[float], Sequence[float]]],
                          *, colors: Mapping[str, Sequence[float]],
                          ncols: int = 2, shared_axes: bool = True,
                          x_label: str = "", y_label: str = ""):
    """Small Multiples Z2: same accepted records, one series per readable panel.

    Shared axes are appropriate for magnitude comparisons; disable only when
    the Figure Contract compares shapes rather than amplitudes. No interpolation,
    smoothing, reordering or dropping missing positions is performed.
    """
    if not series or set(colors) != set(series):
        raise ValueError("Every recorded series needs one explicit RGB color")
    if not isinstance(ncols, int) or isinstance(ncols, bool) or ncols < 1:
        raise ValueError("ncols must be a positive integer chosen for the evidence")
    count = len(series)
    ncols = min(ncols, count)
    nrows = math.ceil(count / ncols)
    fig, axes = plt.subplots(
        nrows, ncols, squeeze=False, sharex=shared_axes,
        sharey=shared_axes, figsize=(4.4 * ncols, 2.9 * nrows),
        layout="constrained",
    )
    for ax, (label, (x_values, y_values)) in zip(axes.flat, series.items()):
        x = _vector(x_values, name=f"{label} x")
        y = _vector(y_values, name=f"{label} y", allow_nan=True)
        if len(x) != len(y) or not np.isfinite(y).any():
            raise ValueError(f"{label}: aligned records with observed values required")
        ax.plot(x, y, color=_rgb(colors[label]), linewidth=1.5)
        ax.text(.03, .96, str(label), transform=ax.transAxes,
                ha="left", va="top", fontsize=10, weight="medium")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        apply_publication_frame(ax)
    for ax in list(axes.flat)[count:]:
        ax.set_visible(False)
    # A formal Figure caption is owned by the paper; no figure/axes title.
    return fig, axes


def recorded_surface_3d(ax, x, y, z, *, cmap: str,
                        x_label: str, y_label: str, z_label: str):
    """Conditional 3D: render an already accepted 2-factor response grid.

    Module 04 must establish the physical/mathematical meaning of the third
    dimension and why a 2-D projection loses evidence before this is used.
    The renderer never interpolates, estimates or extrapolates a surface.
    """
    if getattr(ax, "name", "") != "3d":
        raise ValueError("Conditional 3D requires a genuine 3-D axes")
    x = _vector(x, name="x")
    y = _vector(y, name="y")
    field = np.asarray(z, dtype=float)
    if field.shape != (len(y), len(x)) or not np.isfinite(field).all():
        raise ValueError("3-D surface requires the finite accepted (y, x) grid")
    if len(x) < 2 or len(y) < 2:
        raise ValueError("3-D surface requires at least two measured positions per axis")
    if not all(isinstance(v, str) and v.strip()
               for v in (x_label, y_label, z_label)):
        raise ValueError("Every physically meaningful axis needs a unit-aware label")
    xx, yy = np.meshgrid(x, y)
    surface = ax.plot_surface(xx, yy, field, cmap=cmap, linewidth=0,
                              antialiased=False)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_zlabel(z_label)
    return surface


def export_after_visual_review(fig, path: str | Path, *,
                               dpi: int = 300):
    """Vector-first publication output; actual run is not Figure approval."""
    destination = Path(path)
    if destination.suffix.lower() not in {".pdf", ".svg", ".png"}:
        raise ValueError("Choose PDF/SVG vector or PNG when raster is needed")
    if not isinstance(dpi, int) or not 150 <= dpi <= 600:
        raise ValueError("Raster DPI must be explicitly appropriate to the evidence")
    fig.savefig(destination, dpi=dpi, bbox_inches="tight",
                facecolor="white")
    return destination
