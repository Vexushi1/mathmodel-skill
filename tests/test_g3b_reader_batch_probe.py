"""Bounded G3B experiment cannot claim omitted source/Gate status."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g3b_reader_batch_probe as B

ROOT = Path(__file__).resolve().parents[1]


class G3BReadPilotTests(unittest.TestCase):
    def test_limits_are_strict(self):
        self.assertLessEqual(B.CHUNKS_PER_FILE, 4)
        self.assertLessEqual(B.MAX_SOURCE_BYTES, 65536)
        self.assertGreater(B.CHUNK_LINES, 0)

    def test_unknown_source_is_not_selected(self):
        with self.assertRaisesRegex(ValueError, "not uniquely selected"):
            B.chosen_rows({"reading_plan": {"read_now": [], "conditional": []}},
                          ROOT, ("core/unknown.md",))

    def test_identical_enforces_text_source_and_gate(self):
        row = {"path": "core/source.md", "ranges": [[1, 2]]}
        chunk = {"path": "core/source.md", "source_commit": "a"*40,
                 "source_sha256": "b"*64, "source_blob_sha": None,
                 "start_line": 1, "end_line": 2, "text": "x\ny\n"}
        expected = {"chunks": [chunk], "gate_status": "not_executed_by_reader",
                    "coverage": {"core/source.md": {
                        "complete": True, "missing_ranges": [], "issues": []}}}
        B.identical([chunk], expected, [row])
        with self.assertRaisesRegex(AssertionError, "differs"):
            B.identical([chunk], dict(expected, chunks=[]), [row])
        wrong = {**expected, "coverage": {"core/source.md": {
            "complete": False, "missing_ranges": [[2, 2]], "issues": []}}}
        with self.assertRaisesRegex(AssertionError, "coverage"):
            B.identical([chunk], wrong, [row])
        with self.assertRaisesRegex(AssertionError, "Gate"):
            B.identical([chunk], dict(expected, gate_status="passed"), [row])

    def test_batch_fails_unlisted_input_before_source_read(self):
        with mock.patch.object(B.ACTIVE, "verify_checkout", return_value="a"*40), \
             mock.patch.object(B.ACTIVE, "verify_plan_context", return_value=None):
            with self.assertRaisesRegex(ValueError, "not uniquely selected"):
                B.grouped_probe({"reading_plan": {"read_now": [], "conditional": []}},
                                ROOT, "a"*40, paths=("not_listed",))

    def test_production_reader_remains_unchanged(self):
        self.assertTrue(callable(B.ACTIVE.extract))
        self.assertFalse(hasattr(B.ACTIVE, "extract_batch"))
        self.assertIn("not a runtime API", B.__doc__)


if __name__ == "__main__":
    unittest.main()
