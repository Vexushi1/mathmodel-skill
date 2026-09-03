from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
FAMILIES = (
    "edition_compliance",
    "anonymity_and_metadata",
    "ai_disclosure",
    "citation_entity_integrity",
    "rendered_page_surface",
    "figure_table_information_value",
    "reproducibility_and_package",
    "cross_question_dynamic_coverage",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestV820FinalReviewCompliance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scorer = load_module("score_submission_v820", ROOT / "scripts/score_submission.py")
        cls.config = json.loads((ROOT / "config/review_weights.json").read_text(encoding="utf-8"))

    def valid_report(self) -> dict:
        return {
            "review_schema_version": "1.0.0",
            "review_context": {
                "skill_version": "8.2.0",
                "competition_profile": "demo",
                "edition": "2026",
                "rule_verification_status": "verified",
                "rule_verified_at": "2026-09-01",
                "rule_source": "https://example.invalid/official-rules",
                "delivery_mode": "reproducibility",
                "source_bundle_sha256": "a" * 64,
                "compiled_pdf_sha256": "b" * 64,
            },
            "coverage": [
                {
                    "check_family": family,
                    "applicability": "applicable",
                    "verification_mode": "hybrid",
                    "status": "passed",
                    "rule_source": "modules/06_review_delivery.md",
                    "evidence": f"review evidence for {family}",
                }
                for family in FAMILIES
            ],
            "findings": [],
            "scores": {name: 80 for name in self.config["dimensions"]},
            "hard_fail": [],
            "evidence": {name: f"evidence:{name}" for name in self.config["dimensions"]},
        }

    def finding(self, **overrides) -> dict:
        finding = {
            "check_id": "FR-001",
            "check_family": "rendered_page_surface",
            "dimension": "writing_and_layout",
            "severity": "review_required",
            "status": "open",
            "hard_fail_code": None,
            "rule_source": "modules/06_review_delivery.md#Final-Submission-Compliance-Evidence-Sweep",
            "verification_mode": "manual",
            "location": "final_latex/main.pdf#page=3",
            "evidence": "A table is clipped at the right edge.",
            "action": "Resize the table and recompile the current PDF.",
        }
        finding.update(overrides)
        return finding

    @staticmethod
    def set_coverage_status(report: dict, family: str, status: str) -> None:
        for entry in report["coverage"]:
            if entry["check_family"] == family:
                entry["status"] = status
                return
        raise AssertionError(f"missing coverage family: {family}")

    def test_matrix_template_is_dynamic_and_complete(self):
        path = ROOT / "templates/review/final_review_matrix.yaml"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        payload = yaml.safe_load(text) or {}
        self.assertEqual(payload["review_schema_version"], "1.0.0")
        self.assertEqual(tuple(item["check_family"] for item in payload["coverage"]), FAMILIES)
        for forbidden in ("287", "扣 1", "扣 2", "问题五", "5 问"):
            self.assertNotIn(forbidden, text)

    def test_legacy_report_output_remains_v811_compatible(self):
        report = {
            "scores": {name: 80 for name in self.config["dimensions"]},
            "hard_fail": [],
            "evidence": {"legacy": "retained"},
        }
        result = self.scorer.score_submission(self.config, report)
        self.assertEqual(result["total"], 80.0)
        self.assertEqual(result["evidence"], {"legacy": "retained"})
        self.assertNotIn("review_status", result)
        self.assertNotIn("coverage", result)
        self.assertNotIn("findings", result)

    def test_valid_matrix_is_normalized_without_changing_scores(self):
        result = self.scorer.score_submission(self.config, self.valid_report())
        self.assertEqual(result["total"], 80.0)
        self.assertEqual(result["review_schema_version"], "1.0.0")
        self.assertEqual(result["review_status"], "passed")
        self.assertEqual(len(result["coverage"]), 8)
        self.assertEqual(result["findings"], [])

    def test_open_review_required_is_visible_but_not_a_hard_fail(self):
        report = self.valid_report()
        report["findings"] = [self.finding()]
        self.set_coverage_status(report, "rendered_page_surface", "findings_present")
        result = self.scorer.score_submission(self.config, report)
        self.assertEqual(result["status"], "scored")
        self.assertEqual(result["review_status"], "review_required")
        self.assertEqual(result["hard_fail"], [])

    def test_open_blocking_finding_forces_rejection(self):
        report = self.valid_report()
        report["review_context"].update(
            rule_verification_status="verified",
            rule_verified_at="2026-09-01",
            rule_source="https://example.invalid/official-rules",
            delivery_mode="official",
        )
        report["findings"] = [
            self.finding(
                check_family="edition_compliance",
                dimension="reproduction_and_delivery",
                severity="blocking",
                hard_fail_code="verified_official_rule_violation",
                rule_source="config/competition_profiles.yaml#profiles.demo.edition_rules",
            )
        ]
        self.set_coverage_status(report, "edition_compliance", "findings_present")
        result = self.scorer.score_submission(self.config, report)
        self.assertEqual(result["status"], "reject_or_major_rework")
        self.assertEqual(result["review_status"], "blocking")
        self.assertEqual(result["hard_fail"], ["verified_official_rule_violation"])

    def test_finding_count_never_changes_explicit_scores(self):
        base = self.valid_report()
        base_total = self.scorer.score_submission(self.config, base)["total"]
        base["findings"] = [
            self.finding(check_id=f"FR-{index:03d}", status="resolved")
            for index in range(1, 8)
        ]
        self.assertEqual(self.scorer.score_submission(self.config, base)["total"], base_total)

    def test_duplicate_check_id_is_rejected(self):
        report = self.valid_report()
        report["findings"] = [self.finding(), self.finding()]
        self.set_coverage_status(report, "rendered_page_surface", "findings_present")
        with self.assertRaisesRegex(ValueError, "duplicate check_id"):
            self.scorer.score_submission(self.config, report)

    def test_unknown_finding_enums_are_rejected(self):
        cases = {
            "check_family": "unknown_family",
            "dimension": "unknown_dimension",
            "severity": "fatal",
            "status": "ignored",
            "verification_mode": "guessed",
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                report = self.valid_report()
                report["findings"] = [self.finding(**{field: value})]
                with self.assertRaisesRegex(ValueError, field):
                    self.scorer.score_submission(self.config, report)

    def test_unknown_coverage_enums_are_rejected(self):
        cases = {
            "check_family": "unknown_family",
            "applicability": "sometimes",
            "verification_mode": "guessed",
            "status": "skipped",
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                report = self.valid_report()
                report["coverage"][0][field] = value
                with self.assertRaisesRegex(ValueError, field):
                    self.scorer.score_submission(self.config, report)

    def test_unknown_review_schema_version_is_rejected(self):
        report = self.valid_report()
        report["review_schema_version"] = "2.0.0"
        with self.assertRaisesRegex(ValueError, "review_schema_version"):
            self.scorer.score_submission(self.config, report)

    def test_invalid_attestation_hash_is_rejected(self):
        report = self.valid_report()
        report["review_context"]["compiled_pdf_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(ValueError, "compiled_pdf_sha256"):
            self.scorer.score_submission(self.config, report)

    def test_open_finding_requires_location_evidence_and_action(self):
        for field in ("location", "evidence", "action"):
            with self.subTest(field=field):
                report = self.valid_report()
                report["findings"] = [self.finding(**{field: None})]
                with self.assertRaisesRegex(ValueError, field):
                    self.scorer.score_submission(self.config, report)

    def test_open_blocking_requires_known_hard_fail_code(self):
        for code, message in ((None, "hard_fail_code"), ("invented", "unknown hard-fail")):
            with self.subTest(code=code):
                report = self.valid_report()
                report["findings"] = [self.finding(severity="blocking", hard_fail_code=code)]
                with self.assertRaisesRegex(ValueError, message):
                    self.scorer.score_submission(self.config, report)

    def test_official_rule_hard_fail_requires_verified_source_context(self):
        report = self.valid_report()
        report["review_context"].update(
            rule_verification_status="unverified",
            rule_verified_at=None,
            rule_source=None,
        )
        report["findings"] = [
            self.finding(
                severity="blocking",
                hard_fail_code="verified_official_rule_violation",
                check_family="edition_compliance",
            )
        ]
        self.set_coverage_status(report, "edition_compliance", "findings_present")
        with self.assertRaisesRegex(ValueError, "verified official rule context"):
            self.scorer.score_submission(self.config, report)

    def test_verified_official_rule_cannot_be_accepted_as_exception(self):
        report = self.valid_report()
        report["review_context"].update(
            rule_verification_status="verified",
            rule_verified_at="2026-09-01",
            rule_source="https://example.invalid/official-rules",
        )
        report["findings"] = [
            self.finding(
                status="accepted_exception",
                severity="blocking",
                hard_fail_code="verified_official_rule_violation",
                check_family="edition_compliance",
            )
        ]
        with self.assertRaisesRegex(ValueError, "accepted_exception"):
            self.scorer.score_submission(self.config, report)

    def test_coverage_requires_all_unique_families(self):
        report = self.valid_report()
        report["coverage"].pop()
        with self.assertRaisesRegex(ValueError, "coverage families"):
            self.scorer.score_submission(self.config, report)
        report = self.valid_report()
        report["coverage"][1]["check_family"] = report["coverage"][0]["check_family"]
        with self.assertRaisesRegex(ValueError, "duplicate coverage"):
            self.scorer.score_submission(self.config, report)

    def test_unverifiable_and_not_applicable_coverage_require_evidence(self):
        for status in ("unverifiable", "not_applicable"):
            with self.subTest(status=status):
                report = self.valid_report()
                entry = report["coverage"][0]
                entry["status"] = status
                entry["applicability"] = "not_applicable" if status == "not_applicable" else "applicable"
                entry["evidence"] = None
                with self.assertRaisesRegex(ValueError, "evidence"):
                    self.scorer.score_submission(self.config, report)

    def test_unverified_edition_rules_cannot_be_marked_passed(self):
        report = self.valid_report()
        report["review_context"].update(
            rule_verification_status="unverified",
            rule_verified_at=None,
            rule_source=None,
        )
        with self.assertRaisesRegex(ValueError, "edition rules cannot be marked passed"):
            self.scorer.score_submission(self.config, report)
        self.set_coverage_status(report, "edition_compliance", "unverifiable")
        result = self.scorer.score_submission(self.config, report)
        self.assertEqual(result["review_status"], "review_required")

    def test_final_matrix_requires_current_source_and_pdf_hashes(self):
        for field in ("source_bundle_sha256", "compiled_pdf_sha256"):
            with self.subTest(field=field):
                report = self.valid_report()
                report["review_context"][field] = None
                with self.assertRaisesRegex(ValueError, field):
                    self.scorer.score_submission(self.config, report)

    def test_coverage_requires_rule_source(self):
        report = self.valid_report()
        report["coverage"][0]["rule_source"] = None
        with self.assertRaisesRegex(ValueError, "rule_source"):
            self.scorer.score_submission(self.config, report)

    def test_hard_fail_code_is_reserved_for_blocking_findings(self):
        report = self.valid_report()
        report["findings"] = [self.finding(hard_fail_code="latex_compile_failure")]
        with self.assertRaisesRegex(ValueError, "only valid for blocking"):
            self.scorer.score_submission(self.config, report)

    def test_declared_matrix_hard_fail_requires_atomic_open_finding(self):
        report = self.valid_report()
        report["hard_fail"] = ["latex_compile_failure"]
        with self.assertRaisesRegex(ValueError, "matching open blocking"):
            self.scorer.score_submission(self.config, report)

    def test_hard_fail_codes_must_be_strings(self):
        report = self.valid_report()
        report["hard_fail"] = [None]
        with self.assertRaisesRegex(ValueError, "non-empty string codes"):
            self.scorer.score_submission(self.config, report)

    def test_findings_present_coverage_requires_a_matching_finding(self):
        report = self.valid_report()
        self.set_coverage_status(report, "rendered_page_surface", "findings_present")
        with self.assertRaisesRegex(ValueError, "without findings"):
            self.scorer.score_submission(self.config, report)

    def test_coverage_applicability_and_status_must_agree(self):
        report = self.valid_report()
        report["coverage"][0]["applicability"] = "not_applicable"
        with self.assertRaisesRegex(ValueError, "not_applicable"):
            self.scorer.score_submission(self.config, report)

    def test_new_matrix_requires_dimension_evidence(self):
        report = self.valid_report()
        report["evidence"].pop("mathematical_closure")
        with self.assertRaisesRegex(ValueError, "missing dimension evidence"):
            self.scorer.score_submission(self.config, report)

    def test_official_allowlists_do_not_include_internal_review_matrix(self):
        profiles = yaml.safe_load((ROOT / "config/competition_profiles.yaml").read_text(encoding="utf-8")) or {}
        for name, profile in (profiles.get("profiles") or {}).items():
            files = ((profile.get("edition_rules") or {}).get("submission_files") or [])
            joined = "\n".join(str(item).lower() for item in files)
            self.assertNotIn("final_review_matrix", joined, name)
            self.assertNotIn("review_report", joined, name)

    def test_review_only_files_are_outside_semantic_authorities(self):
        for relative in (
            "core/model_approval_contract.yaml",
            "core/project_state.schema.yaml",
            "core/writing_reasoning_contract.yaml",
            "modules/05_writing/paper_writing_protocol.md",
            "modules/05_writing/ai_cleanup.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("final_review_matrix", text, relative)
            self.assertNotIn("verified_official_rule_violation", text, relative)


if __name__ == "__main__":
    unittest.main()
