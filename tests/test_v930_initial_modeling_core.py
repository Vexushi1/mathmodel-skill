from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class InitialModelingCoreV930Tests(unittest.TestCase):
    def test_model_design_is_condition_driven_before_solver(self):
        text = read("modules/02_model_design.md")
        ordered = [
            "Condition → Consequence",
            "最小充分主模型",
            "Comparison Envelope",
            "Solver 必须后置且服从结构",
        ]
        positions = [text.index(token) for token in ordered]
        self.assertEqual(positions, sorted(positions))

    def test_classic_plus_advanced_routes_are_no_longer_mandatory(self):
        text = read("modules/02_model_design.md")
        self.assertNotIn("每问至少构造两条实质路线", text)
        self.assertIn("不再要求“每问至少经典稳健 + 高级创新两条路线”", text)
        self.assertIn("对照模型数量为 `0..N`", text)

    def test_main_model_is_defined_as_minimal_sufficient_not_merely_simple(self):
        text = read("modules/02_model_design.md")
        self.assertIn("当前最小充分模型", text)
        self.assertIn("更简单模型会失去题面必要机制、精度、可行域或输出能力，则它不是最小充分模型", text)

    def test_advanced_models_remain_available_as_main_or_comparator(self):
        text = read("modules/02_model_design.md")
        self.assertIn("高级模型完全可以作为高保真参照", text)
        self.assertIn("作为主模型时", text)
        self.assertIn("作为正式定量 comparator 时", text)

    def test_existing_reduction_provenance_is_reused(self):
        text = read("modules/02_model_design.md")
        for token in ("exact", "proven_sufficient", "heuristic"):
            self.assertIn(token, text)
        self.assertIn("writing_reasoning_contract.model_construction_rationale.reduction_language", text)

    def test_no_new_lifecycle_gate_is_declared(self):
        core = read("core/hsk_core_policy.md")
        router = read("RUNTIME_ROUTER.md")
        self.assertIn("Model Reviewer", router)
        self.assertIn("Devil's Advocate", router)
        self.assertIn("Human Model Approval", router)
        self.assertIn("pre_delivery_gates", core)
        self.assertNotIn("Structural Reduction Gate", core)
        self.assertNotIn("Minimal Sufficient Gate", core)

    def test_classifier_does_not_map_structure_directly_to_advanced_model(self):
        text = read("packs/task/classifier.md")
        self.assertIn("不直接推出模型名称、算法等级或复杂度", text)
        self.assertIn("`network` 不自动推出 GNN", text)
        self.assertIn("高级方法不是题型标签，也不是默认第二路线", text)

    def test_root_and_packaged_skill_remain_identical(self):
        self.assertEqual(read("SKILL.md"), read("skills/mathmodel-skill/SKILL.md"))


if __name__ == "__main__":
    unittest.main()
