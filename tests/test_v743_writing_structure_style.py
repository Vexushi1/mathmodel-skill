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
            "Paragraph Necessity 与 Detail Allocation", "机器审计不得自动重写正文",
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
        text = (ROOT / "packs/artifact/proposition_proof.md").read_text(encoding="utf-8")
        self.assertIn("core/writing_reasoning_contract.yaml", text)
        self.assertIn("0--4", text)
        self.assertNotIn("超过 4 个直接否决", text)


if __name__ == "__main__":
    unittest.main()
