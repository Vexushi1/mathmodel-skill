from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV730WritingExpressionProtocol(unittest.TestCase):
    def test_latex_module_is_shared_expression_authority(self):
        text = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.assertIn("正文结构与表达权威", text)
        self.assertIn("core/writing_reasoning_contract.yaml", text)
        self.assertIn("Hard", text)
        self.assertIn("Default", text)
        self.assertIn("Recommendation", text)
        for token in ("问题重述", "问题分析", "模型假设", "符号说明", "求解结果", "模型评价"):
            self.assertIn(token, text)

    def test_docx_and_cleanup_reference_shared_authority(self):
        latex = "modules/05_writing/latex.md"
        reasoning = "core/writing_reasoning_contract.yaml"
        for relative in ("modules/05_writing/docx.md", "modules/05_writing/ai_cleanup.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(latex, text, relative)
            self.assertIn(reasoning, text, relative)
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        self.assertIn("不建立第二套正文写作规则", cleanup)

    def test_output_contract_points_to_shared_authorities(self):
        data = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        policy = data["writing_policy"]
        self.assertEqual(policy["expression_authority"], "modules/05_writing/latex.md")
        self.assertEqual(policy["reasoning_contract"], "core/writing_reasoning_contract.yaml")
        self.assertEqual(policy["rule_governance"], "core/writing_reasoning_contract.yaml#rule_governance")
        self.assertEqual(policy["citation_evidence_contract"], "core/writing_reasoning_contract.yaml#citation_evidence")
        self.assertEqual(policy["core_model_summary_policy"], "adaptive_required_inline_not_applicable")

    def test_framework_records_project_specific_writing_choices_only(self):
        framework = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        self.assertIn("### 当前写作选择", framework)
        self.assertIn("正文总体结构", framework)
        self.assertIn("核心模型收束状态", framework)
        self.assertIn("特殊结构例外", framework)
        self.assertIn("这里只记录**本项目的实际选择**", framework)
        self.assertNotIn("命题准入检查：", framework)

    def test_cleanup_preserves_current_anti_template_protocol(self):
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in (
            "算法百科",
            "本文/本问/该模型",
            "揭示、表征、耦合",
            "## B. Evidence closure",
            "## C. Style & necessity",
            "Citation Evidence",
            "Terminology Registry",
            "Numeric Profile",
            "BibTeX",
            "Paragraph Necessity Test",
        ):
            self.assertIn(token, cleanup)
        self.assertIn("Skill 负责原则，脚本负责穷举", cleanup)
        self.assertNotIn("## 六、引用证据清理", cleanup)

    def test_ai_cleanup_keeps_machine_semantic_boundary(self):
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in ("数学正确性", "参数最优性", "文献质量", "语义支持"):
            self.assertIn(token, cleanup)


if __name__ == "__main__":
    unittest.main()
