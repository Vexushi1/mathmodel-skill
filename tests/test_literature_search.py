"""P3 offline tests: real metadata adapter interfaces are never treated as paper proof."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_search():
    spec = importlib.util.spec_from_file_location(
        "literature_search_under_test", ROOT / "scripts/literature_search.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LiteratureProviderAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = load_search()

    def brief(self):
        return {
            "protocol_version": "1.0.0",
            "scope": {
                "mode": "model_design",
                "question": "Q1", "problem_contract_status": "frozen",
                "problem_contract_anchor": "Problem Contract Q1 / frozen snapshot",
                "independent_problem_structure": "Conservation law with a shrinking cylindrical boundary.",
                "research_questions": ["Which original physical boundaries are verifiable?"],
            },
            "depth": "targeted", "year_from": 2022,
            "queries": ["cylindrical drying shrinking radius diffusion"],
        }

    def crossref(self):
        return {"message": {"items": [
            {
                "DOI": "10.1200/example.1",
                "title": ["A mathematical diffusion model for a shrinking cylinder"],
                "published": {"date-parts": [[2025, 6]]},
                "URL": "https://doi.org/10.1200/example.1",
                "container-title": ["Simulation Engineering"],
            },
            {
                "DOI": "10.1200/EXAMPLE.1",
                "title": ["Duplicate DOI publication variant"],
                "published": {"date-parts": [[2025]]},
            },
        ]}}

    def test_network_requires_explicit_opt_in(self):
        brief = self.brief()
        def forbidden(_url, **kwargs):
            self.fail("Network called without --allow-network")
        out = self.api.search(brief, provider="crossref",
                              allow_network=False, fetch=forbidden, clock=lambda: "2026-11-14T00:00:00Z")
        self.assertEqual(out["search"]["status"], "skipped")
        self.assertEqual(out["search"]["attempts"], [])
        self.assertEqual(out["sources"], [])
        self.assertEqual(out["methods"], [])
        self.assertEqual(out["decision"]["evidence_status"], "insufficient")

    def test_actual_provider_response_becomes_only_E0_not_original_paper_proof(self):
        urls = []
        def fetch(url, *, timeout):
            urls.append(url)
            return self.crossref()
        result = self.api.search(self.brief(), provider="crossref", allow_network=True,
                                 fetch=fetch, clock=lambda: "2026-11-14T00:00:00Z")
        self.assertEqual(result["search"]["status"], "completed")
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(result["sources"][0]["doi"], "10.1200/example.1")
        self.assertEqual(result["sources"][0]["publication_year"], 2025)
        self.assertEqual(result["sources"][0]["venue"], "Simulation Engineering")
        self.assertEqual(result["sources"][0]["evidence_level"], "E0")
        self.assertEqual(result["sources"][0]["access_level"], "metadata")
        self.assertEqual(result["methods"], [])
        self.assertEqual(result["search"]["attempts"][0]["result_count"], 2)
        self.assertIn("api.crossref.org/works?", urls[0])
        self.assertNotIn("Problem Contract Q1", urls[0])
        self.assertNotIn("Conservation law with a shrinking", urls[0])
        self.assertEqual(self.api.validate_report(result)["status"], "passed")

    def test_openalex_canonical_doi_and_retracted_exclusion(self):
        def fetch(url, *, timeout):
            self.assertIn("api.openalex.org/works?", url)
            self.assertIn("from_publication_date", url)
            return {"results": [
                {
                    "id": "https://openalex.org/W1234",
                    "title": "An open metadata article",
                    "doi": "https://doi.org/10.3023/test",
                    "publication_year": 2024,
                    "primary_location": {"source": {"display_name": "Synthetic Review"}},
                    "is_retracted": False,
                },
                {
                    "id": "https://openalex.org/W99",
                    "title": "A retracted source", "is_retracted": True,
                },
            ]}
        out = self.api.search(self.brief(), provider="openalex", allow_network=True,
                              fetch=fetch, clock=lambda: "2026-11-14T00:00:00Z")
        self.assertEqual(out["search"]["status"], "completed")
        self.assertEqual(len(out["sources"]), 1)
        self.assertEqual(out["sources"][0]["doi"], "10.3023/test")
        self.assertTrue(any("retracted" in gap for gap in out["decision"]["unresolved_gaps"]))
        self.assertEqual(self.api.validate_report(out)["status"], "passed")

    def test_empty_valid_results_not_confused_with_provider_unavailable(self):
        out = self.api.search(self.brief(), provider="crossref", allow_network=True,
                              fetch=lambda url, timeout: {"message": {"items": []}},
                              clock=lambda: "2026-11-14T00:00:00Z")
        self.assertEqual(out["search"]["status"], "no_suitable_source")
        self.assertEqual(len(out["search"]["attempts"]), 1)
        self.assertEqual(self.api.validate_report(out)["status"], "passed")

    def test_failures_do_not_claim_completed_search(self):
        def offline(url, *, timeout):
            raise self.api.SearchError("provider_unavailable")
        out = self.api.search(self.brief(), provider="crossref", allow_network=True,
                              fetch=offline, clock=lambda: "2026-11-14T00:00:00Z")
        self.assertEqual(out["search"]["status"], "unavailable")
        self.assertEqual(out["sources"], [])
        self.assertEqual(out["search"]["attempts"][0]["status"], "unavailable")
        self.assertEqual(self.api.validate_report(out)["status"], "passed")

    def test_invalid_provider_payload_is_reported_not_approved(self):
        out = self.api.search(self.brief(), provider="crossref", allow_network=True,
                              fetch=lambda url, timeout: {"message": "wrong"},
                              clock=lambda: "2026-11-14T00:00:00Z")
        self.assertEqual(out["search"]["status"], "failed")
        self.assertEqual(out["decision"]["evidence_status"], "insufficient")
        self.assertEqual(out["methods"], [])

    def test_brief_parser_rejects_nonfrozen_and_private_query_dump(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "brief.json"
            brief = self.brief()
            p.write_text(json.dumps(brief), encoding="utf-8")
            self.assertEqual(self.api.load_brief(p), brief)
            brief["scope"]["problem_contract_status"] = "not_applicable"
            p.write_text(json.dumps(brief), encoding="utf-8")
            with self.assertRaisesRegex(self.api.SearchError, "frozen"):
                self.api.load_brief(p)
            brief = self.brief()
            brief["queries"] = ["private " * 50]
            p.write_text(json.dumps(brief), encoding="utf-8")
            with self.assertRaisesRegex(self.api.SearchError, "queries_invalid"):
                self.api.load_brief(p)
            p.write_text('{"x":1,"x":2}', encoding="utf-8")
            with self.assertRaisesRegex(self.api.SearchError, "duplicate_brief_key"):
                self.api.load_brief(p)

    def test_url_guard_and_syntax(self):
        url = self.api.make_url("crossref", "diffusion kinetics", year_from=2022, per_query=5)
        self.assertTrue(url.startswith("https://api.crossref.org/works?"))
        self.assertIn("from-pub-date%3A2022", url)
        with self.assertRaisesRegex(self.api.SearchError, "provider_or_result_limit"):
            self.api.make_url("other", "x", year_from=2022, per_query=5)
        with self.assertRaisesRegex(self.api.SearchError, "provider_host_disallowed"):
            self.api.fetch_json("https://example.org/stolen?query=private", timeout=5)

    def test_file_is_never_overwritten_and_no_state_is_written(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            out = root / "report.json"
            report = self.api.search(self.brief(), provider="crossref", allow_network=False)
            self.api.write_new(out, report)
            before = out.read_bytes()
            self.assertEqual(json.loads(before)["search"]["status"], "skipped")
            with self.assertRaisesRegex(self.api.SearchError, "refuse_overwrite"):
                self.api.write_new(out, {"invalid": True})
            self.assertEqual(out.read_bytes(), before)
            self.assertFalse((root / "state/project_state.yaml").exists())
            self.assertFalse((root / "模型论文框架.md").exists())


if __name__ == "__main__":
    unittest.main()
