"""D2 route navigation never executes retrieval or grants artifact qualification."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from resolve_runtime import resolve_runtime


class CaseMemoryRoutingTests(unittest.TestCase):
    def guarded_resolve(self, intent, **kwargs):
        original = Path.open
        corpus = (ROOT / "knowledge/case_memory").resolve()

        def open_path(path, *args, **options):
            if path.resolve().is_relative_to(corpus):
                raise AssertionError("Routing read the case corpus.")
            return original(path, *args, **options)

        with patch.object(Path, "open", open_path):
            return resolve_runtime(intent, **kwargs)

    def test_explicit_retrieval_navigates_without_loading_cases_or_granting_success(self):
        plan = self.guarded_resolve("case_memory_retrieve")
        self.assertEqual(plan["modules"], [])
        self.assertEqual(plan["pre_delivery_gates"], [])
        self.assertNotIn("model_paper_framework", plan["terminal_outputs"])
        self.assertFalse(plan["task_code_execution_allowed"])
        reading = plan["reading_plan"]
        self.assertEqual(reading["profile"], "case_memory_retrieve")
        self.assertEqual([tool["name"] for tool in reading["tool_interfaces"]], ["case_memory_retrieval"])
        self.assertFalse(any(row["path"].startswith("knowledge/case_memory/") for row in reading["read_now"]))
        self.assertFalse(any(row.get("artifact") == "case_memory_retrieval_report"
                             for row in plan["assurance"]["artifact_assurance"]["evidence"]))

    def test_ordinary_model_design_neither_reads_corpus_nor_adds_retrieval_gate(self):
        plan = self.guarded_resolve("model_selection", objective="optimization", structures=[])
        self.assertNotIn("case_memory_retrieval", [gate["name"] for gate in plan["pre_delivery_gates"]])
        self.assertNotIn("case_memory_retrieval", [tool["name"] for tool in plan["reading_plan"]["tool_interfaces"]])
        self.assertFalse(any(path.startswith("knowledge/case_memory/") for path in plan["load_order"]))

    def test_mixed_intents_keep_original_gate_order_and_only_add_navigation(self):
        base = self.guarded_resolve("model_selection", objective="optimization", structures=[])
        mixed = self.guarded_resolve(["model_selection", "case_memory_retrieve"],
                                     objective="optimization", structures=[])
        self.assertEqual(mixed["pre_delivery_gates"], base["pre_delivery_gates"])
        self.assertEqual(mixed["modules"], base["modules"])
        self.assertEqual(mixed["assurance"]["artifact_assurance"], base["assurance"]["artifact_assurance"])
        self.assertEqual(sum(tool["name"] == "case_memory_retrieval"
                             for tool in mixed["reading_plan"]["tool_interfaces"]), 1)
        self.assertEqual(mixed["reading_plan"]["profile"], "full")

    def test_case_words_in_general_model_request_do_not_implicitly_enable_retrieval(self):
        plan = self.guarded_resolve("model_selection", request="选择当前模型，案例题名仅作背景",
                                    objective="optimization", structures=[])
        self.assertEqual(plan["intents"], ["model_selection"])
        self.assertNotIn("case_memory_retrieval", [tool["name"] for tool in plan["reading_plan"]["tool_interfaces"]])


if __name__ == "__main__":
    unittest.main()
