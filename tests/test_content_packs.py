import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASK_PACKS = [
    "mechanism", "optimization", "prediction", "evaluation", "statistics_ml",
    "simulation", "spatial", "graph_network", "scheduling", "game_decision",
]
HEADINGS = [
    "## 1. 进入条件", "## 2. 路线比较", "## 3. 变量与公式闭环",
    "## 4. 必做验证与输出", "## 5. 否决或降级条件",
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

    def test_code_pack_uses_one_self_contained_two_script_question_folder(self):
        text = (ROOT / "packs/artifact/code.md").read_text(encoding="utf-8")
        for token in (
            "问题X求解/", "问题X求解.py", "问题X求解结果.xlsx",
            "问题X结果深化分析.py", "问题X结果深化分析.xlsx", "qX_plot.m",
            "两个阶段明确的 Python 文件", "冻结", "不生成独立 YAML",
            "同目录两个真实工作簿", "精确匹配表头", "只读兼容",
        ):
            self.assertIn(token, text)
        self.assertNotIn("覆盖更新同一文件", text)

    def test_chart_selection_is_evidence_driven_and_titled(self):
        text = (ROOT / "templates/figure/chart_selection.md").read_text(encoding="utf-8")
        for token in (
            "参数敏感性", "多算法比较", "多目标权衡", "删除规则", "信息效率",
            "饼图", "雷达图", "3D 曲面", "q{x}_plot.m", "MATLAB 标题", "sgtitle",
            "模型论文框架.md",
        ):
            self.assertIn(token, text)
        self.assertIn("工作簿", text)
        self.assertNotIn("图内不重复总标题", text)

    def test_figure_pack_uses_adaptive_analysis_and_standard_script_name(self):
        pack = (ROOT / "packs/artifact/figure.md").read_text(encoding="utf-8")
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        matlab_readme = (ROOT / "templates/matlab/README.md").read_text(encoding="utf-8")
        for text in (pack, module, matlab_readme):
            self.assertIn("q{x}_plot.m", text)
            self.assertIn("title", text)
            self.assertIn("sgtitle", text)
            self.assertIn("模型论文框架.md", text)
        for text in (pack, module):
            self.assertIn("问题X求解结果.xlsx", text)
            self.assertIn("问题X结果深化分析.xlsx", text)
            self.assertIn("阈值", text)
            self.assertIn("结构稳健性", text)
        self.assertIn("高级图表准入检查", pack)
        self.assertIn("推荐主色仅作为起点，不是固定模板", module)
        self.assertIn("中高饱和、高对比", module)
        self.assertIn("q1_plot.m", matlab_readme)
        self.assertIn("q1_polt.m", matlab_readme)

    def test_model_paper_framework_is_project_memory_not_second_manual(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        for token in (
            "当前有效项目事实、选择、状态与证据位置",
            "## 当前有效口径", "## 论文整体框架", "### 命题与证明规划",
            "当前计划命题数：0", "默认正文预算：0--4", "### 核心公式 Trace",
            "### Citation Evidence", "## 各问模型与结果", "#### 当前模型口径",
            "#### 结果摘要", "MATLAB 图标题", "## 图表证据链", "正文引用位置",
            "## 同步检查",
        ):
            self.assertIn(token, text)
        self.assertIn("Git", text)
        self.assertIn("stale", text)
        self.assertNotIn("命题准入检查：", text)
        self.assertNotIn("正文证明默认：", text)

    def test_writing_consumers_delegate_proposition_governance(self):
        reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        proposition = reasoning["proposition_governance"]
        self.assertEqual(proposition["default_budget"], [0, 4])
        self.assertFalse(proposition["automatic_rejection_over_budget"])
        self.assertEqual(proposition["over_budget_action"], "justification_required")

        paths = [
            ROOT / "modules/05_writing/docx.md",
            ROOT / "modules/05_writing/latex.md",
            ROOT / "modules/05_writing/ai_cleanup.md",
            ROOT / "modules/06_review_delivery.md",
            ROOT / "packs/artifact/proposition_proof.md",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("core/writing_reasoning_contract.yaml", text, str(path))
        latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.assertIn("0--4 是**默认正文阅读预算**，不是绝对数学上限", latex)
        self.assertIn("required / inline / not_applicable", latex)

    def test_docx_checklist_is_framework_aware_without_redefining_hard_rules(self):
        writing = ROOT / "templates/writing"
        self.assertTrue((writing / "docx_check.md").is_file())
        self.assertFalse((writing / "docx_draft_check.md").exists())
        self.assertFalse((writing / "docx_layout_check.md").exists())
        module = (ROOT / "modules/05_writing/docx.md").read_text(encoding="utf-8")
        checklist = (writing / "docx_check.md").read_text(encoding="utf-8")
        self.assertIn("templates/writing/docx_check.md", module)
        self.assertIn("模型论文框架.md", module)
        self.assertIn("sgtitle", checklist)
        self.assertIn("## 3. 命题与证明", checklist)
        self.assertIn("默认 0--4 预算", checklist)
        self.assertIn("required / inline / not_applicable", checklist)
        self.assertIn("Citation Evidence", checklist)
        self.assertIn("表题是否位于表格正上方", checklist)
        self.assertIn("图题位于图片正下方", checklist)
        self.assertIn("优缺点数量是否由实际模型决定", checklist)

    def test_cumcm_hsk_template_has_budgeted_boxed_proposition_environment(self):
        text = (ROOT / "templates/latex/cumcm/hsk/hsk_main.tex").read_text(encoding="utf-8")
        self.assertIn("\\usepackage[most]{tcolorbox}", text)
        self.assertIn("\\newtheorem{proposition}{命题}[section]", text)
        self.assertIn("\\renewcommand{\\theproposition}{\\arabic{section}.\\arabic{proposition}}", text)
        self.assertIn("\\newenvironment{hskproposition}[1]", text)
        self.assertIn("\\newenvironment{hskproof}", text)
        self.assertIn("证明：", text)
        self.assertIn("0--4 是默认正文阅读预算，不是数学硬上限", text)
        self.assertIn("短证明默认自然分段", text)
        self.assertNotIn("breakable,", text)
        self.assertIn("colback=white", text)
        self.assertIn("colframe=black!72", text)

    def test_output_contract_keeps_concise_proposition_authority_pointer(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        proposition = contract["proposition_contract"]
        self.assertEqual(proposition["authority"], "core/writing_reasoning_contract.yaml#proposition_governance")
        self.assertEqual(proposition["latex_outer_environment"], "hskproposition")
        self.assertEqual(proposition["display_numbering"], "arabic_section_dot_arabic_proposition")
        self.assertEqual(proposition["default_budget"], [0, 4])
        self.assertEqual(proposition["over_budget_action"], "justification_required")
        self.assertFalse(proposition["automatic_rejection_over_budget"])
        self.assertNotIn("maximum_per_paper", proposition)

    def test_caption_template_has_no_copyable_fixed_sentence_and_requires_body_reference(self):
        text = (ROOT / "templates/writing/caption_explanation.md").read_text(encoding="utf-8")
        self.assertNotIn("由图X可知，……。这一结果说明", text)
        self.assertNotIn("由表X可知，……。该结果与", text)
        for token in ("读图结论", "关键数值", "机制解释", "显式编号引用", "图~\\ref{...}", "表~\\ref{...}"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
