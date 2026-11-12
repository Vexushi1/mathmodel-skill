"""G4-A probe guards: reproducible behavior, bounded read-only scope and diagnostics."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import g4a_resolver_parse_probe as PROBE


class G4AResolverParseProbeTests(unittest.TestCase):
    def test_duplicate_read_accounting_does_not_change_source_identity(self) -> None:
        path = PROBE.CONTRACTS[0]
        observations = [
            ("assured", path), ("legacy", path),
            ("assured", PROBE.CONTRACTS[1]),
        ]
        counts = PROBE.count_contract_reads(observations)
        self.assertEqual(counts["per_contract"][path], 2)
        self.assertEqual(counts["duplicate_contract_reads"], 1)
        self.assertEqual(counts["total_tracked_yaml_file_reads"], 3)
        self.assertEqual(counts["per_role"]["legacy"][path], 1)

    def test_unknown_mode_and_out_of_scope_root_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown measurement mode"):
            PROBE.capture("figures", "只做图表", "untracked_mode")
        for count in (0, 6):
            with self.assertRaisesRegex(ValueError, "repeats"):
                PROBE.collect(ROOT, count)
        with tempfile.TemporaryDirectory(prefix="hsk-g4a-foreign-root-") as path:
            with self.assertRaisesRegex(ValueError, "checked-out source tree"):
                PROBE.collect(Path(path), 1)

    def test_synthetic_measurement_does_not_change_resolver_behavior(self) -> None:
        report = PROBE.collect(ROOT, repeats=1)
        self.assertTrue(report["not_a_production_api"])
        self.assertEqual(set(report["contract_sha256"]), set(PROBE.CONTRACTS))
        self.assertEqual(len(report["cases"]), len(PROBE.CASES))
        for case in report["cases"]:
            self.assertTrue(case["behavior_equal"])
            row = case["runs"][0]
            self.assertEqual(set(row), set(PROBE.MODES))
            signatures = {row[mode]["plan_sha256"] for mode in PROBE.MODES}
            self.assertEqual(len(signatures), 1)
            for mode in PROBE.MODES:
                self.assertGreater(row[mode]["loads"]["total_tracked_yaml_file_reads"], 0)
                self.assertGreaterEqual(row[mode]["parser_calls"], 0)
                self.assertGreaterEqual(row[mode]["safe_yaml_deep_copies"], 0)


if __name__ == "__main__":
    unittest.main()
