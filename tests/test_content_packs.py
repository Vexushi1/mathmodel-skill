import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_PACKS = [
    "mechanism",
    "optimization",
    "prediction",
    "evaluation",
    "statistics_ml",
    "simulation",
    "spatial",
    "graph_network",
    "scheduling",
    "game_decision",
]
HEADINGS = [
    "## 1. 进入条件",
    "## 2. 路线比较",
    "## 3. 变量与公式闭环",
    "## 4. 必做验证与输出",
    "## 5. 否决或降级条件",
]


class TestContentPacks(unittest.TestCase):
    def test_task_packs_are_executable(self):
        for name in TASK_PACKS:
            path = ROOT / "packs" / "task" / f"{name}.md"
            text = path.read_text(encoding="utf-8")
            for heading in HEADINGS:
                self.assertIn(heading, text, f"{path}: {heading}")
            self.assertGreaterEqual(len(text.splitlines()), 20, str(path))

    def test_advanced_method_gate_is_separate_from_classifier_labels(self):
        gate = (ROOT / "packs/task/advanced_method_gate.md").read_text(encoding="utf-8")
        classifier = (ROOT / "packs/task/classifier.md").read_text(encoding="utf-8")
        self.assertIn("七项硬门槛", gate)
        self.assertIn("不是题型标签", classifier)
        self.assertIn("advanced_method_gate.md", classifier)

    def test_chart_selection_is_evidence_driven_and_titled(self):
        text = (ROOT / "templates/figure/chart_selection.md").read_text(encoding="utf-8")
        for token in (
            "参数敏感性",
            "鲁棒性与扰动",
            "多算法比较",
            "多目标权衡",
            "删除规则",
            "信息效率",
            "饼图",
            "雷达图",
            "3D 曲面",
            "q{x}_plot.m",
            "MATLAB 标题",
            "sgtitle",
            "模型论文框架.md",
        ):
            self.assertIn(token, text)
        self.assertIn("工作簿", text)
        self.assertIn("均允许使用", text)
        self.assertNotIn("图内不重复总标题", text)

    def test_figure_pack_uses_efficiency_gate_titles_and_standard_script_name(self):
        pack = (ROOT / "packs/artifact/figure.md").read_text(encoding="utf-8")
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        matlab_readme = (ROOT / "templates/matlab/README.md").read_text(encoding="utf-8")
        for text in (pack, module, matlab_readme):
            self.assertIn("q{x}_plot.m", text)
            self.assertIn("信息", text)
            self.assertIn("title", text)
            self.assertIn("sgtitle", text)
            self.assertIn("模型论文框架.md", text)
        self.assertIn("高级图表准入检查", pack)
        self.assertIn("颜色不是固定约束", module)
        self.assertIn("q1_plot.m", matlab_readme)
        self.assertIn("q1_polt.m", matlab_readme)
        for text in (pack, module, matlab_readme):
            self.assertNotIn("图题由 LaTeX 图注承担", text)

    def test_model_paper_framework_template_is_current_state_and_complete(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        for token in (
            "只保留当前有效口径",
            "## 当前有效口径",
            "## 论文整体框架",
            "### 命题与证明规划",
            "全文命题上限：4",
            "当前计划命题数：0",
            "证明等级",
            "模型作用",
            "失效边界",
            "正文证明默认",
            "同一个外框",
            "流程图和机理图的彩色框限制不适用于命题证明环境",
            "## 各问模型与结果",
            "#### 结果摘要",
            "MATLAB 图标题",
            "## 图表证据链",
            "## 同步检查",
        ):
            self.assertIn(token, text)
        self.assertIn("Git", text)
        self.assertIn("stale", text)

    def test_writing_modules_enforce_optional_max_four_propositions(self):
        paths = [
            ROOT / "modules/05_writing/docx.md",
            ROOT / "modules/05_writing/latex.md",
            ROOT / "modules/05_writing/ai_cleanup.md",
            ROOT / "modules/06_review_delivery.md",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertTrue("最多 4" in text or "不得超过 4" in text, str(path))
            self.assertIn("失效边界", text, str(path))
            self.assertTrue("同一个外框" in text or "同一外框" in text, str(path))
            self.assertIn("2--6", text, str(path))
        latex = paths[1].read_text(encoding="utf-8")
        self.assertIn("hskproposition", latex)
        self.assertIn("hskproof", latex)

    def test_docx_checklists_are_merged_and_framework_aware(self):
        writing = ROOT / "templates/writing"
        self.assertTrue((writing / "docx_check.md").is_file())
        self.assertFalse((writing / "docx_draft_check.md").exists())
        self.assertFalse((writing / "docx_layout_check.md").exists())
        module = (ROOT / "modules/05_writing/docx.md").read_text(encoding="utf-8")
        checklist = (writing / "docx_check.md").read_text(encoding="utf-8")
        self.assertIn("templates/writing/docx_check.md", module)
        self.assertIn("模型论文框架.md", module)
        self.assertIn("sgtitle", checklist)
        self.assertIn("## 2. 命题与证明", checklist)
        self.assertIn("不超过 4", checklist)
        self.assertIn("同一个外框", checklist)
        self.assertIn("流程图、机理图的彩色框限制", checklist)

    def test_cumcm_hsk_template_has_boxed_concise_proposition_environment(self):
        text = (ROOT / "templates/latex/cumcm/hsk/hsk_main.tex").read_text(encoding="utf-8")
        self.assertIn("\\usepackage[most]{tcolorbox}", text)
        self.assertIn("\\newtheorem{proposition}{命题}[section]", text)
        self.assertIn("\\newenvironment{hskproposition}[1]", text)
        self.assertIn("\\newenvironment{hskproof}", text)
        self.assertIn("证明：", text)
        self.assertIn("正文默认使用短证明", text)
        self.assertIn("全文命题总数不得超过 4", text)
        self.assertIn("colback=white", text)
        self.assertIn("shadow", text.lower() if "shadow" in text.lower() else "shadow")

    def test_output_contract_has_boxed_concise_proposition_contract(self):
        import yaml

        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        proposition = contract["proposition_contract"]
        self.assertEqual(proposition["latex_outer_environment"], "hskproposition")
        self.assertEqual(proposition["main_text_default_proof_level"], "outline")
        self.assertEqual(proposition["main_text_key_steps_min"], 2)
        self.assertEqual(proposition["main_text_key_steps_max"], 6)
        display = proposition["display_contract"]
        self.assertTrue(display["single_outer_box"])
        self.assertTrue(display["statement_and_proof_in_same_box"])
        self.assertFalse(display["flowchart_or_mechanism_color_rule_applies"])

    def test_caption_template_has_no_copyable_fixed_sentence(self):
        text = (ROOT / "templates/writing/caption_explanation.md").read_text(encoding="utf-8")
        self.assertNotIn("由图X可知，……。这一结果说明", text)
        self.assertNotIn("由表X可知，……。该结果与", text)
        for token in ("读图结论", "关键数值", "机制解释", "这些是信息结构"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
