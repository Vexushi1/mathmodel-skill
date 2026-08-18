import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV740WritingEvidenceArchitecture(unittest.TestCase):
    def test_latex_authority_preserves_evidence_architecture(self):
        text = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        for token in (
            "对象几何、网络拓扑或空间层级仅靠文字难以恢复时",
            "问题分析：逐问解释难点与抓手",
            "Source → Derivation → Destination",
            "高级算法前",
            "多方法验证",
            "模型评价不能替代",
            "标题优先写研究对象、关键机制或真正的模型贡献",
            "局部证据闭环",
        ):
            self.assertIn(token, text)

    def test_cleanup_preserves_evidence_architecture_antipatterns(self):
        text = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in (
            "核心结论至少能回到公式",
            "模型评价",
            "逐格复述表格",
            "核心图表",
            "算法百科",
            "## B. Evidence closure",
            "Citation Evidence",
            "Terminology Registry",
            "Numeric Profile",
            "Title Claim Gate",
        ):
            self.assertIn(token, text)
        self.assertNotIn("## 六、引用证据清理", text)

    def test_framework_remembers_evidence_placement_without_copying_rules(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        for token in (
            "当前写作选择",
            "共享基础与跨问增量",
            "核心公式 Trace",
            "数值参数依据",
            "Citation Evidence",
            "正文章节与交付映射",
            "图表证据链",
            "Terminology Registry",
            "Numeric Profile",
            "Title Claim Gate",
            "正文局部状态映射",
        ):
            self.assertIn(token, text)
        self.assertNotIn("问题背景通常 1 个自然段", text)
        self.assertNotIn("全文命题上限", text)

    def test_output_contract_freezes_validation_evaluation_split_via_authority(self):
        data = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        policy = data["writing_policy"]
        self.assertEqual(policy["expression_authority"], "modules/05_writing/latex.md")
        self.assertEqual(policy["reasoning_contract"], "core/writing_reasoning_contract.yaml")
        authority = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.assertIn("模型评价不能替代误差", authority)
        self.assertIn("局部反转、算法分歧", authority)

    def test_core_model_summary_is_adaptive_not_removed(self):
        reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        policy = reasoning["adaptive_core_model_summary"]
        self.assertEqual(policy["modes"], ["required", "inline", "not_applicable"])
        self.assertIn("multiple_decision_or_state_variables", policy["required_when_any"])
        self.assertIn("direct_readout_or_simple_calculation_without_new_model_structure", policy["not_applicable_when"])

    def test_citation_evidence_keeps_external_and_internal_evidence_distinct(self):
        reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        citation = reasoning["citation_evidence"]
        self.assertEqual(citation["claim_types"]["own_derivation"]["citation"], "not_required")
        self.assertEqual(citation["claim_types"]["external_empirical_parameter"]["citation"], "required")
        self.assertIn("own_result_is_not_replaced_by_external_citation", citation["closure_rules"])


if __name__ == "__main__":
    unittest.main()
