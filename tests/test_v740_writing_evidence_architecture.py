import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV740WritingEvidenceArchitecture(unittest.TestCase):
    def test_latex_authority_contains_2024_evidence_architecture(self):
        text = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        for token in (
            "对象恢复图准入", "按作用域放置假设", "问题分析放置规则",
            "算法说明实行最小必要预算", "证据邻近原则",
            "模型检验与模型评价必须分工", "标题写研究对象、关键机制或模型贡献",
        ):
            self.assertIn(token, text)
        self.assertIn("不必机械包装成独立命题框", text)

    def test_framework_remembers_evidence_placement_without_fixed_assumption_quota(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        self.assertIn("v0.5-evidence-architecture", text)
        for token in ("对象恢复图", "假设组织", "局部证据闭环", "模型检验安排", "算法说明预算"):
            self.assertIn(token, text)
        self.assertNotIn("1. 假设一：原因、影响、失效偏差和检验方式", text)

    def test_output_contract_freezes_validation_evaluation_split(self):
        data = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        policy = data["writing_policy"]
        self.assertEqual(data["version"], "7.4.0")
        self.assertTrue(policy["model_validation_precedes_evaluation"])
        self.assertFalse(policy["standalone_model_evaluation_required"])
        self.assertTrue(policy["assumption_scope_localization_required"])
        self.assertTrue(policy["local_evidence_closure_preferred"])
        self.assertEqual(policy["generic_algorithm_background_budget"], "minimal_task_specific")

    def test_cleanup_has_evidence_architecture_antipatterns(self):
        text = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in ("标题去软件化", "摘要去实现清单化", "假设去全局滥用", "检验与评价去混淆", "证据邻近检查"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
