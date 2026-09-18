from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class ModelDesignCapabilityPreservationV931Tests(unittest.TestCase):
    def test_module02_restores_framework_read_write_contract(self):
        text = read("modules/02_model_design.md")
        start = text.index("## 10. `模型论文框架.md`")
        end = text.index("## 11. 机理图合同", start)
        section = text[start:end]

        ordered = [
            "框架支持：",
            "读取规则：",
            "写入规则：",
            "事实源边界：",
        ]
        positions = [section.index(token) for token in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("accepted standard workbook", section)
        self.assertIn("project state", section)
        self.assertIn("current framework", section)
        self.assertIn("Condition → Consequence / Reduction", section)
        self.assertIn("继续简化首先损失什么", section)
        self.assertIn("comparison purpose", section)

    def test_module02_restores_mechanism_contract_producer_semantics(self):
        text = read("modules/02_model_design.md")
        start = text.index("## 11. 机理图合同")
        end = text.index("## 阶段门槛", start)
        section = text[start:end]

        self.assertIn("mechanism_contracts", section)
        self.assertIn("Formula / Constraint / Proposition anchor", section)
        self.assertIn("不直接生成正式机理图", section)
        self.assertIn("不新增独立 Gate", section)

        manifest = yaml.safe_load(read("core/module_manifest.yaml"))
        outputs = manifest["modules"]["model_design"]["outputs"]
        self.assertIn("mechanism_contracts", outputs)

    def test_module02_restores_stage_gate_without_adding_new_lifecycle_gate(self):
        text = read("modules/02_model_design.md")
        start = text.index("## 阶段门槛")
        section = text[start:]

        ordered = [
            "Condition → Consequence",
            "exact / proven_sufficient reduction",
            "当前主模型已说明为什么达到最小充分",
            "Comparator Envelope",
            "solver 选择发生在结构化简和主模型闭合之后",
            "scripts/validate_model_approval.py",
            "awaiting_model_approval",
            "locked_model_spec",
        ]
        positions = [section.index(token) for token in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("设计完整性", section)
        self.assertIn("审批完整性", section)
        self.assertNotIn("Structural Reduction Gate", section)
        self.assertNotIn("Minimal Sufficient Gate", section)

    def test_framework_result_sync_selector_points_to_restored_complete_section(self):
        router = yaml.safe_load(read("core/workflow_router.yaml"))
        profile = router["reading_policy"]["profiles"]["framework_result_sync"]
        module_spec = next(
            item for item in profile["read_now"]
            if item.get("path") == "modules/02_model_design.md"
        )
        self.assertIn("## 10. `模型论文框架.md`", module_spec["headings"])

        text = read("modules/02_model_design.md")
        start = text.index("## 10. `模型论文框架.md`")
        end = text.index("## 11. 机理图合同", start)
        section = text[start:end]
        for token in ("读取规则：", "写入规则：", "事实源边界："):
            self.assertIn(token, section)

    def test_v930_structure_first_generation_order_remains_intact(self):
        text = read("modules/02_model_design.md")
        ordered = [
            "### 1.2 Condition → Consequence",
            "### 1.4 最小充分主模型",
            "### 1.5 Comparison Envelope",
            "### 1.6 Solver 必须后置且服从结构",
        ]
        positions = [text.index(token) for token in ordered]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
