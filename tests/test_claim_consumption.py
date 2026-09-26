"""B2 observe-only integration against a real, synthetic A2/B1 receipt chain."""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import claim_consumption as audit
from tests import conformance_a2_smoke as smoke
from tests.claim_fixture import install_record
from tests.test_model_code_conformance import bytes_in, save
from validate_model_paper_framework import sha256_text


class ClaimConsumptionIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed_tmp = tempfile.TemporaryDirectory()
        cls.seed = Path(cls.seed_tmp.name) / "seed"
        cls.seed.mkdir()
        state = smoke.prepare(cls.seed, "python", required=("primary", "analysis"))
        # Synthetic equation: (6 + 194) / 2 = 100. Both native stages and
        # acceptance receipts are produced from this changed input identity.
        (cls.seed / "constraints.json").write_text('{"right_hand_side_offset":194}', encoding="utf-8")
        state, _ = smoke.run_stage(cls.seed, "python", "primary", state)
        state, _ = smoke.run_stage(cls.seed, "python", "analysis", state)
        cls.base_state = state

    @classmethod
    def tearDownClass(cls):
        cls.seed_tmp.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "project"
        shutil.copytree(self.seed, self.root)
        self.state = deepcopy(self.base_state)
        install_record(self.state)
        claim = self.state["paper_framework"]["claim_evidence"]["claims"][0]
        claim["text"] = "Synthetic scalar equation result is 100."
        claim["numeric_profile_id"] = "N99"
        claim["assertion"].update(value="100.0", display_location="abstract")
        self.state["paper_framework"]["numeric_profile"][0].update(
            abstract_decimals=1, body_decimals=2,
        )
        self.state["paper_framework"]["claim_consumption_policy"] = {
            "protocol_version": "1.0.0", "mode": "observe",
            "required_consumptions": [{"claim_id": "answer_claim",
                                       "fragment_kinds": ["abstract_claim", "question_result_text"]}],
        }
        self.fragments = [
            {"id": "paper.abstract.q1", "kind": "abstract_claim", "scope": "Q1",
             "depends_on": ["claim:answer_claim"], "anchor": "Answer:",
             "source_file": "final_latex/abstract.tex", "status": "current"},
            {"id": "paper.result.q1", "kind": "question_result_text", "scope": "Q1",
             "depends_on": ["claim:answer_claim"], "anchor": "Result:",
             "source_file": "final_latex/result.tex", "status": "current"},
        ]
        self.state["paper_framework"]["paper_fragments"] = self.fragments
        latex = self.root / "final_latex"
        latex.mkdir(exist_ok=True)
        (latex / "main.tex").write_text(
            "\\documentclass{article}\n\\begin{document}\n"
            "\\input{abstract}\n\\input{result}\n\\end{document}\n", encoding="utf-8",
        )
        (latex / "abstract.tex").write_text("Answer: 100.0.\n", encoding="utf-8")
        (latex / "result.tex").write_text("Result: 100.00.\n", encoding="utf-8")
        self._save_with_projection()

    def tearDown(self):
        self.tmp.cleanup()

    def _save_with_projection(self):
        framework = self.root / "模型论文框架.md"
        text = framework.read_text(encoding="utf-8")
        text = text.split("### Paper Fragment Dependency Map", 1)[0]
        lines = [
            "### Paper Fragment Dependency Map", "",
            "| Fragment ID | 类型 | 范围 | 依赖对象 | 正文/摘要锚点 | LaTeX 源码文件（可选） | 状态 |",
            "|---|---|---|---|---|---|---|",
        ]
        for row in self.fragments:
            values = [row[key] for key in ("id", "kind", "scope")]
            values += [", ".join(row["depends_on"]), row["anchor"],
                       f"`{row['source_file']}`", row["status"]]
            lines.append("| " + " | ".join(values) + " |")
        text += "\n".join(lines) + "\n"
        framework.write_text(text, encoding="utf-8")
        self.state["paper_framework"]["sha256"] = sha256_text(text)
        save(self.root, self.state)

    def test_b01_live_original_100_matches_two_location_profiles_and_is_readonly(self):
        before = bytes_in(self.root)
        report = audit.inspect_project(self.root)
        self.assertEqual(report["status"], "observed", report)
        self.assertEqual((report["policy_protocol_version"], report["mode"]),
                         ("1.0.0", "observe"))
        self.assertEqual(report["b1_status"], "evidence_checked", report)
        self.assertEqual({item["status"] for item in report["numeric_checks"]}, {"matched"})
        self.assertEqual({item["expected_value"] for item in report["numeric_checks"]},
                         {"100.0", "100.00"})
        self.assertEqual({item["fragment_kind"] for item in report["required_coverage"]
                          if item["status"] == "located"},
                         {"abstract_claim", "question_result_text"})
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["semantic_support"], "not_established")
        self.assertEqual(report["formal_delivery_gate"], "not_run")
        self.assertEqual(bytes_in(self.root), before)

    def test_propagate_policy_audit_reports_real_mode_without_writing(self):
        self.state["paper_framework"]["claim_consumption_policy"].update(
            protocol_version="1.1.0", mode="propagate",
        )
        save(self.root, self.state)
        before = bytes_in(self.root)
        report = audit.inspect_project(self.root)
        self.assertEqual(report["status"], "observed", report)
        self.assertEqual((report["policy_protocol_version"], report["mode"]),
                         ("1.1.0", "propagate"))
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["formal_delivery_gate"], "not_run")
        self.assertEqual(bytes_in(self.root), before)

    def test_partial_unknown_or_mismatched_policy_blocks_before_b1(self):
        original = deepcopy(self.state["paper_framework"]["claim_consumption_policy"])
        for policy in (None, {}, {"mode": "observe"},
                       {**original, "mode": "propagate"},
                       {**original, "protocol_version": "1.1.0"},
                       {**original, "mode": "future"}):
            with self.subTest(policy=policy):
                self.state["paper_framework"]["claim_consumption_policy"] = policy
                save(self.root, self.state)
                before = bytes_in(self.root)
                with patch.object(audit.claim_evidence, "inspect_project",
                                  side_effect=AssertionError("B1 called")):
                    report = audit.inspect_project(self.root)
                self.assertEqual(report["status"], "blocked", report)
                self.assertEqual(report["b1_status"], "not_assessed")
                self.assertEqual(bytes_in(self.root), before)

    def test_b01_second_location_110_conflicts_with_same_live_100(self):
        (self.root / "final_latex/result.tex").write_text("Result: 110.00.\n", encoding="utf-8")
        before = bytes_in(self.root)
        report = audit.inspect_project(self.root)
        self.assertEqual(report["status"], "blocked", report)
        by_fragment = {item["fragment_id"]: item for item in report["numeric_checks"]}
        self.assertEqual(by_fragment["paper.abstract.q1"]["status"], "matched")
        self.assertEqual(by_fragment["paper.result.q1"]["status"], "conflict")
        self.assertEqual(by_fragment["paper.result.q1"]["expected_value"], "100.00")
        self.assertEqual(by_fragment["paper.result.q1"]["observed_value"], "110.00")
        self.assertEqual(by_fragment["paper.result.q1"]["source_file"], "final_latex/result.tex")
        self.assertEqual(by_fragment["paper.result.q1"]["line"], 1)
        self.assertEqual(bytes_in(self.root), before)

    def test_unicode_minus_cannot_turn_negative_paper_number_positive(self):
        (self.root / "final_latex/result.tex").write_text("Result: −100.00.\n", encoding="utf-8")
        before = bytes_in(self.root)
        report = audit.inspect_project(self.root)
        self.assertEqual(report["b1_status"], "evidence_checked", report)
        self.assertEqual(report["status"], "blocked", report)
        checks = {row["fragment_id"]: row for row in report["numeric_checks"]}
        self.assertEqual(checks["paper.abstract.q1"]["status"], "matched")
        self.assertEqual(checks["paper.result.q1"]["status"], "conflict")
        self.assertEqual(checks["paper.result.q1"]["expected_value"], "100.00")
        self.assertEqual(checks["paper.result.q1"]["observed_value"], "-100.00")
        self.assertEqual(bytes_in(self.root), before)

    def test_tex_percent_notation_is_reviewed_before_numeric_unit_attribution(self):
        result = self.root / "final_latex/result.tex"
        for prose in ("Result: 100.00\\,\\%\n", "Result: \\SI{100.00}{\\percent}\n"):
            with self.subTest(prose=prose):
                result.write_text(prose, encoding="utf-8")
                report = audit.inspect_project(self.root)
                self.assertEqual(report["b1_status"], "evidence_checked", report)
                self.assertEqual(report["status"], "needs_review", report)
                checks = {row["fragment_id"]: row for row in report["numeric_checks"]}
                self.assertEqual(checks["paper.result.q1"]["status"], "needs_review")
                self.assertIn("unit", checks["paper.result.q1"]["reason"])

    def test_b01_equal_number_with_wrong_body_precision_needs_review(self):
        # Decimal equality alone would accept 100 and 100.00 as the same value.
        (self.root / "final_latex/result.tex").write_text("Result: 100\n", encoding="utf-8")
        report = audit.inspect_project(self.root)
        self.assertEqual(report["b1_status"], "evidence_checked", report)
        self.assertEqual(report["status"], "needs_review", report)
        checks = {row["fragment_id"]: row for row in report["numeric_checks"]}
        self.assertEqual(checks["paper.abstract.q1"]["status"], "matched")
        self.assertEqual(checks["paper.result.q1"]["status"], "needs_review")
        self.assertEqual(checks["paper.result.q1"]["expected_value"], "100.00")
        self.assertIn("precision", checks["paper.result.q1"]["reason"])

    def test_missing_policy_does_not_call_b1_or_scan_tex(self):
        self.state["paper_framework"].pop("claim_consumption_policy")
        save(self.root, self.state)
        before = bytes_in(self.root)
        with patch.object(audit.claim_evidence, "inspect_project", side_effect=AssertionError("B1 called")):
            with patch.object(audit, "scan_static_latex", side_effect=AssertionError("TeX scanned")):
                report = audit.inspect_project(self.root)
        self.assertEqual(report["status"], "not_assessed", report)
        self.assertIsNone(report["mode"])
        self.assertEqual(report["b1_status"], "not_assessed")
        self.assertEqual(bytes_in(self.root), before)

    def test_b09_b10_overbroad_wording_requires_review(self):
        entry = self.state["subproblems"]["Q1"]
        entry["optimality_claim"] = "heuristic"
        entry["result_analysis_status"] = "not_required"
        (self.root / "final_latex/result.tex").write_text(
            "Result: 100.00; globally optimal and robust across all cases.\n", encoding="utf-8",
        )
        save(self.root, self.state)
        report = audit.inspect_project(self.root)
        self.assertEqual(report["status"], "needs_review", report)
        self.assertEqual(report["b1_status"], "evidence_checked", report)
        self.assertEqual({row["code"] for row in report["wording_findings"]},
                         {"global_optimality_exceeds_registered_status",
                          "broad_robustness_without_required_analysis"})
        self.assertEqual(report["semantic_support"], "not_established")

    def test_global_abstract_inherits_linked_q1_wording_limits(self):
        self.fragments[0]["scope"] = "global"
        entry = self.state["subproblems"]["Q1"]
        entry["optimality_claim"] = "heuristic"
        entry["result_analysis_status"] = "not_required"
        (self.root / "final_latex/abstract.tex").write_text(
            "Answer: 100.0; globally optimal and robust across all cases.\n", encoding="utf-8",
        )
        self._save_with_projection()
        report = audit.inspect_project(self.root)
        self.assertEqual(report["b1_status"], "evidence_checked", report)
        self.assertEqual(report["status"], "needs_review", report)
        findings = {row["code"] for row in report["wording_findings"]
                    if row["fragment_id"] == "paper.abstract.q1"}
        self.assertEqual(findings,
                         {"global_optimality_exceeds_registered_status",
                          "broad_robustness_without_required_analysis"})

    def test_b11_workbook_drift_blocks_current_b1_qualification(self):
        workbook = self.root / self.state["subproblems"]["Q1"]["solution_workbook"]
        workbook.write_bytes(workbook.read_bytes() + b"drift")
        before = bytes_in(self.root)
        report = audit.inspect_project(self.root)
        self.assertEqual(report["status"], "blocked", report)
        self.assertEqual(report["b1_status"], "blocked", report)
        self.assertEqual(report["numeric_checks"], [])
        self.assertEqual(bytes_in(self.root), before)

    def test_b12_disposition_suggests_local_stale_with_reason_without_writing(self):
        self.fragments[0]["depends_on"].append("paper.result.q1")
        self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"] = [{
            "id": "E1", "method_or_source": "synthetic analysis", "target_claim": "answer_claim",
            "disposition": "modify", "key_finding": "synthetic correction",
            "required_action": "review both fragments", "status": "current",
        }]
        self._save_with_projection()
        before = bytes_in(self.root)
        report = audit.inspect_project(self.root)
        self.assertEqual(report["status"], "needs_review", report)
        self.assertEqual(report["suggested_stale_fragment_ids"],
                         ["paper.abstract.q1", "paper.result.q1"])
        self.assertTrue(any(row["disposition_id"] == "E1" and
                            row["path"][0] == "claim:answer_claim"
                            for row in report["stale_reason_paths"]))
        self.assertTrue(all(row["fragment_status"] == "current"
                            for row in report["fragment_locations"]))
        self.assertEqual(bytes_in(self.root), before)

    def test_unknown_paper_fragment_dependency_blocks_opted_in_graph(self):
        self.fragments[1]["depends_on"].append("paper.missing")
        self._save_with_projection()
        with patch.object(audit.claim_evidence, "inspect_project", side_effect=AssertionError("B1 called")):
            report = audit.inspect_project(self.root)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(any("unknown paper fragment" in error for error in report["errors"]), report)

    def test_multiple_claims_in_one_fragment_are_not_silent_numeric_matches(self):
        other = deepcopy(self.state["paper_framework"]["claim_evidence"]["claims"][0])
        other["id"] = "answer_secondary"
        other["text"] = "Second synthetic claim using the same accepted number."
        self.state["paper_framework"]["claim_evidence"]["claims"].append(other)
        self.fragments[1]["depends_on"].append("claim:answer_secondary")
        self._save_with_projection()
        report = audit.inspect_project(self.root)
        self.assertEqual(report["b1_status"], "evidence_checked", report)
        self.assertEqual(report["status"], "needs_review", report)
        checks = {row["fragment_id"]: row for row in report["numeric_checks"]}
        self.assertEqual(checks["paper.result.q1"]["status"], "not_assessed")
        self.assertIn("multiple linked claims", checks["paper.result.q1"]["reason"])

    def test_b16_missing_registered_coverage_and_unregistered_number_need_review(self):
        self.fragments.pop()
        self._save_with_projection()
        before = bytes_in(self.root)
        report = audit.inspect_project(self.root)
        self.assertEqual(report["status"], "needs_review", report)
        by_kind = {row["fragment_kind"]: row for row in report["required_coverage"]}
        self.assertEqual(by_kind["question_result_text"]["status"], "gap")
        self.assertEqual(by_kind["question_result_text"]["registered_fragment_ids"], [])
        self.assertTrue(any(row["literal"] == "100.00" and
                            row["source_file"] == "final_latex/result.tex"
                            for row in report["unregistered_candidates"]))
        self.assertEqual(report["human_semantic_coverage"], "not_assessed")
        self.assertEqual(bytes_in(self.root), before)

    def test_unlocated_registered_claim_fragment_outside_obligations_needs_review(self):
        self.fragments.append({
            "id": "paper.evaluation.q1", "kind": "model_evaluation_claim", "scope": "Q1",
            "depends_on": ["claim:answer_claim"], "anchor": "Evaluation:",
            "source_file": "final_latex/unincluded.tex", "status": "current",
        })
        self._save_with_projection()
        before = bytes_in(self.root)
        report = audit.inspect_project(self.root)
        self.assertEqual(report["b1_status"], "evidence_checked", report)
        self.assertEqual(report["status"], "needs_review", report)
        locations = {row["id"]: row for row in report["fragment_locations"]}
        self.assertEqual(locations["paper.evaluation.q1"]["status"], "not_assessed")
        self.assertIn("active include graph", locations["paper.evaluation.q1"]["reason"])
        self.assertEqual({row["status"] for row in report["required_coverage"]}, {"located"})
        self.assertEqual(bytes_in(self.root), before)

    def test_registered_section_without_claim_edge_does_not_hide_extra_number(self):
        self.fragments.append({
            "id": "paper.aside.q1", "kind": "paper_section", "scope": "Q1",
            "depends_on": [], "anchor": "Aside:",
            "source_file": "final_latex/result.tex", "status": "current",
        })
        (self.root / "final_latex/result.tex").write_text(
            "Result: 100.00.\nAside: 777\n", encoding="utf-8",
        )
        self._save_with_projection()
        report = audit.inspect_project(self.root)
        self.assertEqual(report["b1_status"], "evidence_checked", report)
        self.assertEqual(report["status"], "needs_review", report)
        self.assertTrue(any(row["literal"] == "777" and
                            row["source_file"] == "final_latex/result.tex"
                            for row in report["unregistered_candidates"]), report)
        self.assertEqual({row["status"] for row in report["required_coverage"]}, {"located"})

    def test_two_fragments_sharing_same_anchor_are_not_both_located(self):
        self.fragments.append({
            "id": "paper.abstract.other", "kind": "model_evaluation_claim", "scope": "Q1",
            "depends_on": ["claim:answer_claim"], "anchor": "Answer:",
            "source_file": "final_latex/abstract.tex", "status": "current",
        })
        self._save_with_projection()
        report = audit.inspect_project(self.root)
        self.assertEqual(report["b1_status"], "evidence_checked", report)
        self.assertEqual(report["status"], "needs_review", report)
        locations = {row["id"]: row for row in report["fragment_locations"]}
        for fragment_id in ("paper.abstract.q1", "paper.abstract.other"):
            self.assertEqual(locations[fragment_id]["status"], "not_assessed")
            self.assertIn("share one source anchor", locations[fragment_id]["reason"])
        abstract = next(row for row in report["required_coverage"]
                        if row["fragment_kind"] == "abstract_claim")
        self.assertEqual(abstract["status"], "gap")

    def test_full_framework_row_mismatch_blocks_before_b1(self):
        framework = self.root / "模型论文框架.md"
        text = framework.read_text(encoding="utf-8").replace(
            "| Result: |", "| Wrong anchor: |", 1,
        )
        framework.write_text(text, encoding="utf-8")
        self.state["paper_framework"]["sha256"] = sha256_text(text)
        save(self.root, self.state)
        with patch.object(audit.claim_evidence, "inspect_project", side_effect=AssertionError("B1 called")):
            report = audit.inspect_project(self.root)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(any("row differ" in error for error in report["errors"]), report)

    def test_tex_read_set_drift_during_scan_blocks_return(self):
        path = self.root / "final_latex/result.tex"
        original = audit.scan_static_latex

        def drift(root, main):
            observed = original(root, main)
            path.write_bytes(path.read_bytes() + b"% concurrent edit\n")
            return observed

        with patch.object(audit, "scan_static_latex", side_effect=drift):
            report = audit.inspect_project(self.root)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(any("read-set conflict" in error for error in report["errors"]), report)


class ClaimNumericTokenizerTests(unittest.TestCase):
    def test_unicode_minus_in_exponent_is_one_number(self):
        tokens = audit._numeric_tokens("1.20e−3")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0][0], Decimal("0.00120"))


if __name__ == "__main__":
    unittest.main()
