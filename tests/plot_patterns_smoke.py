"""Module-04-equivalent Python scientific Figure rendering smoke (no approval claims)."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
module_path = ROOT / "templates" / "plot" / "python" / "figure_patterns.py"
spec = importlib.util.spec_from_file_location("plot_patterns", module_path)
patterns = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patterns)


class PythonScientificFigurePatterns(unittest.TestCase):
    def test_distribution_with_all_raw_points_and_adaptive_panels(self):
        values = {"A": [1, 2, 5, 3, 4], "B": [2, 3, 4, 7, 5]}
        fig, axes = plt.subplots(1, 2, figsize=(9, 4.4), layout="constrained")
        patterns.box_with_raw_points(axes[0], values,
                                     colors=[(.18, .33, .59), (.75, .36, .22)])
        self.assertEqual(sum(len(coll.get_offsets()) for coll in axes[0].collections), 10)
        patterns.pareto_with_choice(axes[1], [1, 2, 3], [5, 3, 2],
                                   color=(.1, .4, .55), selected=1,
                                   selected_color=(.7, .25, .18), labels=["x1", "x2", "x3"])
        axes[0].set_ylabel("Recorded measure")
        axes[1].set_xlabel("Objective A")
        axes[1].set_ylabel("Objective B")
        for ax in axes:
            ax.legend(frameon=False) if ax.get_legend_handles_labels()[1] else None
            patterns.apply_publication_frame(ax)
            self.assertEqual(ax.get_title(), "")
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "figure_portfolio.svg"
            patterns.export_after_visual_review(fig, destination)
            self.assertGreater(destination.stat().st_size, 1000)
        plt.close(fig)

    def test_true_interval_preserves_missing_positions(self):
        x = np.arange(4.)
        y = [1, np.nan, 2, 3]
        lo = [.5, np.nan, 1.4, 2.3]
        hi = [1.4, np.nan, 2.6, 3.5]
        fig, ax = plt.subplots()
        patterns.line_with_recorded_interval(ax, x, y, lo, hi,
                                             color=(.3, .48, .6), name="recorded",
                                             lower_upper_name="measured interval")
        self.assertTrue(np.isnan(ax.lines[-1].get_ydata()[1]))
        with self.assertRaisesRegex(ValueError, "exceed"):
            patterns.line_with_recorded_interval(ax, x, y, [2, 0, 0, 0], [1, 1, 1, 1],
                                                 color=(.3, .4, .5), name="not an interval")
        plt.close(fig)

    def test_parameter_surface_uses_real_grid_and_threshold(self):
        fig, ax = plt.subplots()
        x, y = [1., 2., 3.], [4., 5., 6.]
        field = np.array([[0., .2, .4], [.3, .55, .8], [.6, .9, 1.2]])
        patterns.heatmap_with_real_boundary(ax, x, y, field, cmap="viridis",
                                            boundary_level=.5, boundary_color=(.2, .2, .2),
                                            colorbar_label="Recorded value")
        self.assertGreaterEqual(len(fig.axes), 2)
        with self.assertRaisesRegex(ValueError, "accepted grid"):
            patterns.heatmap_with_real_boundary(ax, x, y, [[1., 2.]], cmap="viridis")
        plt.close(fig)

    def test_local_zoom_is_grounded_and_reuses_samples(self):
        fig, ax = plt.subplots()
        x = np.arange(6.)
        y = [0, 1, 2, 1.5, 3, 2.8]
        ax.plot(x, y, color=(.2, .45, .65))
        inset = patterns.inset_with_grounded_limits(
            ax, (2, 4), (1.2, 3.1), relative_bounds=(.48, .48, .43, .43)
        )
        inset.plot(x, y, color=(.2, .45, .65))
        self.assertEqual(inset.get_xlim(), (2., 4.))
        self.assertEqual(inset.get_ylim(), (1.2, 3.1))
        plt.close(fig)


if __name__ == "__main__":
    unittest.main()
