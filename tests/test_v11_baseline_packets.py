"""Acceptance of the maintenance packet and its separation from evaluation material."""

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v11_web_app_packet import CATALOG, FIXTURES, export_packet, packet_files


class WebAppPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = yaml.safe_load(CATALOG.read_bytes())["cases"]
        cls.rubric = yaml.safe_load((FIXTURES / "v11_web_app_rubric.yaml").read_bytes())

    def test_each_turn_has_a_distinct_evaluation_and_exportable_inputs(self):
        ids = [case["id"] for case in self.cases]
        scored_ids = [case["id"] for case in self.rubric["cases"]]
        self.assertCountEqual(ids, scored_ids)
        self.assertEqual(len(ids), len(set(ids)))
        for case in self.cases:
            scored = next(item for item in self.rubric["cases"] if item["id"] == case["id"])
            self.assertEqual(len(case["turns"]), len(scored["turns"]))
            for turn, (inputs, scoring) in enumerate(zip(case["turns"], scored["turns"]), 1):
                with self.subTest(case=case["id"], turn=turn):
                    self.assertTrue(scoring["criteria"])
                    self.assertTrue(all(isinstance(v, str) and v.strip() for v in scoring["criteria"].values()))
                    files = packet_files(case["id"], turn)
                    self.assertEqual(files["用户请求.txt"].decode().strip(), inputs["prompt"].strip())
                    self.assertFalse(any("v11_web_app_rubric" in p or p.startswith("tests/") for p in files))
                    self.assertNotIn((FIXTURES / "v11_web_app_rubric.yaml").read_bytes(), files.values())

    def test_export_is_reproducible_and_preserves_prior_packet(self):
        with TemporaryDirectory() as directory:
            first, second = (Path(directory) / n for n in ("first.zip", "second.zip"))
            for case in self.cases:
                for index in range(1, len(case["turns"]) + 1):
                    with self.subTest(case=case["id"], turn=index):
                        expected = export_packet(case["id"], index, first)
                        self.assertEqual(export_packet(case["id"], index, second), expected)
                        self.assertEqual(sha256(first.read_bytes()).hexdigest(), expected)
                        with ZipFile(first) as archive:
                            self.assertEqual({p: archive.read(p) for p in archive.namelist()}, packet_files(case["id"], index))
                        with self.assertRaises(FileExistsError):
                            export_packet(case["id"], index, first)
                        self.assertEqual(first.read_bytes(), second.read_bytes())
                        first.unlink()
                        second.unlink()

    def test_invalid_case_or_turn_cannot_export_another_turn(self):
        for case, number in (("unknown-case", 1), ("intake", 0), ("intake", 999)):
            with self.subTest(case=case, turn=number), self.assertRaises(ValueError):
                packet_files(case, number)
