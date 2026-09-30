"""E1 A/B/C chains on real isolated synthetic execution outputs.

Receipt records below are synthetic declarations of separated review passes.
They test snapshot applicability, never attest human review or independent
execution. Only fixture construction is patched; no gate result is mocked.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import claim_consumption as consumption
import claim_evidence
import claim_tex
import conformance_gate
import model_code_conformance
import review_receipt_consumption as review_consumption
import review_receipts
import runtime_assurance
import sync_project
from tests import test_claim_consumption as claim_fixture
from tests import test_b2b4_figure_integration as figure_fixture
from tests import test_model_code_conformance as conformance_fixture
from tests.claim_fixture import record


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CrossModuleAcceptanceTests(unittest.TestCase):
    """Reuse one genuinely executed primary/analysis seed for all chains."""

    @classmethod
    def setUpClass(cls):
        original = claim_fixture.smoke.instantiate_stage

        def with_helper(root, backend, stage, state):
            code, config = original(root, backend, stage, state)
            helper = code.parent / "e1_helper.py"
            helper.write_text("def checked_solution(value):\n    return value\n", encoding="utf-8")
            old_config = repr(config)
            config["code_dependencies"] = [{
                "path": helper.relative_to(root).as_posix(), "sha256": digest(helper),
            }]
            text = code.read_text(encoding="utf-8")
            marker = "RUN_CONFIG = " + old_config
            if text.count(marker) != 1:
                raise AssertionError("synthetic RUN_CONFIG marker is ambiguous")
            text = text.replace(marker, "RUN_CONFIG = " + repr(config), 1)
            old_bundle = 'digest(root, [code.relative_to(root).as_posix()])'
            if text.count(old_bundle) != 1:
                raise AssertionError("synthetic receipt bundle marker is ambiguous")
            text = text.replace(old_bundle,
                                'digest(root, [code.relative_to(root).as_posix(), '
                                '*[row["path"] for row in config["code_dependencies"]]])', 1)
            # The helper participates in the calculation and in both stage
            # receipt bundles. A later helper change cannot reuse the seed.
            text = text.replace("solution = b / a", "solution = checked_solution(b / a)", 1)
            text = text.replace("import openpyxl\n",
                                "import openpyxl\nfrom e1_helper import checked_solution\n", 1)
            code.write_text(text, encoding="utf-8")
            return code, config

        with patch.object(claim_fixture.smoke, "instantiate_stage", side_effect=with_helper):
            figure_fixture.FigureFormalChainIntegrationTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        figure_fixture.FigureFormalChainIntegrationTests.tearDownClass.__func__(cls)

    save_projection = figure_fixture.FigureFormalChainIntegrationTests.save_projection
    set_caption = figure_fixture.FigureFormalChainIntegrationTests.set_caption

    def setUp(self):
        figure_fixture.FigureFormalChainIntegrationTests.setUp(self)
        self.addCleanup(self.tmp.cleanup)
        framework = self.state["paper_framework"]
        framework["claim_consumption_policy"].update(
            protocol_version="1.5.0", mode="enforce_selected_paper_claim_chain",
            paper_source={"format": "latex", "entrypoint": "final_latex/main.tex"},
        )
        # C2 paper consumption requires selected carrier 1.5. Reuse the
        # existing complete Figure fixture instead of declaring an incomplete
        # selected policy on a text-only fixture. Its image is an identity
        # fixture; neither review below claims rendered or visual approval.
        for binding in framework["claim_consumption_policy"]["figure_bindings"]:
            binding["carrier_locator"] = {
                "kind": "latex_label", "value": binding.pop("latex_label"),
            }
        main = self.root / "final_latex/main.tex"
        main.write_text(main.read_text(encoding="utf-8").replace(
            "\\begin{document}", "\\title{Synthetic scalar equation study}\n\\begin{document}", 1),
            encoding="utf-8")
        pdf = self.root / "final_latex/main.pdf"
        pdf.write_bytes(b"synthetic PDF identity; no compilation or rendering claim\n")
        self.state.setdefault("artifacts", {})["compiled_pdf"] = "final_latex/main.pdf"
        self.save_projection()
        self.install_bound_review_pair()
        self.assert_current_chain()

    def install_bound_review_pair(self):
        gate = "final_review_and_delivery"
        matrix = yaml.safe_load((ROOT / "templates/review/final_review_matrix.yaml").read_text(encoding="utf-8"))
        checks = [row["check_family"] for row in matrix["coverage"]]
        scan = claim_tex.scan_static_latex(
            self.root, self.root / "final_latex/main.tex", selected_carrier=True)
        self.assertEqual(scan["status"], "scanned", scan)
        objects = ["paper_source:final_latex/main.tex", "rendered:final_latex/main.pdf"]
        objects += ["source:" + path for path in sorted(scan["files"])]
        approved_images = self.state["artifacts"]["approved_figures"]
        objects += ["figure:" + path for path in sorted(approved_images)]
        roles = [{"role": role, "check_ids": list(checks)}
                 for role in ("semantic_reviewer", "final_reviewer")]
        self.state["review_receipt_policy"] = {
            "protocol_version": "1.0.0", "mode": "enforce_scoped",
            "requirements": [{"gate": gate, "questions": ["Q1"],
                              "object_ids": objects, "roles": roles}],
        }
        contract = yaml.safe_load((ROOT / "core/review_receipt_contract.yaml").read_text(encoding="utf-8"))
        authority_paths = set(contract["required_authority_paths"])
        authority_paths.update(contract["gate_authorities"][gate]["required_paths"])
        authority_paths.update(contract["gate_authorities"][gate]["latex_required_paths"])
        authority_paths.add("core/review_receipt_consumption_contract.yaml")
        authorities = [{"path": path, "sha256": digest(ROOT / path)}
                       for path in sorted(authority_paths)]
        pointers = {
            "/review_receipt_policy": self.state["review_receipt_policy"],
            "/paper_framework/claim_consumption_policy/paper_source":
                self.state["paper_framework"]["claim_consumption_policy"]["paper_source"],
            "/artifacts/compiled_pdf": self.state["artifacts"]["compiled_pdf"],
            "/artifacts/approved_figures": approved_images,
        }
        fields = [{"pointer": pointer, "sha256": review_receipts.state_field_sha256(value)}
                  for pointer, value in pointers.items()]
        entry = self.state["subproblems"]["Q1"]
        paths = {*scan["files"], "final_latex/main.pdf", "问题一求解/e1_helper.py"}
        paths.update(entry[field] for field in (
            "code", "result_analysis_code", "solution_workbook", "result_analysis_workbook"))
        paths.update(approved_images)
        # These supplemental input bindings are the scope of this fixture, not
        # a new requirement that every paper receipt bind every helper.
        files = [{"path": path, "sha256": digest(self.root / path)} for path in sorted(paths)]
        records = []
        for index, role in enumerate(roles, 1):
            scope = {"questions": ["Q1"], "object_ids": list(objects)}
            snapshot = {
                "state_generation": self.state["project"].get("state_generation", 0),
                "state_fields": deepcopy(fields), "project_files": deepcopy(files),
                "authorities": deepcopy(authorities),
                "fingerprint_sha256": review_receipts.snapshot_fingerprint(
                    fields, files, authorities, gate=gate, role=role["role"],
                    scope=scope, criteria_version="1.0.0"),
            }
            records.append({
                "review_id": f"E1-review-{index}", "gate": gate, "role": role["role"],
                "criteria_version": "1.0.0", "scope": scope, "snapshot": snapshot,
                "execution": {"method": "separated_passes", "source_kind": "assistant_record",
                              "source_locator": f"synthetic/e1-pass-{index}",
                              "pass_id": f"e1-pass-{index}"},
                "checks": [{"id": check, "object_ids": list(objects), "result": "pass",
                            "evidence_locator": f"synthetic/e1-pass-{index}#{check}"}
                           for check in role["check_ids"]],
                "findings": [], "uncovered": [], "verdict": "pass",
            })
        self.state["review_receipts"] = {"protocol_version": "1.0.0", "records": records}
        conformance_fixture.save(self.root, self.state)

    def assert_current_chain(self):
        a_report = model_code_conformance.inspect_project(self.root, "Q1", "primary")
        self.assertEqual(a_report["status"], "structure_verified", a_report)
        b_report = claim_evidence.inspect_project(self.root)
        self.assertEqual(b_report["status"], "evidence_checked", b_report)
        observed = consumption.inspect_project(self.root)
        # The generic Figure numeric row retains its not_assessed boundary;
        # the exact selected-carrier Figure gate separately checks its current
        # caption/source identity. Neither result grants visual semantics.
        self.assertEqual(observed["status"], "needs_review", observed)
        self.assertEqual({row["fragment_id"]: row["status"]
                          for row in observed["numeric_checks"]
                         if row.get("fragment_id") in {"paper.abstract.q1", "paper.result.q1"}},
                         {"paper.abstract.q1": "matched", "paper.result.q1": "matched"}, observed)
        paper_gate = consumption.formal_paper_gate(self.root)
        self.assertEqual(paper_gate["status"], "passed", paper_gate)
        self.assertEqual(paper_gate["human_semantic_coverage"], "not_assessed", paper_gate)
        c_report = review_consumption.evaluate_gate(self.root, "final_review_and_delivery")
        self.assertEqual(c_report["status"], "passed", c_report)
        self.assertIn("accepted_solution_workbook",
                      runtime_assurance.hydrate_project_context(self.root)["verified_artifacts"])

    def test_helper_drift_rejects_a_b_and_explicitly_bound_old_c_pass(self):
        entry = self.state["subproblems"]["Q1"]
        preserved = {entry[field]: (self.root / entry[field]).read_bytes()
                     for field in ("code", "result_analysis_code", "solution_workbook",
                                   "result_analysis_workbook")}
        helper = self.root / "问题一求解/e1_helper.py"
        helper.write_text("def checked_solution(value):\n    return value + 1\n", encoding="utf-8")
        before = conformance_fixture.bytes_in(self.root)
        a_report = model_code_conformance.inspect_project(self.root, "Q1", "primary")
        self.assertEqual(a_report["status"], "blocked", a_report)
        self.assertTrue(conformance_gate.inspect_gate(
            self.root, self.state, "Q1", "primary", boundary="current")["issues"])
        b_report = claim_evidence.inspect_project(self.root)
        self.assertEqual(b_report["status"], "blocked", b_report)
        observed = consumption.inspect_project(self.root)
        self.assertEqual(observed["status"], "blocked", observed)
        self.assertEqual(observed["numeric_checks"], [])
        inspected = review_receipts.inspect_project(self.root)
        self.assertEqual({row["applicability"] for row in inspected["receipts"]}, {"stale"}, inspected)
        c_report = review_consumption.evaluate_gate(self.root, "final_review_and_delivery")
        self.assertEqual(c_report["status"], "failed", c_report)
        context = runtime_assurance.hydrate_project_context(self.root)
        self.assertNotIn("accepted_solution_workbook", context["verified_artifacts"])
        self.assertEqual(entry["human_model_approval_status"], "approved")
        self.assertEqual(before, conformance_fixture.bytes_in(self.root))
        for path, raw in preserved.items():
            self.assertEqual((self.root / path).read_bytes(), raw)
        # The existing synchronizer supplies the question-to-consumption impact
        # closure, while B refuses to certify old numbers after source drift.
        sync = sync_project.synchronize(self.root, write=False)
        self.assertIn("Q1", sync["stale_questions"], sync)
        self.assertTrue({"paper.abstract.q1", "paper.result.q1"}
                        <= set(sync["stale_paper_fragments"]), sync)
        self.assertEqual(before, conformance_fixture.bytes_in(self.root))

    def test_title_wording_drift_preserves_accepted_numbers_but_stales_text_review(self):
        entry_before = deepcopy(self.state["subproblems"]["Q1"])
        main = self.root / "final_latex/main.tex"
        text = main.read_text(encoding="utf-8")
        old = "\\title{Synthetic scalar equation study}"
        self.assertEqual(text.count(old), 1)
        main.write_text(text.replace(old, "\\title{A study of a synthetic scalar equation}", 1),
                        encoding="utf-8")
        before = conformance_fixture.bytes_in(self.root)
        a_report = model_code_conformance.inspect_project(self.root, "Q1", "primary")
        self.assertEqual(a_report["status"], "structure_verified", a_report)
        b_report = claim_evidence.inspect_project(self.root)
        self.assertEqual(b_report["status"], "evidence_checked", b_report)
        observed = consumption.inspect_project(self.root)
        self.assertEqual(observed["status"], "needs_review", observed)
        self.assertEqual({row["fragment_id"]: row["status"]
                          for row in observed["numeric_checks"]
                         if row.get("fragment_id") in {"paper.abstract.q1", "paper.result.q1"}},
                         {"paper.abstract.q1": "matched", "paper.result.q1": "matched"}, observed)
        paper_gate = consumption.formal_paper_gate(self.root)
        self.assertEqual(paper_gate["status"], "passed", paper_gate)
        self.assertEqual(paper_gate["human_semantic_coverage"], "not_assessed", paper_gate)
        c_report = review_consumption.evaluate_gate(self.root, "final_review_and_delivery")
        self.assertEqual(c_report["status"], "failed", c_report)
        inspected = review_receipts.inspect_project(self.root)
        self.assertEqual({row["applicability"] for row in inspected["receipts"]}, {"stale"}, inspected)
        self.assertIn("accepted_solution_workbook",
                      runtime_assurance.hydrate_project_context(self.root)["verified_artifacts"])
        self.assertEqual(self.state["subproblems"]["Q1"], entry_before)
        self.assertEqual(before, conformance_fixture.bytes_in(self.root))


class ExplicitScenarioAcceptanceTests(unittest.TestCase):
    def test_a06_approved_approximation_is_never_reported_as_strict_equivalence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, _, _ = conformance_fixture.fixture(root)
            mapping = conformance_fixture.declare(root, state, check_expression=True)
            for row in mapping["mappings"]:
                row["relation"] = "approved_approximation"
                row["rationale"] = "Synthetic declared approximation; exactness is not proved."
            conformance_fixture.save(root, state)
            before = conformance_fixture.bytes_in(root)
            result = model_code_conformance.inspect_project(root, "Q1", "primary")
            self.assertEqual(result["status"], "needs_review", result)
            self.assertEqual(result["mathematical_equivalence"], "not_established")
            self.assertTrue(any("approximation applicability" in reason
                                for reason in result["review_required"]), result)
            self.assertEqual(state["subproblems"]["Q1"]["human_model_approval_status"], "approved")
            self.assertEqual(before, conformance_fixture.bytes_in(root))

    def test_b08_external_citation_cannot_substitute_an_own_result_source(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        contract = yaml.safe_load((ROOT / "core/claim_evidence_contract.yaml").read_text(encoding="utf-8"))
        declared = record()
        declared["sources"][0] = {
            "id": "baseline", "kind": "external_citation", "citation_id": "C1",
            "url": "https://example.invalid/synthetic-reference", "value": "100",
        }
        with self.assertRaises(claim_evidence.EvidenceError):
            claim_evidence.validate_record(declared, schema, contract)
