"""P6: source-bound paired evaluation; all local test designs are synthetic controls."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location(
        "literature_p6_benchmark_under_test", ROOT / "scripts/literature_p6_benchmark.py")
    assert spec and spec.loader
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class LiteratureP6BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = module()
        cls.catalog = cls.api.load_json(cls.api.DEFAULT_CATALOG, cls.api.MAX_CATALOG_BYTES)

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def _file(self, name: str, content: bytes) -> dict:
        path = self.root / name
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_bytes(content)
        return {"path": name, "sha256": hashlib.sha256(content).hexdigest()}

    def _review(self, rid, base=2, lit=3):
        score = lambda v: {k: v for k in self.api.AXES}
        return {
            "reviewer_id": rid, "scored_before_unblinding": True,
            "scores": {"X": score(base), "Y": score(lit)},
            "blocking_issues": {"X": 2, "Y": 1},
            "unsupported_assumptions": {"X": 2, "Y": 0},
            "review_evidence": {
                "X": "Synthetic control reviewer notes, not a real historical judgment.",
                "Y": "Synthetic enhanced reviewer notes, not a real historical judgment.",
            }
        }

    def _case(self, meta):
        code = meta["id"]
        task = self._file(code + ".pdf", b"%PDF-1.5\nsynthetic test data\n")
        attachments = []
        for kind in meta["required_attachment_kinds"]:
            attachments.append({"kind": kind, **self._file(code + "-" + kind + ".csv",
                                                          b"synthetic,control\n1,2\n")})
        prompt_sha = hashlib.sha256(b"synthetic-equal-prompt-template").hexdigest()
        arm = lambda name, calls: {
            "model_runtime": "same-test-model", "prompt_sha256": prompt_sha,
            "design_path": name + ".md", "design_sha256": self._file(
                name + ".md", b"synthetic model content only; not evaluated against real contest.")["sha256"],
            "elapsed_minutes": 45, "research_read_minutes": 10 if calls else 0,
            "external_queries": calls, "design_tokens": 1000,
        }
        return {
            "case_id": code, "official_page_url": meta["official_page_url"],
            "task": task, "attachments": attachments,
            "budget_minutes": 60,
            "controls": {
                "same_question_and_attachments": True,
                "same_resource_budget": True,
                "separate_run_contexts": True,
                "reviewers_blinded_before_scoring": True,
            },
            "arms": {"X": arm(code + "-baseline", 0), "Y": arm(code + "-candidate", 3)},
            "unblinding": {"X": "baseline", "Y": "literature_enhanced"},
            "reviews": [self._review("R1"), self._review("R2")],
        }

    def _study(self):
        return {
            "protocol_version": "1.0.0", "study_id": "synthetic-protocol-check",
            "catalog_version": "1.0.0", "protocol_pre_registered": True,
            "cases": [self._case(meta) for meta in self.catalog["cases"]],
        }

    def test_catalog_is_real_official_link_catalog_only_not_study_result(self):
        items = self.api.catalog_cases(self.catalog)
        self.assertEqual(tuple(items), self.api.EXPECTED_CASES)
        self.assertFalse(self.catalog["authoritative_problem_text_embedded"])
        self.assertTrue(all(v["official_problem_pdf_url"].startswith("https://www.comap.org/")
                            for v in items.values()))

    def test_empty_or_partial_study_cannot_claim_improvement(self):
        study = {
            "protocol_version": "1.0.0", "study_id": "incomplete-p6",
            "catalog_version": "1.0.0", "protocol_pre_registered": True,
            "cases": [],
        }
        r = self.api.evaluate(study, self.catalog, self.root)
        self.assertEqual(r["status"], "not_ready")
        self.assertEqual(len(r["missing_case_ids"]), 3)
        self.assertEqual(r["measured_quality_improvement"], "not_assessed")
        study["cases"] = [self._case(self.catalog["cases"][0])]
        r = self.api.evaluate(study, self.catalog, self.root)
        self.assertEqual(len(r["missing_case_ids"]), 2)

    def test_complete_synthetic_case_set_returns_descriptive_only_not_gate(self):
        result = self.api.evaluate(self._study(), self.catalog, self.root)
        self.assertEqual(result["status"], "descriptive_only")
        self.assertEqual(result["case_count"], 3)
        self.assertEqual(result["criteria_delta_mean"]["requirements_coverage"], 1)
        self.assertEqual(result["case_deltas"][0]["external_query_delta"], 3)
        self.assertEqual(result["causal_inference"], "not_established")
        self.assertEqual(result["statistical_significance"], "not_assessed")
        self.assertTrue(result["no_automatic_winner_or_release_gate"])
        self.assertEqual(result["model_approval"], "not_granted")

    def test_source_hash_and_required_attachments_fail_closed(self):
        study = self._study()
        study["cases"][0]["task"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(self.api.BenchmarkError, "source_sha256_mismatch"):
            self.api.evaluate(study, self.catalog, self.root)
        study = self._study()
        study["cases"][1]["attachments"].pop()
        with self.assertRaisesRegex(self.api.BenchmarkError, "required_attachments_incomplete"):
            self.api.evaluate(study, self.catalog, self.root)

    def test_model_runtime_prompt_and_baseline_search_comparability(self):
        for key, value, msg in (
            ("model_runtime", "different-test-model", "different_model_runtime"),
            ("prompt_sha256", "f" * 64, "unequal_prompt_template"),
            ("external_queries", 4, "baseline_search_not_disabled"),
        ):
            study = self._study()
            study["cases"][0]["arms"]["X"][key] = value
            with self.subTest(field=key), self.assertRaisesRegex(self.api.BenchmarkError, msg):
                self.api.evaluate(study, self.catalog, self.root)

    def test_blinding_reviewers_and_budgets_must_be_complete(self):
        for mutation, failure in (
            ("blind_flag", "paired_conditions_not_declared"),
            ("duplicate_reviewer", "duplicate_reviewer"),
            ("premature_unblind", "review_must_precede_unblinding"),
            ("overbudget", "elapsed_minutes_invalid"),
            ("unequal_budget", "reading_time_exceeds_elapsed"),
        ):
            s = self._study()
            case = s["cases"][0]
            if mutation == "blind_flag":
                case["controls"]["reviewers_blinded_before_scoring"] = False
            elif mutation == "duplicate_reviewer":
                case["reviews"][1]["reviewer_id"] = "R1"
            elif mutation == "premature_unblind":
                case["reviews"][0]["scored_before_unblinding"] = False
            elif mutation == "overbudget":
                case["arms"]["Y"]["elapsed_minutes"] = 62
            else:
                case["arms"]["Y"]["research_read_minutes"] = 50
                case["arms"]["Y"]["elapsed_minutes"] = 45
            with self.subTest(mutation=mutation), self.assertRaisesRegex(
                self.api.BenchmarkError, failure
            ):
                self.api.evaluate(s, self.catalog, self.root)

    def test_traversal_and_symlink_are_rejected(self):
        sha = "a" * 64
        for relative in ("../outside.pdf", "C:\\private.pdf", "/etc/passwd"):
            with self.subTest(relative=relative), self.assertRaisesRegex(
                self.api.BenchmarkError, "unsafe_relative_path"
            ):
                self.api.guarded_file(self.root, relative, sha)
        target = self._file("real.pdf", b"%PDF-1.5\nfake")
        alias = self.root / "link.pdf"
        try:
            alias.symlink_to(self.root / "real.pdf")
        except (NotImplementedError, OSError):
            self.skipTest("symlink unsupported")
        with self.assertRaisesRegex(self.api.BenchmarkError, "symlink_source_forbidden"):
            self.api.guarded_file(self.root, alias.name, target["sha256"])

    def test_duplicate_json_keys_and_nonfinite_values_rejected(self):
        p = self.root / "bad.json"
        p.write_text('{"study_id":"A","study_id":"B"}', encoding="utf-8")
        with self.assertRaisesRegex(self.api.BenchmarkError, "duplicate_json_key"):
            self.api.load_json(p, 262144)
        p.write_text('{"x":NaN}', encoding="utf-8")
        with self.assertRaisesRegex(self.api.BenchmarkError, "nonfinite_json_number"):
            self.api.load_json(p, 262144)

    def test_untrusted_source_and_review_forgery_do_not_authorize(self):
        s = self._study()
        s["cases"][0]["official_page_url"] = "https://evil.example/task"
        with self.assertRaisesRegex(self.api.BenchmarkError, "official_source_identity_drift"):
            self.api.evaluate(s, self.catalog, self.root)
        s = self._study()
        s["cases"][0]["reviews"][0]["scores"]["X"]["source_verifiability"] = 5
        with self.assertRaisesRegex(self.api.BenchmarkError, "score_invalid"):
            self.api.evaluate(s, self.catalog, self.root)

    def test_malformed_catalog_case_id_or_unblinding_fails_without_traceback(self):
        bad_catalog = deepcopy(self.catalog)
        bad_catalog["cases"][0]["official_page_url"] = None
        with self.assertRaisesRegex(self.api.BenchmarkError, "catalog_case_source_invalid"):
            self.api.catalog_cases(bad_catalog)
        study = self._study()
        study["cases"][0]["case_id"] = []
        with self.assertRaisesRegex(self.api.BenchmarkError, "study_case_unknown_or_duplicate"):
            self.api.evaluate(study, self.catalog, self.root)
        study = self._study()
        study["cases"][0]["unblinding"]["X"] = []
        with self.assertRaisesRegex(self.api.BenchmarkError, "arm_mapping_invalid"):
            self.api.evaluate(study, self.catalog, self.root)

    def test_no_project_state_or_research_report_writes(self):
        study = self._study()
        before = {p.relative_to(self.root).as_posix(): p.read_bytes()
                  for p in self.root.rglob("*") if p.is_file()}
        self.api.evaluate(study, self.catalog, self.root)
        self.assertFalse((self.root / "state/project_state.yaml").exists())
        self.assertFalse((self.root / "模型论文框架.md").exists())
        self.assertFalse((self.root / "research_evidence").exists())
        # The tool never creates a report or manipulates these existing sources.
        for name, data in before.items():
            self.assertEqual((self.root / name).read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
