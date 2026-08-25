from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".py", ".m", ".tex", ".txt", ".json"}
OBSOLETE_ACTIVE_TEMPLATE_MARKERS = ("v6.6.0",)


class TestActiveTemplateVersionHygiene(unittest.TestCase):
    def test_active_template_index_has_no_obsolete_release_marker(self) -> None:
        index_text = (ROOT / "TEMPLATE_INDEX.md").read_text(encoding="utf-8")
        relative_paths = sorted(set(re.findall(r"`(templates/[^`]+)`", index_text)))
        self.assertTrue(relative_paths)
        for relative in relative_paths:
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in OBSOLETE_ACTIVE_TEMPLATE_MARKERS:
                self.assertNotIn(marker, text, relative)

    def test_historical_v660_marker_remains_legacy_only(self) -> None:
        legacy = ROOT / "legacy" / "v660_self_contained_output_migration.md"
        self.assertTrue(legacy.is_file())
        self.assertIn("v6.6.0", legacy.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
