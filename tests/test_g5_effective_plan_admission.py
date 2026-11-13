"""G5 negative-admission guards: read unions are never effective-plan approval."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import g5_effective_plan_admission as G5


def row(path: str, start: int, end: int, sha: str = "a" * 64):
    return {
        "path": path, "origin": "skill", "sha256": sha,
        "ranges": [[start, end]],
    }


def gate(name: str, command: str):
    return {"name": name, "path": f"scripts/{name}.py", "command": command,
            "inputs": ["current"], "delivery_scope": "submission"}


class G5EffectivePlanAdmissionTests(unittest.TestCase):
    def test_existing_oracle_actions_have_cross_action_dependencies(self):
        cases = G5.selected_cases(ROOT)
        self.assertEqual([case["id"] for case in cases], list(G5.IDS))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(case["category"], "independent_actions")
                self.assertEqual(len(case["positive_actions"]), 2)
                self.assertTrue(case["dependencies"])
                self.assertFalse(
                    any(action["intent"] in case.get("negative_intents", [])
                        for action in case["positive_actions"])
                )

    def test_source_coverage_requires_exact_ranges_and_identity(self):
        required = [row("a.md", 1, 11), row("b.md", 1, 2)]
        partial = [row("a.md", 1, 3), row("a.md", 5, 11), row("b.md", 1, 2)]
        gaps = G5.missing_read_ranges(required, partial)
        self.assertEqual(gaps, [{"source": ("skill", "a.md", "a" * 64),
                                 "range": [4, 4]}])
        self.assertEqual(
            G5.missing_read_ranges(required, partial + [row("a.md", 4, 4)]), [])
        different_hash = [row("a.md", 1, 11, "b" * 64), row("b.md", 1, 2)]
        self.assertEqual(G5.missing_read_ranges(required, different_hash), [{
            "source": ("skill", "a.md", "a" * 64), "range": [1, 11],
        }])

    def test_invalid_ranges_and_source_rows_fail_closed(self):
        for invalid in ([[True, 3]], [[0, 3]], [[4, 1]], [["1", 3]], [[1]]):
            with self.subTest(interval=invalid):
                with self.assertRaisesRegex(ValueError, "malformed"):
                    G5.normalize_ranges([{"path": "a.md", "sha256": "a"*64,
                                          "ranges": invalid}])
        with self.assertRaisesRegex(ValueError, "identity"):
            G5.source_rows({"reading_plan": {"read_now": [{"path": "x"}]}}, "read_now")

    def test_gate_order_and_input_binding_are_not_name_only(self):
        a = gate("project_sync", "python sync.py --write")
        b = gate("review", "python review.py --strict")
        modified_a = gate("project_sync", "python sync.py --dry-run")
        mixed = {"pre_delivery_gates": [a, b]}
        self.assertTrue(G5.all_gate_orders_preserved(
            mixed, [{"pre_delivery_gates": [a]},
                    {"pre_delivery_gates": [b]}]))
        self.assertFalse(G5.all_gate_orders_preserved(
            mixed, [{"pre_delivery_gates": [b, a]}]))
        self.assertFalse(G5.all_gate_orders_preserved(
            mixed, [{"pre_delivery_gates": [modified_a]}]))
        self.assertTrue(G5.ordered_subsequence([], ["anything"]))

    def test_project_or_result_gates_are_never_claimed_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "checked-out source tree"):
                G5.collect(Path(tmp))
        sample = {
            "reading_plan": {"read_now": [row("a.md", 2, 3)],
                             "conditional": [dict(row("a.md", 5, 7), when="unknown")]},
            "pre_delivery_gates": [gate("project_sync", "python sync.py --write")],
            "assurance": {"status": "pass"},
        }
        got = G5.summarize(sample)
        self.assertEqual(got["conditional_sources"], 1)
        self.assertEqual(got["gates"], ["project_sync"])
        self.assertNotIn("gate_execution", got)
        self.assertNotIn("qualified_for_delivery", got)

    def test_real_two_case_probe_keeps_g2_actions_but_does_not_admit_execution(self):
        report = G5.collect(ROOT)
        self.assertEqual(report["case_count"], 2)
        self.assertFalse(report["production_narrow_read_enabled"])
        self.assertFalse(report["project_state_written"])
        for result in report["cases"]:
            with self.subTest(case=result["case_id"]):
                self.assertEqual(result["missing_actions"], [])
                self.assertEqual(result["forbidden_intents"], [])
                self.assertEqual(result["composability_admission"], "NOT_ADMITTED")
                self.assertIn("oracle_declares_cross_action_dependencies", result["reasons"])
                self.assertFalse(result["gate_execution"])
                self.assertFalse(result["read_consumption_executed"])
                self.assertTrue(result["source_sha256"])


if __name__ == "__main__":
    unittest.main()
