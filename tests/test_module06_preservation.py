"""P3 migration preserves business text rather than blessing new layout hashes."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from module06_sources import (
    BASELINE_PATH, CANONICAL_PATHS, CONTENT, ENTRY, FINAL, ROOT, SECTION_SOURCES,
    PHASE_C_CONTENT_REVIEW_REWRITES,
    assert_preserved_review, baseline_text, historical_review_text, review_text,
    split_sections,
)
from r1_continuity_reference import prior_r1_text
from r3_concision_reference import prior_r3_text
from writing_slimming_reference import prior_writing_slimming_text


class Module06PreservationTests(unittest.TestCase):
    def copied_sources(self, destination: Path) -> None:
        for relative in (*CANONICAL_PATHS, BASELINE_PATH):
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, path)

    def test_all_eleven_business_sections_reconstruct_the_exact_old_document(self):
        self.assertEqual(len(SECTION_SOURCES), 11)
        self.assertEqual(assert_preserved_review(), baseline_text())

    def test_new_leaf_sections_have_only_their_declared_business_ownership(self):
        for path in (CONTENT, FINAL):
            with self.subTest(path=path):
                _, sections = split_sections((ROOT / path).read_text(encoding="utf-8"))
                self.assertEqual(
                    [heading for heading, _ in sections],
                    [heading for heading, owner in SECTION_SOURCES if owner == path],
                )

    def test_old_business_sections_are_not_duplicated_in_compatibility_stubs(self):
        # Verify current canonical ownership before the historical projection.
        # A duplicated approved hunk, an unchanged duplicated section, or an
        # unauthorized rewrite must still fail the original preservation checks.
        live = review_text()
        for heading, owner in SECTION_SOURCES:
            with self.subTest(current_heading=heading):
                _, owned = split_sections((ROOT / owner).read_text(encoding="utf-8"))
                matches = [body for key, body in owned if key == heading]
                self.assertEqual(len(matches), 1)
                self.assertEqual(live.count(matches[0]), 1)
        combined = "\n".join(
            prior_writing_slimming_text(
                path, prior_r1_text(path, prior_r3_text(path, (ROOT / path).read_text(encoding="utf-8")))
            )
            for path in CANONICAL_PATHS
        ) + "\n"
        _, sections = split_sections(baseline_text())
        for heading, body in sections:
            with self.subTest(heading=heading):
                canonical_body = body
                if heading == "## 二、题意、框架与局部 stale 审查":
                    for current, previous in PHASE_C_CONTENT_REVIEW_REWRITES:
                        self.assertEqual(canonical_body.count(previous), 1)
                        canonical_body = canonical_body.replace(previous, current, 1)
                self.assertEqual(combined.count(canonical_body), 1)

    def test_missing_leaf_or_section_does_not_restore_text_from_the_fixture(self):
        for relative in (CONTENT, FINAL):
            with self.subTest(missing_file=relative), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.copied_sources(root)
                (root / relative).unlink()
                with self.assertRaises(FileNotFoundError):
                    historical_review_text(root)
        for heading, relative in SECTION_SOURCES:
            with self.subTest(missing_section=heading), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.copied_sources(root)
                path = root / relative
                text = path.read_text(encoding="utf-8")
                _, sections = split_sections(text)
                section = next(body for key, body in sections if key == heading)
                path.write_text(text.replace(section, "", 1), encoding="utf-8")
                with self.assertRaises(ValueError):
                    historical_review_text(root)

    def test_duplicate_canonical_heading_is_not_silently_selected(self):
        for heading, relative in SECTION_SOURCES:
            with self.subTest(heading=heading), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.copied_sources(root)
                path = root / relative
                text = path.read_text(encoding="utf-8")
                path.write_text(text + "\n" + heading + "\nDuplicate.\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    historical_review_text(root)

    def test_changed_business_text_is_not_masked_by_an_unchanged_entry(self):
        for relative, original in (
            (CONTENT, "数学错误回上游修复，不能由风格润色掩盖。"),
            (FINAL, "不得抽样几个章节就宣称全文通过"),
            (ENTRY, "或尚未完成本次交付所需的实际审阅。"),
        ):
            with self.subTest(path=relative), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.copied_sources(root)
                path = root / relative
                text = path.read_text(encoding="utf-8")
                self.assertEqual(text.count(original), 1)
                path.write_text(text.replace(original, "unauthorized weakening", 1), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "business text differs"):
                    assert_preserved_review(root)


if __name__ == "__main__":
    unittest.main()
