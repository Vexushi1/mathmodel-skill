import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestWritingEvidenceArchitecture(unittest.TestCase):
    def test_cleanup_preserves_evidence_architecture(self):
        text = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in (
            "核心数值", "逐格复述表格", "核心图表", "算法百科",
            "## B. Evidence closure", "Citation Evidence", "Terminology Registry",
            "Numeric Profile", "Title Claim", "Paragraph Necessity、Model Rationale 与 Detail Allocation",
        ):
            self.assertIn(token, text)
        self.assertNotIn("## 六、引用证据清理", text)

    def test_table_and_figure_readability_is_preserved_without_changing_facts(self):
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")
        caption = (ROOT / "templates/writing/caption_explanation.md").read_text(encoding="utf-8")
        checklist = (ROOT / "templates/writing/docx_check.md").read_text(encoding="utf-8")

        for token in (
            "图题/表题负责识别对象和范围",
            "accepted 数值",
            "绝对/相对误差",
            "baseline",
        ):
            self.assertIn(token, cleanup)

        for token in (
            "表格首先要能独立读懂",
            "一张表通常服务一个主要比较问题",
            "不得改 accepted workbook 数值",
            "图题说明对象、关系、范围",
        ):
            self.assertIn(token, protocol)

        for token in (
            "内部 run id",
            "指标若优劣方向不显然",
            "accepted 数值",
            "过宽表",
        ):
            self.assertIn(token, caption)

        self.assertIn("图表可读性修改是否未改变数值", checklist)
        self.assertIn("表格解释是否抓关键差异", checklist)

    def test_framework_remembers_evidence_placement_without_copying_manual(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        for token in (
            "Formula Trace", "Citation Evidence", "正文章节与交付映射", "图表证据链",
            "Terminology Registry", "Numeric Profile", "Title Claim Gate", "Paper Fragment Dependency Map",
        ):
            self.assertIn(token, text)
        self.assertNotIn("问题背景通常 1 个自然段", text)

    def test_protocol_closes_local_result_evidence(self):
        text = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")
        for token in ("局部证据闭环", "高精度关键数值", "显式编号引用", "support", "modify", "reject"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
