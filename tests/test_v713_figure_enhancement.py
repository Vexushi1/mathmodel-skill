import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV713FigureEnhancement(unittest.TestCase):
    def test_module_keeps_single_authority_and_exposes_enhancement_gate(self):
        text = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        for token in (
            "## Figure Enhancement Gate",
            "Local Zoom",
            "Small Multiples",
            "Focus Highlighting",
            "Semantic Background",
            "Composite Diagnostic",
            "Conditional 3D",
            "默认状态为 `none`",
            "不得仅为了美观使用 spline",
        ):
            self.assertIn(token, text)
        self.assertIn("同一视觉层级中同时竞争注意力的主要对象通常不超过 2--3 个", text)
        self.assertIn("一张 Figure 可以包含多个 axes", text)

    def test_pattern_template_is_implementation_only(self):
        text = (ROOT / "templates/figure/figure_enhancement_patterns.md").read_text(
            encoding="utf-8"
        )
        for token in (
            "Z1 Embedded inset",
            "Z2 Detached zoom",
            "Z3 Selective detail",
            "Z4 ROI + semantic zoom",
            "Overview + detail",
            "Composite Diagnostic",
            "Conditional 3D",
            "Data Honesty",
            "不建立第二套绘图决策权威",
        ):
            self.assertIn(token, text)

    def test_router_loads_patterns_for_figures_and_full_workflow_resume(self):
        router = yaml.safe_load(
            (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")
        )
        pattern = "templates/figure/figure_enhancement_patterns.md"
        self.assertEqual(router["version"], "7.13.0")
        self.assertIn(pattern, router["routing"]["figures"]["load"])
        self.assertIn(pattern, router["runtime_segments"]["full_workflow_resume"]["final_load"])

    def test_contract_and_qa_record_enhancement_without_parameter_sprawl(self):
        contract = (ROOT / "templates/figure/result_figure_contract.md").read_text(
            encoding="utf-8"
        )
        qa = (ROOT / "templates/figure/result_figure_qa.md").read_text(encoding="utf-8")
        self.assertIn("| Enhancement |", contract)
        self.assertIn("| Enhancement rationale |", contract)
        self.assertIn("不记录 inset 坐标、透明度等 MATLAB 实现参数", contract)
        for token in (
            "Local Zoom",
            "Small Multiples",
            "Focus Highlighting",
            "Semantic Background",
            "Composite Diagnostic / 3D",
            "避免为美观对离散点擅自平滑",
        ):
            self.assertIn(token, qa)

    def test_pack_delegates_and_chart_index_exposes_problems(self):
        pack = (ROOT / "packs/artifact/figure.md").read_text(encoding="utf-8")
        chart = (ROOT / "templates/figure/chart_selection.md").read_text(encoding="utf-8")
        self.assertIn("唯一权威为 `modules/04_figure_evidence.md`", pack)
        self.assertIn("只提供实现参考，不拥有独立决策权", pack)
        self.assertIn("## Figure Enhancement 快速索引", chart)
        self.assertIn("全局尺度压缩关键差异", chart)
        self.assertIn("多条曲线大量交叉", chart)
        self.assertIn("第三维具有真实结构", chart)


if __name__ == "__main__":
    unittest.main()
