"""Actual Python fixture regression; MATLAB runs in the explicit native CI job."""
from pathlib import Path
import tempfile
import unittest

from tests.analysis_comparison_smoke import run_smoke


class AnalysisComparisonSmokeTests(unittest.TestCase):
    def test_real_python_comparison_delivery_execution_and_acceptance(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run_smoke(Path(temporary) / "isolated-project", "python")
            self.assertTrue(report["actual_python_execution"])
            self.assertTrue(report["primary_unchanged"])
            self.assertTrue(report["model_comparison_verified"])
            self.assertTrue(report["algorithm_comparison_verified"])
            self.assertTrue(report["helper_drift_rejected"])
            self.assertEqual(len(report["stages"]), 2)
            ordinary = report["ordinary_comparison"]
            self.assertTrue(ordinary["primary_unchanged"])
            self.assertFalse(ordinary["machine_state_created"])
            self.assertFalse(ordinary["comparison_extension_emitted"])
            self.assertAlmostEqual(ordinary["quadratic_holdout_prediction"], 16)
            self.assertAlmostEqual(ordinary["linear_holdout_prediction"], 11)
            self.assertEqual(set(ordinary["invalid_extension_rejections"]),
                             {"missing_plan", "missing_version", "unsupported_version", "invalid_plan"})
            self.assertTrue(all(code != 0 for code in ordinary["invalid_extension_rejections"].values()))
            for case, index in (("holdout_observations", 4), ("reordered_holdout", 0)):
                with self.subTest(case=case):
                    self.assertEqual(report[case]["evaluation_index"], index)
                    for source in ("primary_core", "primary_detail", "comparison_baseline"):
                        self.assertAlmostEqual(report[case][source], 16)
            self.assertEqual(set(report["invalid_holdout_rejections"]), {"missing", "duplicate"})
            self.assertTrue(all(code != 0 for code in report["invalid_holdout_rejections"].values()))


if __name__ == "__main__":
    unittest.main()
