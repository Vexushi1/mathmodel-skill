from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "legacy"


class TestLegacyArchiveHygiene(unittest.TestCase):
    def test_legacy_readme_covers_every_top_level_archive_entry(self) -> None:
        text = (LEGACY / "README.md").read_text(encoding="utf-8")
        entries = sorted(path.name for path in LEGACY.iterdir() if path.name != "README.md")
        for name in entries:
            self.assertIn(f"`{name}", text, name)

    def test_v660_migration_targets_current_five_file_interface(self) -> None:
        text = (LEGACY / "v660_self_contained_output_migration.md").read_text(encoding="utf-8")
        for token in (
            "问题X求解.py",
            "问题X结果深化分析.py",
            "问题X求解结果.xlsx",
            "问题X结果深化分析.xlsx",
            "qX_plot.m",
        ):
            self.assertIn(token, text)
        self.assertIn("两个独立 Python", text)
        self.assertNotIn("在同一个 `问题X求解.py` 中加入结果深化分析阶段", text)

    def test_v621_release_pointer_does_not_claim_old_runtime_is_current(self) -> None:
        text = (LEGACY / "releases/v6.2.1/README.md").read_text(encoding="utf-8")
        self.assertIn("current `core/bootstrap.yaml`", text)
        self.assertNotIn("Current execution uses the v6.2.2 entries", text)

    def test_legacy_paper_docs_point_to_archive_tools(self) -> None:
        readme = (LEGACY / "papers/README.md").read_text(encoding="utf-8")
        report = (LEGACY / "papers/_DOWNLOAD_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("legacy/tools/ingest_papers.py", readme)
        self.assertNotIn("python scripts/ingest_papers.py", readme)
        self.assertNotIn("references/papers/", readme)
        self.assertNotIn("references/winning_patterns.md", readme)
        self.assertIn("legacy/tools/download_cumcm_papers.py", report)
        self.assertIn("legacy/tools/ingest_papers.py", report)
        self.assertNotIn("`scripts/download_cumcm_papers.py`", report)

    def test_only_legacy_readme_is_active_indexed(self) -> None:
        index = (ROOT / "SKILL_FILE_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("`legacy/README.md`", index)
        self.assertNotIn("`legacy/v660_self_contained_output_migration.md`", index)
        self.assertNotIn("`legacy/papers/README.md`", index)
        self.assertNotIn("`legacy/releases/v6.2.1/README.md`", index)

    def test_docs_branches_can_refresh_generated_metadata(self) -> None:
        workflow = (ROOT / ".github/workflows/refresh-generated.yml").read_text(encoding="utf-8")
        self.assertIn('- "docs/**"', workflow)


if __name__ == "__main__":
    unittest.main()
