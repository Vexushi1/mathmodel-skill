from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestNaturalPaperFlow(unittest.TestCase):
    def test_cleanup_reviews_negation_density_and_evidence_without_word_bans(self):
        text = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in (
            "本文不是……而是……", "制造无必要冲突", "核心图表",
            "Citation Evidence", "Paragraph Necessity、Model Rationale 与 Detail Allocation",
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

    def test_protocol_prefers_positive_natural_progression(self):
        text = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")
        self.assertIn("优先正向叙述", text)
        self.assertIn("科研训练初期", text)
        self.assertIn("不追求成熟期刊式概念包装", text)

    def test_result_precision_follows_prompt_and_preserves_accepted_values(self):
        text = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")
        self.assertIn("题目对数值精度有明确要求时，按题目及已核验的官方输出格式执行", text)
        self.assertIn("未明确要求时，**论文数值默认保留小数点后两位**", text)
        self.assertIn("该规则只调整论文展示，不修改 accepted 工作簿原始数值、计算精度、求解容差或提交数据", text)
        self.assertIn("**摘要中的数值精度服从题目明确要求；未明确要求时默认保留小数点后两位**", text)
        self.assertIn("特殊精度必须有题面或官方来源", text)
        self.assertNotIn("高精度评分场景常见为小数后 6--7 位", text)


if __name__ == "__main__":
    unittest.main()
