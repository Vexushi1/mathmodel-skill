from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class FrameworkProjectMemoryContractTests(unittest.TestCase):
    def test_router_declares_project_memory_contract(self):
        router = yaml.safe_load(read("core/workflow_router.yaml"))
        contract = router["project_memory_contract"]
        self.assertEqual(contract["project_file"], "模型论文框架.md")
        self.assertEqual(contract["numeric_fact_source"], "accepted_standard_workbooks")
        self.assertEqual(contract["machine_state_source"], "state/project_state.yaml")
        rules = "\n".join(str(item) for item in contract.get("rules", []))
        self.assertIn("paper_framework.sync_status", rules)
        self.assertIn("accepted primary results, result analysis or figure evidence", rules)

    def test_framework_is_memory_not_numeric_database(self):
        policy = read("core/hsk_core_policy.md")
        self.assertIn("助手可读工作记忆", policy)
        self.assertIn("已验收工作簿", policy)
        self.assertIn("state/project_state.yaml", policy)

    def test_v08_framework_keeps_project_specific_semantic_registries(self):
        template = read("templates/model/model_paper_framework.md")
        self.assertIn("v0.8-project-memory", template)
        for token in (
            "### Terminology Registry",
            "### Numeric Profile",
            "#### Title Claim Gate",
            "### Paper Fragment Dependency Map",
            "### 核心公式 Trace",
            "### Citation Evidence",
            "**深化证据处置**",
            "### 正文章节与交付映射",
            "图表证据链",
        ):
            self.assertIn(token, template)
        self.assertIn("具体数值必须回到已验收标准工作簿复核", template)
        self.assertNotIn("问题背景通常 1 个自然段", template)

    def test_framework_uses_current_question_directory_mapping(self):
        template = read("templates/model/model_paper_framework.md")
        self.assertIn("`问题一求解/q1_plot.m`", template)
        self.assertNotIn("`结果数据表/问题一/q1_plot.m`", template)
        self.assertIn("深化分析工作簿", template)

    def test_writing_route_reads_framework_before_downstream_use(self):
        router = yaml.safe_load(read("core/workflow_router.yaml"))
        read_before = set(router["project_memory_contract"]["read_before_modules"])
        for module in ("result_analysis", "figure_evidence", "writing_latex", "review_delivery"):
            self.assertIn(module, read_before)


if __name__ == "__main__":
    unittest.main()
