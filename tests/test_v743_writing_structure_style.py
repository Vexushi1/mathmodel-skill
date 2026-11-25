from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestWritingStructureStyle(unittest.TestCase):
    def test_cleanup_is_consumer_not_second_structure_authority(self):
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        self.assertIn("modules/05_writing/latex.md", cleanup)
        self.assertIn("core/writing_reasoning_contract.yaml", cleanup)
        for token in (
            "## A. Integrity / Hard boundary",
            "## B. Evidence closure",
            "## C. Style & Necessity",
            "## D. Optional machine diagnostics",
            "数值实验", "算法百科", "逐格复述表格", "Citation Evidence",
            "Paragraph Necessity、Model Rationale 与 Detail Allocation", "机器审计不得自动重写正文",
        ):
            self.assertIn(token, cleanup)
        self.assertIn("Skill 负责原则，脚本负责穷举", cleanup)

    def test_reasoning_keeps_adaptive_core_model_summary(self):
        import yaml
        reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        summary = reasoning["adaptive_core_model_summary"]
        self.assertEqual(summary["semantic_summary_mode"]["values"], ["required", "inline", "not_applicable"])
        self.assertEqual(summary["modes"], ["required", "inline", "not_applicable"])
        self.assertEqual(summary["legacy_modes_field"]["canonical_field"], "semantic_summary_mode.values")
        self.assertEqual(reasoning["proposition_governance"]["default_budget"], [0, 4])
        protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")
        self.assertIn("displayed / inline / omitted", protocol)

    def test_proposition_pack_remains_optional(self):
        import yaml
        text = (ROOT / "packs/artifact/proposition_proof.md").read_text(encoding="utf-8")
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        contract = output["proposition_contract"]
        governance = reasoning["proposition_governance"]

        # Optional use and a hard full-paper limit are independent requirements.
        self.assertIs(contract["optional"], True)
        self.assertEqual(contract["detail_pack"], "packs/artifact/proposition_proof.md")
        self.assertEqual(contract["lazy_load_when"],
                         ["explicit_proof_request", "proposition_count_greater_than_zero"])
        self.assertIn("仅在用户明确要求命题/证明，或全文命题计划非零时加载。", text)
        self.assertEqual(contract["authority"],
                         "core/writing_reasoning_contract.yaml#proposition_governance")
        self.assertIn(contract["authority"], text)
        self.assertEqual(contract["default_budget"], [0, 4])
        self.assertEqual(governance["default_budget"], [0, 4])
        self.assertEqual(governance["governance_level"], "hard")
        self.assertEqual(governance["maximum_body_propositions"], 4)
        for rule in (contract, governance):
            self.assertEqual(rule["count_scope"], "full_paper_body")
            self.assertEqual(rule["over_budget_action"], "revise_body_plan_required")
            self.assertIs(rule["automatic_rejection_over_budget"], True)
        self.assertIn("全文正文正式命题最多 4 个，不设超额例外", text)
        self.assertIn("不构成正文超过 4 个命题的豁免", text)
        self.assertIn("核心证明和关键推导必须保持正文数学闭环", text)
        self.assertNotIn("不是绝对上限", text)
        self.assertNotIn("不自动否决", text)


if __name__ == "__main__":
    unittest.main()
