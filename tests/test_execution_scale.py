from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from execution_scale import (
    adaptive_plan_issues,
    inspect_scale_plan,
    normalize_scale_plan,
    scale_evidence_issues,
    scale_plan_sha256,
    scale_receipt_issues,
)


def stop_workbook(rows):
    book = Workbook()
    sheet = book.active
    sheet.title = "执行停止证据"
    sheet.append(["迭代或样本数", "指标", "数值", "单位"])
    for row in rows:
        sheet.append(row)
    output = io.BytesIO()
    book.save(output)
    book.close()
    return output.getvalue()


class ExecutionScaleTests(unittest.TestCase):
    def setUp(self):
        self.plan = normalize_scale_plan({
            "axis": "iterations",
            "mode": "adaptive_stop",
            "minimum_count": 50,
            "maximum_count": 100,
            "pqs_id": "PQ-Q1-01",
        }, "primary")
        self.config = {
            "stage": "primary",
            "run_receipt_protocol_version": "1.4.0",
            "execution_scale_plan": self.plan,
            "execution_scale_plan_sha256": scale_plan_sha256(self.plan),
            "data_paths": ["data.csv"],
        }
        self.receipt = {
            "stage": "primary",
            "run_receipt_version": "1.4.0",
            "execution_scale_plan_sha256": scale_plan_sha256(self.plan),
            "actual_scale_count": 80,
            "actual_stop_reason": "criterion_met",
            "data_paths": '["data.csv"]',
            "data_identity_mode": "combined",
        }
        self.approved = {"version": "1.0.0", "items": [{
            "id": "PQ-Q1-01",
            "metric": "relative_error",
            "evidence_sheet": "执行停止证据",
            "relation": "<=",
            "threshold": 0.05,
            "unit": "1",
            "threshold_source": "mathematical_definition",
        }]}
        self.rows = [[40, "relative_error", 0.07, "1"], [80, "relative_error", 0.04, "1"]]

    def stop_issues(self, rows, receipt=None):
        return scale_evidence_issues(
            stop_workbook(rows), self.plan, receipt or self.receipt, approved_specification=self.approved,
        )

    def test_lower_protocol_does_not_admit_explicit_scale_fields(self):
        self.assertEqual(inspect_scale_plan({"run_receipt_protocol_version": "1.2.0"}), (None, []))
        old = {**self.config, "run_receipt_protocol_version": "1.3.0"}
        self.assertTrue(inspect_scale_plan(old)[1])
        self.assertTrue(scale_receipt_issues(self.receipt, old))
        self.assertTrue(scale_receipt_issues({**self.receipt, "run_receipt_version": "1.3.0"}, self.config))
        self.assertEqual(inspect_scale_plan(self.config), (self.plan, []))
        self.assertEqual(scale_receipt_issues(self.receipt, self.config), [])

    def test_adaptive_requires_approved_numeric_stop_evidence(self):
        self.assertIn("approved PQS", adaptive_plan_issues(self.plan, None)[0])
        criterion = self.approved["items"][0]
        for field, value in (("evidence_sheet", "收敛诊断"), ("relation", "bool_true")):
            with self.subTest(field=field):
                altered = {"items": [{**criterion, field: value}]}
                self.assertIn("numeric criterion", adaptive_plan_issues(self.plan, altered)[0])
        self.assertEqual(adaptive_plan_issues(self.plan, self.approved), [])
        self.assertEqual(self.stop_issues(self.rows), [])

    def test_terminal_step_value_and_units_must_match(self):
        for rows, receipt, message in (
            (self.rows, {**self.receipt, "actual_scale_count": 79}, "last checkpoint"),
            (self.rows, {**self.receipt, "actual_scale_count": True}, "positive numeric integer"),
            (self.rows, {**self.receipt, "actual_stop_reason": "budget_exhausted"}, "criterion_met"),
            ([self.rows[0], [80, "relative_error", 0.07, "1"]], self.receipt, "does not satisfy"),
            ([self.rows[0], [80, "relative_error", 0.04, "%"]], self.receipt, "approved PQS unit"),
            ([*self.rows, self.rows[-1]], self.receipt, "duplicate checkpoints"),
            ([[80, "other_metric", 0.04, "1"]], self.receipt, "missing the approved PQS metric"),
        ):
            with self.subTest(message=message):
                self.assertTrue(any(message in issue for issue in self.stop_issues(rows, receipt)))

    def test_scenario_id_canonicalization_and_digest(self):
        scenario = {"axis": "scenarios", "mode": "exact", "count": 2, "required_scenario_ids": ["  B", "A"]}
        normalized = normalize_scale_plan(scenario, "analysis")
        self.assertEqual(normalized["required_scenario_ids"], ["A", "B"])
        source = {**self.config, "stage": "analysis", "execution_scale_plan": scenario}
        self.assertTrue(inspect_scale_plan(source)[1])
        source["execution_scale_plan_sha256"] = scale_plan_sha256(normalized)
        self.assertEqual(inspect_scale_plan(source), (normalized, []))
        for ids in (["A", " A "], ["A"], []):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                normalize_scale_plan({**scenario, "required_scenario_ids": ids}, "analysis")
