from __future__ import annotations

import ast
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
            self.assertEqual(
                row["function_count"],
                row["top_level_function_count"] + row["nested_function_count"],
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
        self.assertEqual(generated["actions_write_permission_occurrences"], 1)
        self.assertGreaterEqual(generated["full_ci_dispatch_occurrences"], 1)
        self.assertGreaterEqual(generated["optimization_baseline_dispatch_occurrences"], 1)
        self.assertIsInstance(generated["generated_check_occurrences"], list)

    def test_top_level_span_helper_excludes_nested_functions(self):
        tree = ast.parse(
            "def outer():\n"
            "    def inner():\n"
            "        return 1\n"
            "    return inner()\n"
            "\n"
            "async def second():\n"
            "    return 2\n"
        )
        rows = metrics._top_level_function_rows(tree)
        self.assertEqual([row["name"] for row in rows], ["outer", "second"])
        self.assertEqual(rows[0]["start_line"], 1)
        self.assertEqual(rows[0]["end_line"], 4)
        self.assertEqual(rows[0]["span_lines"], 4)
        self.assertFalse(rows[0]["async"])
        self.assertTrue(rows[1]["async"])

    def test_lint_hotspot_function_distribution_is_structural_only(self):
        report = metrics.collect_metrics(ROOT, top=10)
        structure = report["lint_skill_checks_structure"]
        self.assertTrue(structure["present"])
        self.assertEqual(structure["path"], "scripts/lint_skill_checks.py")
        self.assertGreater(structure["top_level_function_count"], 0)
        self.assertGreaterEqual(structure["nested_function_count"], 0)
        self.assertGreater(structure["top_level_span_lines_total"], 0)
        self.assertGreater(structure["top_level_span_lines_max"], 0)
        self.assertIn("structural evidence only", structure["interpretation_boundary"])

        functions = structure["functions_source_order"]
        self.assertEqual(
            [item["start_line"] for item in functions],
            sorted(item["start_line"] for item in functions),
        )
        self.assertEqual(
            sum(structure["name_prefix_families"].values()),
            structure["top_level_function_count"],
        )
        self.assertEqual(
            sum(structure["span_buckets"].values()),
            structure["top_level_function_count"],
        )
        largest_spans = [item["span_lines"] for item in structure["largest_functions"]]
        self.assertEqual(largest_spans, sorted(largest_spans, reverse=True))
        self.assertLessEqual(len(structure["largest_functions"]), 10)

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
        self.assertEqual(len(payload["lint_skill_checks_structure"]["largest_functions"]), 3)


if __name__ == "__main__":
    unittest.main()
