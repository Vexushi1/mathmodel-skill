import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV740WritingEvidenceArchitecture(unittest.TestCase):
    def test_latex_authority_preserves_evidence_architecture(self):
        text = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        for token in (
            "对象几何、网络拓扑、空间区域或复杂层级仅靠文字难以恢复时",
            "局部假设只在对应问题首次使用前说明",
            "问题分析：国赛式逐问分析，不写公式和结果",
            "通用遗传算法、粒子群、差分进化",
            "能直接验证局部结论的误差图、残差、灵敏度",
            "模型评价不能替代模型检验",
            "标题写研究对象、关键机制或模型贡献",
        ):
            self.assertIn(token, text)
        self.assertIn("普通局部性质", text)
        self.assertIn("不机械升级为正式命题", text)

    def test_framework_remembers_evidence_placement_without_fixed_assumption_quota(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        self.assertIn("v0.6-reasoning-architecture", text)
        for token in (
            "对象恢复图",
            "假设组织",
            "局部证据闭环",
            "模型检验安排",
            "算法说明预算",
            "核心公式链索引",
            "跨问模型增量",
        ):
            self.assertIn(token, text)
        self.assertNotIn("1. 假设一：原因、影响、失效偏差和检验方式", text)

    def test_output_contract_freezes_validation_evaluation_split(self):
        data = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        policy = data["writing_policy"]
        self.assertEqual(data["version"], "7.5.1")
        self.assertTrue(policy["model_validation_precedes_evaluation"])
        self.assertFalse(policy["standalone_model_evaluation_required"])
        self.assertTrue(policy["assumption_scope_localization_required"])
        self.assertTrue(policy["local_evidence_closure_preferred"])
        self.assertEqual(policy["generic_algorithm_background_budget"], "minimal_task_specific")
        self.assertTrue(policy["figure_table_text_reference_required"])
        self.assertTrue(policy["affirmative_statement_preferred"])
        self.assertEqual(policy["default_model_evaluation_section"], "模型的评价与推广")
        self.assertEqual(policy["prose_audit_script"], "scripts/audit_paper_prose.py")

    def test_cleanup_preserves_evidence_architecture_antipatterns(self):
        text = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in (
            "问题重述去复制化", "摘要第一段压缩", "假设去万能化",
            "模型检验与模型评价分工明确", "证据邻近检查", "成稿机器审计",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
