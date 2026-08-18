from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestWritingExpressionProtocol(unittest.TestCase):
    def test_latex_module_is_shared_expression_authority(self):
        text = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.assertIn("正文结构与表达权威", text)
        self.assertIn("core/writing_reasoning_contract.yaml", text)
        for token in ("Hard", "Default", "Recommendation", "问题重述", "问题分析", "求解结果", "Numeric Style Contract"):
            self.assertIn(token, text)

    def test_docx_and_cleanup_reference_shared_authorities(self):
        latex = "modules/05_writing/latex.md"
        reasoning = "core/writing_reasoning_contract.yaml"
        for relative in ("modules/05_writing/docx.md", "modules/05_writing/ai_cleanup.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(latex, text, relative)
            self.assertIn(reasoning, text, relative)
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        self.assertIn("不建立第二套正文写作规则", cleanup)

    def test_output_contract_points_to_shared_authorities(self):
        policy = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))["writing_policy"]
        self.assertEqual(policy["expression_authority"], "modules/05_writing/latex.md")
        self.assertEqual(policy["reasoning_contract"], "core/writing_reasoning_contract.yaml")
        self.assertEqual(policy["rule_governance"], "core/writing_reasoning_contract.yaml#rule_governance")
        self.assertEqual(policy["citation_evidence_contract"], "core/writing_reasoning_contract.yaml#citation_evidence")
        self.assertEqual(policy["core_model_summary_policy"], "adaptive_required_inline_not_applicable")

    def test_framework_records_project_specific_writing_choices_only(self):
        framework = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        for token in ("### 当前写作选择", "正文总体结构", "核心模型收束状态", "特殊结构例外"):
            self.assertIn(token, framework)
        self.assertIn("这里只记录**本项目的实际选择**", framework)
        self.assertNotIn("命题准入检查：", framework)

    def test_cleanup_is_layered_consumer_not_second_manual(self):
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in (
            "## A. Integrity / Hard boundary",
            "## B. Evidence closure",
            "## C. Style & Necessity",
            "## D. Optional machine diagnostics",
            "Skill 负责原则，脚本负责穷举",
            "算法百科", "本文/本问/该模型", "Terminology Registry", "Numeric Profile", "Citation Evidence", "BibTeX",
        ):
            self.assertIn(token, cleanup)
        self.assertNotIn("99.", cleanup)

    def test_cleanup_keeps_machine_semantic_boundary(self):
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in ("数学正确性", "参数最优性", "术语语义等价", "物理/统计准确性", "语义支持"):
            self.assertIn(token, cleanup)


if __name__ == "__main__":
    unittest.main()
