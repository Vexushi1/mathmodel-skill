import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV800V720Regression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = yaml.safe_load(
            (ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml").read_text(encoding="utf-8")
        )
        cls.protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")
        cls.question = (ROOT / "templates/latex/cumcm/hsk/sections/06_question1.tex").read_text(encoding="utf-8")
        cls.runtime = yaml.safe_load((ROOT / "core/writing_runtime_contract.yaml").read_text(encoding="utf-8"))
        cls.surface = yaml.safe_load((ROOT / "config/prose_audit_patterns.yaml").read_text(encoding="utf-8"))

    def test_cumcm_question_title_stays_locked(self):
        question = self.manifest["cumcm_question_section"]
        self.assertEqual(question["title_pattern"], "问题{N}模型建立及求解")
        self.assertTrue(question["title_locked"])
        self.assertIn(r"\section{问题一模型建立及求解}", self.question)

    def test_four_stage_chain_is_functional_not_literal(self):
        question = self.manifest["cumcm_question_section"]
        self.assertEqual(question["functional_slots"], ["model", "solve", "result", "validate"])
        self.assertEqual(question["internal_structure"], "adaptive")
        self.assertIn("MODEL → SOLVE → RESULT → VALIDATE", self.protocol)
        self.assertIn("认知功能", self.protocol)
        self.assertIn("简单解析或直接计算问题", self.protocol)

    def test_local_narrative_and_handoff_are_first_class(self):
        self.assertIn("Local Narrative Chain", self.protocol)
        self.assertIn("previous_output", self.protocol)
        self.assertIn("current_gap", self.protocol)
        self.assertIn("current_operation", self.protocol)
        self.assertIn("current_output", self.protocol)
        self.assertIn("next_use", self.protocol)
        self.assertIn("Paragraph Handoff Test", self.protocol)

    def test_result_validation_bridge_is_required_when_validation_is_separate(self):
        self.assertIn("Result → Validation Bridge", self.protocol)
        self.assertIn("当前结果已经回答什么", self.protocol)
        self.assertIn("仍可能受哪个因素影响", self.protocol)
        self.assertIn("下一段检验什么", self.protocol)

    def test_optimization_summary_renders_objective_outside_brace(self):
        rendering = self.manifest["core_model_summary_rendering"]["optimization_example"]
        self.assertTrue(rendering["objective_separate_display"])
        self.assertTrue(rendering["constraints_separate_display"])
        self.assertFalse(rendering["objective_inside_constraint_brace"])
        self.assertNotIn(r"\subsection{核心模型汇总}", self.question)
        self.assertLess(self.question.index(r"\min_{\mathbf{x}}"), self.question.index(r"\text{s.t.}\quad"))

    def test_internal_workflow_firewall_and_surface_style_are_preserved(self):
        terms = set(self.runtime["runtime_vocabulary_firewall"]["do_not_surface_as_paper_vocabulary"])
        for term in ("主工作簿", "质量门", "深化分析", "support", "modify", "reject", "accepted", "stale"):
            self.assertIn(term, terms)
        self.assertIn("decorative_chinese_quotes", self.surface)
        self.assertIn("concept_chain", self.surface)

    def test_page_length_is_diagnostic_not_generation_target(self):
        self.assertIn("页数只作为覆盖度诊断", self.protocol)
        self.assertIn("不为达到目标页数", self.protocol)


if __name__ == "__main__":
    unittest.main()
