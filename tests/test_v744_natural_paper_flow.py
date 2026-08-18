from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestNaturalPaperFlow(unittest.TestCase):
    def test_cleanup_reviews_negation_density_and_evidence_without_word_bans(self):
        text = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in (
            "本文不是……而是……", "制造无必要冲突", "核心图表",
            "Citation Evidence", "Paragraph Necessity Test",
            "## B. Evidence closure", "## C. Style & Necessity", "## D. Optional machine diagnostics",
        ):
            self.assertIn(token, text)

    def test_framework_remembers_current_project_writing_choices(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        for token in (
            "v0.8-project-memory", "### 当前写作选择", "正文总体结构",
            "共享基础与跨问递进", "核心模型收束状态", "特殊结构例外",
            "### 核心公式 Trace", "### Citation Evidence", "### Terminology Registry",
            "### Numeric Profile", "#### Title Claim Gate", "### Paper Fragment Dependency Map",
            "### 正文章节与交付映射",
        ):
            self.assertIn(token, text)

    def test_latex_prefers_positive_natural_progression(self):
        text = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.assertIn("优先正向叙述", text)
        self.assertIn("科研训练初期", text)
        self.assertIn("不追求成熟期刊式概念包装", text)

    def test_result_precision_is_not_reduced_for_abstract_brevity(self):
        text = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.assertIn("核心答案的精度不得为了摘要简洁而擅自降低", text)
        self.assertIn("6--7", text)


if __name__ == "__main__":
    unittest.main()
