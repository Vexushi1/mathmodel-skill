"""Safety and comparability tests for G4-B test-only Markdown heading index."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reading_plan as READING
import g4b_selector_index_probe as PROBE


class G4BSelectorIndexProbeTests(unittest.TestCase):
    def test_two_distinct_selectors_same_reader_reuse_exact_heading_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "source.md"
            path.write_text(
                "# Introduction\nGlobal.\n## A\nAlpha.\n## B\nBeta.\n",
                encoding="utf-8",
            )
            specs = [
                {"path": "source.md", "headings": ["## A"]},
                {"path": "source.md", "headings": ["## B"]},
                {"path": "source.md", "headings": ["## A"]},
            ]
            baseline = READING.SourceReader(root)
            before = [baseline.describe(spec) for spec in specs]
            index = PROBE.HeadingIndex("test_only_index")
            with mock.patch.object(READING, "_headings", side_effect=index.headings), \
                 mock.patch.object(READING.SourceReader, "describe", autospec=True,
                                   side_effect=index.describe):
                indexed = READING.SourceReader(root)
                after = [indexed.describe(spec) for spec in specs]
            self.assertEqual(before, after)
            self.assertEqual(index.heading_requests, 3)
            self.assertEqual(index.heading_builds, 1)
            self.assertEqual(index.index_hits, 2)
            self.assertEqual(index.counts()["index_entries"], 1)

    def test_changed_source_and_different_reader_never_reuse_stale_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "source.md"
            spec = {"path": "source.md", "headings": ["## A"]}
            index = PROBE.HeadingIndex("test_only_index")
            with mock.patch.object(READING, "_headings", side_effect=index.headings), \
                 mock.patch.object(READING.SourceReader, "describe", autospec=True,
                                   side_effect=index.describe):
                path.write_text("# A\n## A\nold\n", encoding="utf-8")
                original_reader = READING.SourceReader(root)
                first = original_reader.describe(spec)
                path.write_text("# A\n## A\nnew text\n", encoding="utf-8")
                fresh_reader = READING.SourceReader(root)
                second = fresh_reader.describe(spec)
                self.assertNotEqual(first["sha256"], second["sha256"])
                self.assertNotEqual(first["planned_bytes"], second["planned_bytes"])
            self.assertEqual(index.heading_builds, 2)
            self.assertEqual(index.index_hits, 0)

    def test_ambiguous_markdown_and_yaml_fallback_stay_original(self):
        documents = (
            ("source.md", "# H\n## Repeat\none\n## Repeat\ntwo\n",
             {"headings": ["## Repeat"]}),
            ("source.md", "# H\n~~~\n## Fake\n~~~\n",
             {"headings": ["## Fake"]}),
            ("source.yaml", "base: &v {a: 1}\nchild: *v\n",
             {"yaml_paths": ["base.a"]}),
            ("source.yaml", "base: 1\nbase: 2\n",
             {"yaml_paths": ["base"]}),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path, data, selectors in documents:
                (root / path).write_text(data, encoding="utf-8")
                spec = {"path": path, **selectors}
                expected = READING.SourceReader(root).describe(spec)
                index = PROBE.HeadingIndex("test_only_index")
                with mock.patch.object(READING, "_headings", side_effect=index.headings), \
                     mock.patch.object(READING.SourceReader, "describe", autospec=True,
                                       side_effect=index.describe):
                    actual = READING.SourceReader(root).describe(spec)
                self.assertEqual(expected, actual)
                self.assertEqual(actual["resolution"], "whole_file_fallback")
                self.assertEqual(actual["planned_bytes"], actual["source_bytes"])

    def test_bounds_and_out_of_scope_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "unknown G4-B"):
            PROBE.HeadingIndex("different")
        for repeats in (0, 6):
            with self.assertRaisesRegex(ValueError, "repeats"):
                PROBE.collect(ROOT, repeats)
        with tempfile.TemporaryDirectory() as foreign:
            with self.assertRaisesRegex(ValueError, "checked-out source tree"):
                PROBE.collect(Path(foreign), 1)

    def test_stateless_real_resolver_plan_equal_and_no_production_cache(self):
        report = PROBE.collect(ROOT, repeats=1)
        self.assertTrue(report["no_production_changes"])
        self.assertEqual(len(report["cases"]), 2)
        self.assertEqual(set(report["source_sha256"]), set(PROBE.SOURCES))
        for case in report["cases"]:
            self.assertTrue(case["full_plan_equal"])
            modes = case["runs"][0]
            self.assertEqual(set(modes), set(PROBE.MODES))
            self.assertEqual(
                modes["existing"]["full_plan_sha256"],
                modes["test_only_index"]["full_plan_sha256"],
            )
            for mode in PROBE.MODES:
                self.assertGreaterEqual(modes[mode]["markdown_heading_requests"], 0)
                self.assertGreaterEqual(modes[mode]["yaml_selector_scan_calls"], 0)
                self.assertGreaterEqual(modes[mode]["yaml_selector_compose_calls"], 0)
            self.assertEqual(modes["existing"]["markdown_index_hits"], 0)


if __name__ == "__main__":
    unittest.main()
