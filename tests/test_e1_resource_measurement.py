"""Behavior checks for bounded, honest E1 maintenance resource observations."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import measure_e1_resources as evidence


class E1ResourceMeasurementTests(unittest.TestCase):
    def test_real_fixed_fixture_observes_off_without_corpus_reads_and_on_with_current_bindings(self):
        report = evidence.measure(repeats=1)
        self.assertEqual(report["source_head"], report["checkout_commit"])
        self.assertRegex(report["checkout_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(report["inputs_sha256"], evidence.digest(evidence.canonical(report["inputs"])))
        self.assertEqual(report["driver_sha256"], evidence.digest((ROOT / "scripts/measure_e1_resources.py").read_bytes()))
        self.assertEqual(report["independent_modeling_quality"], "not_assessed")
        self.assertEqual(report["solver_performance"], "not_assessed")
        self.assertIn("no_prefrozen", report["performance_gate"])
        rows = {row["id"]: row for row in report["rows"]}
        for name in ("ordinary_route_extensions_off", "explicit_retrieval_off"):
            sample = rows[name]["samples"][0]
            self.assertEqual(sample["observed_corpus_open_calls"], 0)
            self.assertFalse(sample["execution_authorized"])
            self.assertEqual(rows[name]["retrieval_read_set"], {})
        enabled = rows["explicit_retrieval_on"]
        self.assertGreater(enabled["samples"][0]["observed_corpus_open_calls"], 0)
        self.assertTrue(enabled["retrieval_read_set"]["corpus"])
        self.assertTrue(enabled["retrieval_read_set"]["skill"])
        self.assertEqual(enabled["retrieval_bindings"]["query_sha256"], evidence.digest(evidence.canonical(evidence.QUERY)))
        self.assertGreater(rows["ordinary_route_extensions_off"]["declared_skill_resource_bytes"], 0)
        for row in report["rows"]:
            sample = row["samples"][0]
            self.assertGreaterEqual(sample["elapsed_ns"], 0)
            self.assertGreaterEqual(sample["python_allocation_peak_bytes"], 0)
            self.assertGreater(sample["returned_utf8_bytes"], 0)

    def test_boolean_or_unbounded_repeat_request_fails_before_reading_inputs(self):
        with patch.object(evidence, "source_snapshot", side_effect=AssertionError("must not read")):
            for value in (True, False, 0, 6, -1, 1.0, "1"):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    evidence.measure(repeats=value)

    def test_off_measurement_rejects_real_corpus_open_attempt(self):
        with self.assertRaisesRegex(ValueError, "extension-off"):
            evidence.sample(lambda: (evidence.DEFAULT_CORPUS / "sources.json").read_bytes(),
                            evidence.DEFAULT_CORPUS, forbid_corpus=True)
        self.assertFalse(tracemalloc.is_tracing())

    def test_measured_operation_cannot_write_any_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "unexpected.txt"
            with self.assertRaisesRegex(ValueError, "attempted a write"):
                evidence.sample(lambda: path.write_text("unexpected", encoding="utf-8"),
                                evidence.DEFAULT_CORPUS, forbid_corpus=False)
            self.assertFalse(path.exists())

    def test_caught_forbidden_read_cannot_be_reported_as_an_off_success(self):
        def swallowed_read():
            try:
                (evidence.DEFAULT_CORPUS / "sources.json").read_bytes()
            except ValueError:
                pass
            return {"status": "off", "execution_authorized": False}

        with self.assertRaisesRegex(ValueError, "extension-off"):
            evidence.sample(swallowed_read, evidence.DEFAULT_CORPUS,
                            forbid_corpus=True, expected_status="off")

    def test_caller_allocation_trace_is_preserved_instead_of_relabelled(self):
        tracemalloc.start()
        try:
            with self.assertRaisesRegex(ValueError, "existing allocation trace"):
                evidence.sample(lambda: {}, evidence.DEFAULT_CORPUS, forbid_corpus=True)
            self.assertTrue(tracemalloc.is_tracing())
        finally:
            tracemalloc.stop()

    def test_failed_or_authorizing_retrieval_cannot_produce_successful_cost_evidence(self):
        for value in ({"status": "unavailable", "execution_authorized": False},
                      {"status": "matches", "execution_authorized": True}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "failed or claimed"):
                evidence.sample(lambda: deepcopy(value), evidence.DEFAULT_CORPUS,
                                forbid_corpus=False, expected_status="matches")

    def test_same_size_raw_corpus_change_after_sample_invalidates_final_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            corpus = Path(temporary) / "corpus"
            shutil.copytree(evidence.DEFAULT_CORPUS, corpus)
            original = evidence.sample

            def changed_after_retrieval(*args, **kwargs):
                result = original(*args, **kwargs)
                if kwargs.get("expected_status") == "matches":
                    path = corpus / "index.json"
                    before = path.read_bytes()
                    self.assertTrue(before.endswith(b"\n"))
                    path.write_bytes(before[:-1] + b" ")
                return result

            with patch.object(evidence, "sample", changed_after_retrieval):
                with self.assertRaisesRegex(ValueError, "bytes changed"):
                    evidence.measure(repeats=1, corpus_root=corpus)

    def test_current_corpus_failure_is_not_replaced_by_old_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            corpus = Path(temporary) / "corpus"
            shutil.copytree(evidence.DEFAULT_CORPUS, corpus)
            path = corpus / "index.json"
            index = json.loads(path.read_text(encoding="utf-8"))
            index["corpus_sha256"] = "0" * 64
            path.write_text(json.dumps(index), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "failed or claimed"):
                evidence.measure(repeats=1, corpus_root=corpus)

    def test_nonstatic_route_resource_raw_change_is_also_checked_at_finalize(self):
        relative = "core/module_manifest.yaml"
        self.assertNotIn(relative, evidence.SOURCE_FILES)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / relative
            path.parent.mkdir()
            previous = b"version: 1\n"
            path.write_bytes(previous)
            with patch.object(evidence, "ROOT", root):
                evidence.assert_frozen_files(root / "unused-corpus", {relative: previous})
                path.write_bytes(b"version: 2\n")
                with self.assertRaisesRegex(ValueError, "bytes changed"):
                    evidence.assert_frozen_files(root / "unused-corpus", {relative: previous})


if __name__ == "__main__":
    unittest.main()
