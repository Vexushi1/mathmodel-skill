"""Exact, source-hash-bound G1A span-shift tests; historical approval fixture remains immutable."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_measurement():
    spec = importlib.util.spec_from_file_location(
        "v10280_measurement", ROOT / "tests/v10270_runtime_measurement.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V10280ApprovedSourceSpanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measurement = load_measurement()
        cls.fixture = ROOT / "tests/fixtures/v10290_approved_source_spans.json"
        cls.frozen_v10280 = ROOT / "tests/fixtures/v10280_approved_source_spans.json"

    def test_frozen_v10280_approval_is_preserved_not_rewritten(self):
        legacy = json.loads(self.frozen_v10280.read_text(encoding="utf-8"))
        self.assertEqual(legacy["scope"], "v10.28.0_p1_source_only_read_ranges")
        self.assertEqual(legacy["version"], "10.28.0")
        self.assertEqual(legacy["migrations"][0]["candidate_sha256"],
                         "47177e0208cb4a4993efdb189126e76ff2503cb079b7bf9fcfd6237f16c76cc1")
        self.assertEqual(legacy["migrations"][0]["old_ranges"], [[416, 416], [419, 430]])
        self.assertEqual(legacy["migrations"][0]["new_ranges"], [[424, 424], [427, 438]])
        with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
            self.measurement.approved_source_span_migrations(self.frozen_v10280)

    def cases(self):
        manifest = self.measurement.approved_source_span_migrations(self.fixture)
        before = {"id": "pure_model_design", "behavior": {"read_now": []},
                  "source_identity": {"skill_version": "10.27.0", "sources": []}}
        after = {"id": "pure_model_design", "behavior": {"read_now": []},
                 "source_identity": {"skill_version": "10.28.0", "sources": []}}
        for item in manifest["migrations"]:
            original = {
                "origin": "skill", "path": item["path"],
                "ranges": deepcopy(item["old_ranges"]),
                "selectors": {}, "when": None, "resolution": "exact",
            }
            current = deepcopy(original)
            current["ranges"] = deepcopy(item["new_ranges"])
            before["behavior"]["read_now"].append(original)
            after["behavior"]["read_now"].append(current)
            before["source_identity"]["sources"].append({
                "path": item["path"], "sha256": item["baseline_sha256"]})
            after["source_identity"]["sources"].append({
                "path": item["path"], "sha256": item["candidate_sha256"]})
        return manifest, before, after

    def test_exact_current_bytes_and_spans_project_without_mutating_actual_evidence(self):
        fixture, old, new = self.cases()
        preserved = deepcopy(new)
        projected, evidence = self.measurement.project_exact_approved_source_spans(
            old, new, fixture)
        self.assertEqual(projected["read_now"], old["behavior"]["read_now"])
        self.assertEqual(new, preserved)
        self.assertEqual(len(evidence), 1)
        self.assertTrue(all(entry["source_sha256"] for entry in evidence))

    def test_reject_changed_ranges_even_if_source_sha_matches(self):
        fixture, old, new = self.cases()
        new["behavior"]["read_now"][0]["ranges"] = [[1, 999]]
        with self.assertRaisesRegex(ValueError, "physical span drift"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)

    def test_reject_changed_selector_or_unauthorized_source_provenance(self):
        fixture, old, new = self.cases()
        new["behavior"]["read_now"][0]["selectors"] = {"yaml_paths": ["wrong"]}
        with self.assertRaisesRegex(ValueError, "reading semantics"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)
        _, old, new = self.cases()
        new["source_identity"]["sources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source identity drift"):
            self.measurement.project_exact_approved_source_spans(old, new, fixture)

    def test_manifest_fails_if_candidate_source_bytes_or_paths_change(self):
        data = json.loads(self.fixture.read_text(encoding="utf-8"))
        data["migrations"][0]["candidate_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "span.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "candidate bytes changed"):
                self.measurement.approved_source_span_migrations(p)
        data["migrations"][0]["path"] = "core/unrelated.yaml"
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "span.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "current router authority"):
                self.measurement.approved_source_span_migrations(p)


if __name__ == "__main__":
    unittest.main()
