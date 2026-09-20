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
            "收敛 trace",
        ):
            self.assertIn(token, primary)
        self.assertIn("是否需要改变当前主计算", primary)
        for token in ("参数敏感性", "压力场景", "替代算法", "多随机种子"):
            self.assertIn(token, analysis)
        self.assertIn("Analysis Evidence Capture", analysis)
        self.assertIn("细粒度", analysis)

    def test_starters_request_evidence_ready_outputs(self):
        starter_dir = ROOT / "templates/code/starter"
        for name in ("optimization.py", "prediction.py", "simulation.py", "classification.py", "evaluation.py"):
            text = (starter_dir / name).read_text(encoding="utf-8")
            self.assertIn("Primary Evidence Capture", text, name)
        readme = (starter_dir / "README.md").read_text(encoding="utf-8")
        self.assertIn("是否改变当前主计算条件并重新运行", readme)
        self.assertIn("Scientific Figure Synthesis", readme)
        self.assertIn("参数敏感性", readme)
        self.assertIn("主工作簿 accepted 后进入 03B", readme)

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
            "F2 互补编码表达",
            "F3 多结构综合表达",
        ):
            self.assertIn(token, module)
        self.assertIn("不按图型复杂度分级", module)
        self.assertIn("可以是正文核心 Figure", module)
        self.assertIn("不是质量排序", module)
        self.assertIn("不为填写合同凑第二候选", module)
        self.assertIn("不以 plain 图数量或占比触发返工", module)
        self.assertIn("不得设置图型种类、复杂度或 F2/F3 占比配额", module)
        self.assertNotIn("明明有更丰富证据，却只用一个普通柱状图", module)

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
        self.assertIn("核心证据覆盖检查", chart)
        self.assertIn("真实互补信息", module)
        self.assertIn("组合后更易读", module)
        for text in (module, patterns):
            self.assertIn("没有实际区间就不画", text)
            self.assertIn("没有真实配对就不画", text)
        self.assertIn("加号不表示必须凑齐组件", patterns)
        self.assertIn("相同 x/y 的线与点仍是一份证据", chart)

    def test_matlab_guidance_keeps_simple_core_figures_and_conditional_composites(self):
        readme = (ROOT / "templates/matlab/README.md").read_text(encoding="utf-8")
        q1 = (ROOT / "templates/matlab/q1_plot.m").read_text(encoding="utf-8")
        process = (ROOT / "templates/matlab/data_process.m").read_text(encoding="utf-8")
        for text in (readme, q1, process):
            self.assertIn("Basic-form Challenge", text)
            self.assertRegex(text, r"可(?:以)?直接承担核心")
            self.assertIn("真实互补信息和可读性增益", text)
            self.assertIn("没有实际区间就不画带", text)
            self.assertNotIn("优先 Composite Encoding", text)
        self.assertIn("不凑第二候选", readme)
        self.assertIn("不按 plain 图数量或占比触发返工", readme)
        self.assertIn("不强制 hero panel 或不对称布局", readme)
        self.assertNotIn("只有数据结构本身确实是一维简单比较时", readme)
        self.assertNotIn("如果大量都是 plain bar", readme)
        self.assertNotIn("按 Evidence Structure 升级", process)

    def test_explicit_legacy_palette_remains_available_without_authority_default(self):
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        profile = (ROOT / "templates/matlab/hsk_publication_profile.m").read_text(encoding="utf-8")
        style = (ROOT / "templates/matlab/hsk_apply_scientific_style.m").read_text(encoding="utf-8")
        for token in ("#1478FF", "#F04444", "#16B364", "#F79009", "#7A5AF8"):
            self.assertIn(token, profile)
        self.assertIn("不设默认配色或默认 palette profile", module)
        self.assertIn("不为单张图换色而破坏全文映射", module)
        self.assertIn("红绿不承担唯一语义", module)
        self.assertIn("palette.brightBlue = [20, 120, 255] / 255", profile)
        self.assertIn("palette.vividRed = [240, 68, 68] / 255", profile)
        self.assertIn("palette.lightGray", profile)
        self.assertIn("spec = hsk_publication_profile(profile)", style)

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
            self.assertIn("grid(ax, gridMode)", text)

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
        self.assertIn("不作质量排序，任一级均可承担核心论证", contract)
        self.assertIn("不凑第二候选", contract)
        self.assertIn("复合形式不自动代表通过", contract)
        self.assertIn("没有实际区间不画带", contract)
        self.assertIn("不补造比较", contract)


if __name__ == "__main__":
    unittest.main()
