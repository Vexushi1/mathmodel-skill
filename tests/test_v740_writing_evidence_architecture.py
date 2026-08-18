import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestWritingEvidenceArchitecture(unittest.TestCase):
    def test_cleanup_preserves_evidence_architecture(self):
        text = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in (
            "核心数值", "逐格复述表格", "核心图表", "算法百科",
            "## B. Evidence closure", "Citation Evidence", "Terminology Registry",
            "Numeric Profile", "Title Claim", "Paragraph Necessity Test",
        ):
            self.assertIn(token, text)
        self.assertNotIn("## 六、引用证据清理", text)

    def test_framework_remembers_evidence_placement_without_copying_manual(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        for token in (
            "Formula Trace", "Citation Evidence", "正文章节与交付映射", "图表证据链",
            "Terminology Registry", "Numeric Profile", "Title Claim Gate", "Paper Fragment Dependency Map",
        ):
            self.assertIn(token, text)
        self.assertNotIn("问题背景通常 1 个自然段", text)

    def test_latex_authority_closes_local_result_evidence(self):
        text = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        for token in ("局部证据闭环", "高精度关键数值", "显式编号引用", "support", "modify", "reject"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
