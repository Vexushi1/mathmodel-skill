from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


def module_from_path():
    spec = importlib.util.spec_from_file_location(
        "literature_evidence_under_test", ROOT / "scripts/literature_evidence.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LiteratureEvidenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = module_from_path()

    def report(self):
        return {
            "protocol_version": "1.0.0",
            "scope": {
                "mode": "model_design",
                "question": "Q1",
                "problem_contract_status": "frozen",
                "independent_problem_structure": "题目存在守恒方程与可变边界，不先行选模型名。",
                "research_questions": ["可变边界扩散问题有何关键前提及适用条件？"],
            },
            "search": {
                "depth": "targeted", "status": "completed",
                "searched_at": "2026-11-14T08:00:00Z",
                "stop_reason": "核心机制的原文已定位",
                "attempts": [{
                    "provider": "test-academic-provider", "channel": "academic_connector",
                    "query": "moving boundary diffusion mechanism", "status": "success",
                }],
            },
            "sources": [{
                "id": "L1", "title": "Synthetic test article - not a real citation",
                "source_url": "https://example.org/test-only",
                "origin": "academic_connector", "access_level": "method",
                "evidence_level": "E2", "method_anchor": "Section 2 / Equation 3",
            }],
            "methods": [{
                "id": "M1", "source_id": "L1",
                "method_summary": "Conservation model with a declared moving boundary.",
                "transferability": "conditional", "disposition": "adapt_to_problem",
                "applicability_reason": "本题的外边界条件仍需单独核实和推导。",
            }],
            "decision": {
                "evidence_status": "partial",
                "independent_model_reasoning": "本题必须独立建立质量守恒和移动边界方程。",
                "unresolved_gaps": ["边界参数需要本题验证"],
            },
        }

    def test_valid_structure_does_not_grant_source_truth_or_approval(self):
        r = self.module.validate_report(self.report())
        self.assertEqual(r["status"], "passed", r["issues"])
        self.assertEqual(r["source_authenticity"], "not_assessed")
        self.assertEqual(r["search_execution"], "declared_not_independently_attested")
        self.assertEqual(r["human_model_approval"], "not_granted")
        self.assertEqual(r["numerical_acceptance"], "not_granted")

    def test_abstract_does_not_verify_adopted_equation(self):
        item = self.report()
        item["sources"][0].update(evidence_level="E1", access_level="abstract")
        item["sources"][0].pop("method_anchor")
        self.assertIn(
            "method:M1:original_method_not_verified",
            self.module.validate_report(item)["issues"],
        )

    def test_completed_search_requires_real_attempt_declaration(self):
        item = self.report()
        item["search"]["attempts"] = []
        self.assertIn(
            "declared_search_success_requires_real_channel_and_date",
            self.module.validate_report(item)["issues"],
        )
        item["search"]["attempts"] = [{
            "provider": "test-documents", "channel": "user_supplied",
            "query": "uploaded article", "status": "success",
        }]
        self.assertIn(
            "declared_search_success_requires_real_channel_and_date",
            self.module.validate_report(item)["issues"],
        )

    def test_unavailable_search_may_have_no_sources(self):
        item = self.report()
        item["search"].update(
            status="unavailable", attempts=[], stop_reason="当前网络服务不可用")
        item["sources"] = []
        item["methods"] = []
        item["decision"].update(
            evidence_status="insufficient", unresolved_gaps=["方法未核实"])
        self.assertEqual(self.module.validate_report(item)["status"], "passed")

    def test_duplicate_or_missing_source_is_rejected(self):
        item = self.report()
        item["sources"].append(dict(item["sources"][0]))
        self.assertIn("duplicate_source_id", self.module.validate_report(item)["issues"])
        item["sources"].pop()
        item["methods"][0]["source_id"] = "L9"
        self.assertIn("method:M1:missing_source", self.module.validate_report(item)["issues"])

    def test_unlocated_original_or_wrong_transfer_is_rejected(self):
        item = self.report()
        item["sources"][0].pop("method_anchor")
        self.assertIn(
            "source:L1:original_method_not_located",
            self.module.validate_report(item)["issues"],
        )
        item["sources"][0]["method_anchor"] = "Section 2 / Equation 3"
        item["methods"][0]["transferability"] = "inapplicable"
        self.assertIn(
            "method:M1:transferability_not_supported",
            self.module.validate_report(item)["issues"],
        )

    def test_standalone_research_is_not_model_design(self):
        item = self.report()
        item["scope"].update(
            mode="standalone", question="general",
            problem_contract_status="not_applicable",
        )
        self.assertIn(
            "method:M1:standalone_cannot_adopt",
            self.module.validate_report(item)["issues"],
        )

    def test_unexpected_approval_field_is_not_allowed(self):
        item = self.report()
        item["human_model_approval_status"] = "approved"
        self.assertEqual(self.module.validate_report(item)["status"], "failed")

    def test_duplicate_json_keys_and_oversize_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            path.write_text('{"status":"pending","status":"approved"}', encoding="utf-8")
            with self.assertRaisesRegex(self.module.EvidenceError, "duplicate_json_key"):
                self.module.read_report(path)
            path.write_text("x" * 262145, encoding="utf-8")
            with self.assertRaisesRegex(self.module.EvidenceError, "report_size_limit"):
                self.module.read_report(path)

    def test_router_makes_audit_explicit_and_read_only(self):
        router = yaml.safe_load(
            (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        route = router["routing"]["literature_evidence_audit"]
        self.assertEqual(route["pre_delivery_gates"], [])
        self.assertFalse(route["formal_delivery"])
        self.assertNotIn("model_approval", route.get("boundary_roles", []))
        self.assertEqual(
            router["runtime_segments"]["model_approval_pending"]["pause_state"],
            "awaiting_model_approval",
        )
        self.assertNotIn(
            "literature_evidence_audit",
            router["routing"]["full_workflow"].get("then", []),
        )


if __name__ == "__main__":
    unittest.main()
