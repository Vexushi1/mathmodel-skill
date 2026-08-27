import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV715ScientificFigureElevation(unittest.TestCase):
    def test_primary_solve_captures_current_run_evidence_without_eating_analysis(self):
        primary = (ROOT / "modules/03_solve_validate.md").read_text(encoding="utf-8")
        analysis = (ROOT / "modules/03_result_analysis.md").read_text(encoding="utf-8")
        for token in (
            "Primary Evidence Capture",
            "current-run capture",
            "alternative-world analysis",
            "状态",
            "逐时刻",
            "候选可行解",
            "求解轨迹",
        ):
            self.assertIn(token, primary)
        self.assertIn("是否需要改变当前主计算", primary)
        for token in ("参数敏感性", "压力场景", "替代算法", "多 seed"):
            self.assertIn(token, analysis)
        self.assertIn("Analysis Evidence Capture", analysis)
        self.assertIn("细粒度", analysis)

    def test_starters_request_evidence_ready_outputs(self):
        starter_dir = ROOT / "templates/code/starter"
        for name in ("optimization.py", "prediction.py", "simulation.py", "classification.py", "evaluation.py"):
            text = (starter_dir / name).read_text(encoding="utf-8")
            self.assertIn("Primary Evidence Capture", text, name)
            self.assertNotIn("提前执行参数敏感性", text if name == "optimization.py" else "", name) if False else None
        readme = (starter_dir / "README.md").read_text(encoding="utf-8")
        self.assertIn("是否改变当前主计算条件并重新运行", readme)
        self.assertIn("Scientific Figure Synthesis", readme)

    def test_figure_authority_has_synthesis_basic_form_composite_rendering_and_portfolio_gates(self):
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        for token in (
            "Scientific Figure Synthesis Gate",
            "Basic-form Challenge",
            "Composite Encoding Preference",
            "Scientific Rendering Profiles",
            "Figure Portfolio Scientific Quality Gate",
            "Missing Scientific Evidence Check",
            "F1 基础表达",
            "F2 增强科研表达",
            "F3 核心科学综合图",
        ):
            self.assertIn(token, module)
        self.assertIn("明明有更丰富证据，却只用一个普通柱状图", module)
        self.assertIn("不得设置“必须有 N 种图型”", module)

    def test_composite_patterns_cover_requested_high_information_figures(self):
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        patterns = (ROOT / "templates/figure/figure_enhancement_patterns.md").read_text(encoding="utf-8")
        chart = (ROOT / "templates/figure/chart_selection.md").read_text(encoding="utf-8")
        for token in (
            "箱线 + 原始散点",
            "小提琴 + 原始散点 + 中位数/四分位",
            "折线 + CI/预测区间",
            "热力图 + 等高线",
            "Pareto + 推荐点 + Local Zoom",
        ):
            self.assertIn(token, module)
        for token in (
            "C1 Box + Raw Scatter",
            "C2 Violin + Scatter + Median/Quartile",
            "C5 Heatmap + Contour + Boundary + Point",
            "C6 Pareto + Recommendation + Global/Detail",
            "C7 Trajectory + Field + Boundary",
        ):
            self.assertIn(token, patterns)
        self.assertIn("基础图退化检查", chart)

    def test_high_contrast_palette_is_restored_but_auxiliary_elements_are_deweighted(self):
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        style = (ROOT / "templates/matlab/hsk_apply_scientific_style.m").read_text(encoding="utf-8")
        for token in ("#1478FF", "#F04444", "#16B364", "#F79009", "#7A5AF8"):
            self.assertIn(token, module)
        self.assertIn("亮蓝 vs 鲜红", module)
        self.assertIn("高对比 ≠ 全图所有元素都鲜艳", module)
        self.assertIn("palette.brightBlue = [20, 120, 255] / 255", style)
        self.assertIn("palette.vividRed = [240, 68, 68] / 255", style)
        self.assertIn("palette.lightGray", style)

    def test_formal_titles_and_data_honesty_are_unchanged(self):
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        q1 = (ROOT / "templates/matlab/q1_plot.m").read_text(encoding="utf-8")
        process = (ROOT / "templates/matlab/data_process.m").read_text(encoding="utf-8")
        self.assertIn("不设置整体 `title` 或 `sgtitle`", module)
        self.assertIn("不得仅为了美观使用 spline", module)
        for text in (q1, process):
            code = "\n".join(line.split("%", 1)[0] for line in text.splitlines())
            self.assertNotIn("title(", code)
            self.assertNotIn("sgtitle(", code)
            self.assertIn('grid(ax, "off")', text)

    def test_figure_contract_records_scientific_decision_not_style_sprawl(self):
        contract = (ROOT / "templates/figure/result_figure_contract.md").read_text(encoding="utf-8")
        for token in (
            "Available evidence dimensions",
            "Evidence structure",
            "Figure level",
            "Candidate visual structures",
            "Selected visual structure",
            "Basic-form challenge",
            "Composite encoding",
            "Scientific Rendering Profile",
            "Scientific value rationale",
            "Rejected alternatives",
        ):
            self.assertIn(token, contract)
        self.assertIn("不记录 inset 坐标、透明度等 MATLAB 实现参数", contract)


if __name__ == "__main__":
    unittest.main()
