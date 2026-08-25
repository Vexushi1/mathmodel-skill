from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROOT_SKILL = ROOT / "SKILL.md"
PACKAGED_SKILL = ROOT / "skills/mathmodel-skill/SKILL.md"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def skill_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"missing frontmatter: {path}")
    return yaml.safe_load(text.split("---\n", 2)[1]) or {}


def assert_order(test: unittest.TestCase, text: str, tokens: list[str]) -> None:
    positions = []
    for token in tokens:
        pos = text.find(token)
        test.assertGreaterEqual(pos, 0, token)
        positions.append(pos)
    test.assertEqual(positions, sorted(positions), tokens)


class RuntimeHealthCoherenceTests(unittest.TestCase):
    def test_root_and_packaged_skill_are_fully_identical(self):
        self.assertEqual(ROOT_SKILL.read_text(encoding="utf-8"), PACKAGED_SKILL.read_text(encoding="utf-8"))

    def test_skill_discovery_covers_high_frequency_intents(self):
        triggers = set(skill_frontmatter(ROOT_SKILL).get("triggers", []))
        required = {"审题", "建模思路", "建模方案", "完整求解", "结果分析", "终审", "提交包"}
        self.assertFalse(required - triggers, sorted(required - triggers))

    def test_subordinate_contract_versions_are_introduction_metadata(self):
        for relative in (
            "core/global_preprocessing_contract.yaml",
            "core/user_execution_contract.yaml",
            "core/code_quality_contract.yaml",
        ):
            data = yaml.safe_load(read(relative)) or {}
            self.assertNotIn("skill_version", data, relative)
            self.assertEqual(str(data.get("introduced_in_skill_version")), "7.4.2", relative)
            self.assertEqual(str(data.get("skill_compatibility")), ">=7.4.2,<8.0.0", relative)

    def test_preprocessing_lifecycle_authority_is_explicit(self):
        data = yaml.safe_load(read("core/global_preprocessing_contract.yaml")) or {}
        position = data.get("workflow_position", {})
        self.assertEqual(position.get("decision_stage"), "model_design")
        self.assertEqual(position.get("decision_after"), "data_audit_and_model_route_selection")
        self.assertEqual(position.get("decision_before"), "proposed_model_spec_and_model_challenge")
        self.assertEqual(position.get("project_level_stage_after"), "human_model_approval")
        self.assertEqual(position.get("before"), "solve_validate")

    def test_skill_main_chain_preserves_preprocessing_lifecycle(self):
        text = ROOT_SKILL.read_text(encoding="utf-8")
        block = text.split("## 主链", 1)[1].split("目录、正式交付", 1)[0]
        assert_order(self, block, [
            "通用数据审计",
            "两条模型路线与数据需求比较",
            "preprocessing_decision",
            "proposed_model_spec",
            "Model Reviewer + Devil's Advocate",
            "locked_model_spec",
        ])

    def test_runtime_router_preserves_preprocessing_lifecycle(self):
        text = read("RUNTIME_ROUTER.md")
        block = text.split("## 概念上的完整工作流", 1)[1].split("## Algorithm Trace 路由边界", 1)[0]
        assert_order(self, block, [
            "两条模型路线/数据需求比较",
            "preprocessing_decision",
            "proposed_model_spec",
            "Model Reviewer",
            "locked_model_spec",
            "按 preprocessing_decision 分流",
        ])

    def test_primary_solve_flow_preserves_gate_order(self):
        text = read("modules/03_solve_validate.md")
        block = text.split("```text\n题意口径冻结", 1)[1].split("```", 1)[0]
        assert_order(self, block, [
            "模型路线/输入需求比较",
            "preprocessing_decision",
            "Independent Model Challenge",
            "Human Model Approval",
            "semantic governance gate",
            "model approval gate",
            "生成问题X求解.py",
            "validate_code_delivery.py",
        ])


if __name__ == "__main__":
    unittest.main()
