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

    def test_chart_selection_is_evidence_driven(self):
        text = (ROOT / "templates/figure/chart_selection.md").read_text(encoding="utf-8")
        for token in ("参数敏感性", "鲁棒性与扰动", "多算法比较", "多目标权衡", "删除规则"):
            self.assertIn(token, text)
        self.assertIn("工作簿", text)

    def test_docx_checklists_are_merged(self):
        writing = ROOT / "templates/writing"
        self.assertTrue((writing / "docx_check.md").is_file())
        self.assertFalse((writing / "docx_draft_check.md").exists())
        self.assertFalse((writing / "docx_layout_check.md").exists())
        module = (ROOT / "modules/05_writing/docx.md").read_text(encoding="utf-8")
        self.assertIn("templates/writing/docx_check.md", module)

    def test_caption_template_has_no_copyable_fixed_sentence(self):
        text = (ROOT / "templates/writing/caption_explanation.md").read_text(encoding="utf-8")
        self.assertNotIn("由图X可知，……。这一结果说明", text)
        self.assertNotIn("由表X可知，……。该结果与", text)
        for token in ("读图结论", "关键数值", "机制解释", "这些是信息结构"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()