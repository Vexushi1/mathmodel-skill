"""Measure case 10 on the existing real Excel / matplotlib jobs."""
import json
import unittest

from v11_plot_observations import plot_observations


class PlotWorkbookBaseline(unittest.TestCase):
    def test_real_blank_and_numeric_controls(self):
        observed = plot_observations()
        print("v11 case 10:", json.dumps(observed, sort_keys=True))
        for reader in ("question", "preprocessing"):
            with self.subTest(reader=reader):
                self.assertEqual(observed[reader + "_missing"], "gap")
                self.assertEqual(observed[reader + "_numeric"], 3)
