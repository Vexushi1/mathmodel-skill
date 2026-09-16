from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import measure_infrastructure as metrics  # noqa: E402


class TestP8InfrastructureMeasurement(unittest.TestCase):
    def test_measurement_is_read_only_structured_evidence(self):
        report = metrics.collect_metrics(ROOT, top=8)
        self.assertEqual(report["schema_version"], "1.1.0")
        self.assertEqual(report["scope"], "repository_infrastructure_measurement_only")
        self.assertGreater(report["python_scripts"]["count"], 0)
        self.assertGreater(report["python_scripts"]["total_bytes"], 0)
        self.assertLessEqual(len(report["python_scripts"]["largest"]), 8)

    def test_largest_rows_are_sorted_and_use_relative_paths(self):
        report = metrics.collect_metrics(ROOT, top=12)
        rows = report["python_scripts"]["largest"]
        sizes = [row["bytes"] for row in rows]
        self.assertEqual(sizes, sorted(sizes, reverse=True))
        for row in rows:
            self.assertFalse(Path(row["path"]).is_absolute())
            self.assertGreater(row["bytes"], 0)
            self.assertGreater(row["nonblank_lines"], 0)
            self.assertGreaterEqual(row["function_count"], row["top_level_function_count"])
            spans = row["largest_top_level_functions"]
            self.assertLessEqual(len(spans), 10)
            if spans:
                span_sizes = [item["span_lines"] for item in spans]
                self.assertEqual(span_sizes, sorted(span_sizes, reverse=True))
                for item in spans:
                    self.assertGreaterEqual(item["start_line"], 1)
                    self.assertGreaterEqual(item["end_line"], item["start_line"])
                    self.assertEqual(
                        item["span_lines"],
                        item["end_line"] - item["start_line"] + 1,
                    )

    def test_lint_skill_function_distribution_is_measured_not_inferred(self):
        report = metrics.collect_metrics(ROOT, top=20)
        lint = next(
            row
            for row in report["validator_hotspots"]
            if row["path"] == "scripts/lint_skill_checks.py"
        )
        self.assertGreater(lint["top_level_function_count"], 0)
        self.assertGreater(lint["top_level_check_function_count"], 0)
        self.assertTrue(lint["largest_top_level_functions"])
        self.assertTrue(
            all(
                item["name"]
                for item in lint["largest_top_level_functions"]
            )
        )

    def test_repeated_parser_measurement_matches_ast_scan(self):
        report = metrics.collect_metrics(ROOT, top=8)
        yaml_report = report["repeated_parsing"]["yaml_safe_load"]
        self.assertEqual(
            yaml_report["call_count"],
            sum(item["calls"] for item in yaml_report["files"]),
        )
        self.assertEqual(yaml_report["file_count"], len(yaml_report["files"]))
        paths = {item["path"] for item in yaml_report["files"]}
        self.assertIn("scripts/validate_code_delivery.py", paths)
        self.assertIn("scripts/validate_user_execution.py", paths)

    def test_generated_metadata_measurement_detects_current_workflow_shape(self):
        report = metrics.collect_metrics(ROOT, top=8)
        generated = report["generated_metadata"]
        self.assertTrue(generated["refresh_workflow_present"])
        self.assertGreaterEqual(generated["generator_invocations"], 1)
        self.assertIsInstance(generated["generated_check_occurrences"], list)

    def test_json_cli_matches_schema(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "measure_infrastructure.py"), "--json", "--top", "3"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "1.1.0")
        self.assertEqual(len(payload["python_scripts"]["largest"]), 3)
        self.assertIn("largest_top_level_functions", payload["python_scripts"]["largest"][0])


if __name__ == "__main__":
    unittest.main()
