"""Behavioral regressions for default paper drafts and explicit review carriers."""
import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_runtime():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("resolve_runtime", ROOT / "scripts/resolve_runtime.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PaperRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = load_runtime()
        cls.router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))

    def assert_route_matches_explicit(self, resolve, request, intent):
        plan = resolve(request=request, competition="CUMCM")
        expected = resolve(intent, competition="CUMCM")
        for field in ("intents", "delivery_scope", "modules", "terminal_outputs", "pre_delivery_gates"):
            self.assertEqual(plan[field], expected[field], (request, field))
        self.assertFalse(plan["task_code_execution_allowed"])
        return plan

    def test_generic_paper_drafts_reach_latex_with_existing_outputs_and_gates(self):
        for request in ("请写论文草稿", "请写草稿论文", "用 LaTeX 写论文草稿"):
            for resolve in (self.runtime.resolve_runtime, self.runtime.resolve_workflow):
                with self.subTest(request=request, resolver=resolve.__name__):
                    plan = self.assert_route_matches_explicit(resolve, request, "latex")
                    self.assertIn("core/writing_runtime_contract.yaml", plan["load_order"])
                    self.assertIn("latex_source", plan["terminal_outputs"])
                    self.assertNotIn("docx_draft", plan["terminal_outputs"])
                    if resolve is self.runtime.resolve_runtime:
                        stages = [stage["id"] for stage in plan["writing_runtime"]["authoring_sequence"]]
                        self.assertLess(stages.index("draft_semantic_review"), stages.index("ai_cleanup"))
                        self.assertLess(stages.index("ai_cleanup"), stages.index("latex_assembly_audit_and_compile"))

    def test_explicit_word_docx_survive_accumulated_generic_paper_keywords(self):
        requests = (
            "请写 Word 论文草稿", "请写 Word论文草稿", "输出 DOCX 草稿论文",
            "输出DOCX草稿论文", "用 word 写论文草稿",
            "用 Word 写论文草稿、草稿论文并编译论文、形成终稿论文",
        )
        for request in requests:
            for resolve in (self.runtime.resolve_runtime, self.runtime.resolve_workflow):
                with self.subTest(request=request, resolver=resolve.__name__):
                    plan = self.assert_route_matches_explicit(resolve, request, "docx")
                    self.assertIn("docx_draft", plan["terminal_outputs"])
                    self.assertNotIn("latex_source", plan["terminal_outputs"])

    def test_explicit_api_paper_intent_overrides_opposite_carrier_keywords(self):
        for intent, request in (("docx", "用 LaTeX 写论文草稿"), ("latex", "用 Word 写论文草稿")):
            for resolve in (self.runtime.resolve_runtime, self.runtime.resolve_workflow):
                with self.subTest(intent=intent, resolver=resolve.__name__):
                    plan = resolve(intent, request=request, competition="CUMCM")
                    expected = resolve(intent, competition="CUMCM")
                    self.assertEqual(plan["intents"], [intent])
                    self.assertEqual(plan["delivery_scope"], intent)
                    self.assertEqual(plan["pre_delivery_gates"], expected["pre_delivery_gates"])
                    self.assertEqual(plan["terminal_outputs"], expected["terminal_outputs"])
                    if resolve is self.runtime.resolve_runtime:
                        self.assertEqual(plan["assurance"]["intent_resolution"]["confidence_score"], 1.0)

    def test_two_explicit_carriers_keep_existing_specificity_and_legacy_multi_intent(self):
        request = "用 Word 和 LaTeX 写论文草稿"
        plan = self.runtime.resolve_runtime(request=request, competition="CUMCM")
        diagnostics = plan["assurance"]["intent_resolution"]
        candidates = {row["intent"]: row for row in diagnostics["inferred_candidates"]}
        self.assertEqual(set(candidates), {"docx", "latex"})
        self.assertGreater(candidates["latex"]["score"], candidates["docx"]["score"])
        self.assertEqual(plan["intents"], ["latex"])
        legacy = self.runtime.resolve_workflow(request=request, competition="CUMCM")
        self.assertEqual(set(legacy["intents"]), {"latex", "docx"})

    def test_bare_drafts_and_ascii_substrings_do_not_create_paper_routes(self):
        for request in ("请润色这份草稿", "请改代码注释草稿", "password", "wording", "WordCount", "xDOCXy"):
            for resolve in (self.runtime.resolve_runtime, self.runtime.resolve_workflow):
                with self.subTest(request=request, resolver=resolve.__name__):
                    with self.assertRaisesRegex(ValueError, "no workflow intent resolved"):
                        resolve(request=request)
        for resolve in (self.runtime.resolve_runtime, self.runtime.resolve_workflow):
            self.assert_route_matches_explicit(resolve, "请写 password 的论文草稿", "latex")
            self.assert_route_matches_explicit(resolve, "请修复 pdflatex 编译", "latex")

    def test_carrier_disambiguation_does_not_override_unrelated_routes(self):
        selected, _ = self.runtime.resolve_intent_assurance([], "请终审并评分审稿 Word 文档", self.router)
        self.assertEqual(selected, ["review"])
        for intent, request in (("full_workflow", "请完成全流程"), ("review", "请终审论文检查"),
                                ("algorithm_presentation", "请写论文算法伪代码")):
            for resolve in (self.runtime.resolve_runtime, self.runtime.resolve_workflow):
                with self.subTest(intent=intent, resolver=resolve.__name__):
                    plan = resolve(request=request, objective="optimization", competition="CUMCM")
                    expected = resolve(intent, objective="optimization", competition="CUMCM")
                    for field in ("intents", "delivery_scope", "pre_delivery_gates", "pause_for_model_approval",
                                  "pause_for_user_execution", "task_code_execution_allowed"):
                        self.assertEqual(plan[field], expected[field], field)

    def test_legacy_explicit_paper_override_preserves_other_inferred_intents(self):
        plan = self.runtime.resolve_workflow("latex", request="Word论文草稿并展示伪代码", competition="CUMCM")
        self.assertEqual(set(plan["intents"]), {"latex", "algorithm_presentation"})


if __name__ == "__main__":
    unittest.main()
