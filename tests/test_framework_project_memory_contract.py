from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class FrameworkProjectMemoryContractTests(unittest.TestCase):
    def test_router_declares_project_memory_contract(self) -> None:
        router = yaml.safe_load(read("core/workflow_router.yaml"))
        contract = router.get("project_memory_contract", {})
        self.assertEqual(contract.get("artifact"), "model_paper_framework")
        self.assertEqual(contract.get("project_file"), "模型论文框架.md")
        self.assertEqual(contract.get("numeric_fact_source"), "accepted_standard_workbooks")
        self.assertEqual(contract.get("machine_state_source"), "state/project_state.yaml")
        modules = set(contract.get("read_before_modules", []))
        for required in {"data_preprocessing", "solve_validate", "result_analysis", "figure_evidence", "writing_latex", "review_delivery"}:
            self.assertIn(required, modules)
        self.assertIn("cross_chat_handoff", contract.get("full_read_when", []))
        self.assertIn("full_paper_writing", contract.get("full_read_when", []))

    def test_downstream_modules_explicitly_read_framework(self) -> None:
        checks = {
            "modules/03_data_preprocessing.md": "先读取全局数据协议",
            "modules/03_solve_validate.md": "正式生成本问代码前必须先读取",
            "modules/03_result_analysis.md": "制定分析计划前先读取",
            "modules/04_figure_evidence.md": "进入本模块时先读取 current `模型论文框架.md`",
            "modules/05_writing/latex.md": "必须读取完整 current `模型论文框架.md`",
        }
        for relative, marker in checks.items():
            self.assertIn(marker, read(relative), relative)

    def test_framework_is_memory_not_numeric_database(self) -> None:
        for relative in ("core/bootstrap.yaml", "core/hsk_core_policy.md", "PROJECT_INSTRUCTIONS.md", "SKILL.md"):
            text = read(relative)
            self.assertIn("模型论文框架.md", text, relative)
        policy = read("core/hsk_core_policy.md")
        self.assertIn("read-before-use / write-after-change", policy)
        self.assertIn("工作簿是数值事实源", policy)
        self.assertIn("project state 是机器状态源", policy)

    def test_framework_template_declares_memory_role_and_current_paths(self) -> None:
        template = read("templates/model/model_paper_framework.md")
        self.assertIn("助手的项目级长期工作记忆", template)
        self.assertIn("`问题一求解/q1_plot.m`", template)
        self.assertNotIn("`结果数据表/问题一/q1_plot.m`", template)
        self.assertIn("结果深化分析工作簿", template)

    def test_agent_entry_uses_framework_for_context_recovery(self) -> None:
        text = read("AGENTS.md")
        self.assertIn("assistant-readable project memory", text)
        self.assertIn("instead of reconstructing the model from chat memory", text)


if __name__ == "__main__":
    unittest.main()
