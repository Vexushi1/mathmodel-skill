import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from runtime_assurance import hydrate_project_context, reconcile_legacy_artifacts
from resolve_runtime import resolve_runtime
from tests import test_solver_backends as solver_fixtures


class RuntimeQualificationTests(unittest.TestCase):
    def state(self, root, *, primary=True, analysis=True):
        (root / "state").mkdir()
        (root / "问题一求解").mkdir()
        hashes = {}
        for layer, name in (("solution_workbook", "问题一求解结果.xlsx"),
                            ("result_analysis_workbook", "问题一结果深化分析.xlsx")):
            path = root / "问题一求解" / name
            path.write_bytes(layer.encode())
            hashes[layer] = hashlib.sha256(path.read_bytes()).hexdigest()
        fixture = solver_fixtures.SolverBackendTests()
        fixture.root = root
        primary_config = fixture.config("python")
        primary_source = fixture.source(primary_config)
        entry = fixture.entry(primary_source, primary_config, accepted=primary)
        analysis_config = fixture.config("python", stage="analysis",
                                         primary_workbook_sha256=hashes["solution_workbook"])
        analysis_source = fixture.source(analysis_config)
        analysis_entry = fixture.entry(analysis_source, analysis_config, accepted=analysis)
        entry.update(result_analysis_code=analysis_entry["result_analysis_code"],
                     analysis_code_sha256=analysis_entry["analysis_code_sha256"])
        entry["solver_execution"].update(analysis_entry["solver_execution"])
        artifact_hashes = {**hashes, "data": primary_config["data_sha256"],
                           "primary_code": entry["primary_code_sha256"],
                           "analysis_code": entry["analysis_code_sha256"]}
        entry.update({
            "classification": {"objective": "optimization", "structures": []},
            "primary_execution_status": "accepted" if primary else "pending",
            "result_quality_status": "passed" if primary else "pending",
            "analysis_execution_status": "accepted" if analysis else "pending",
            "result_analysis_status": "passed" if analysis else "pending",
            "solution_workbook": "问题一求解/问题一求解结果.xlsx",
            "result_analysis_workbook": "问题一求解/问题一结果深化分析.xlsx",
            "artifact_hashes": artifact_hashes, "validated_artifact_hashes": dict(artifact_hashes),
            "validated_data_hash": primary_config["data_sha256"],
        })
        return {"project": {"competition": "CUMCM"},
                "execution": {"solver_backend": "python",
                              "solver_backend_selection_reason": "Synthetic whole-problem review"},
                "preprocessing": {"decision": "not_needed", "status": "not_applicable"},
                "subproblems": {"Q1": entry}}

    def write(self, root, state):
        (root / "state/project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")

    def test_primary_aliases_cannot_clear_known_invalid_current_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.state(root, primary=False, analysis=False)
            self.write(root, state)
            for alias in ("accepted_solution_workbook", "solution_workbook", "solved_results", "result_quality_report"):
                with self.subTest(alias=alias):
                    plan = resolve_runtime("figures", project_root=root, question="Q1",
                                           available_artifacts=[alias])
                    assurance = plan["assurance"]
                    self.assertEqual(assurance["status"], "review_required")
                    self.assertNotIn(alias, assurance["artifact_assurance"]["effective_artifacts"])
                    self.assertTrue(plan["missing_prerequisites"])

    def test_analysis_only_does_not_promote_current_results_or_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, self.state(root, primary=False))
            hydration = hydrate_project_context(root, "Q1")
            for alias in ("validated_results", "accepted_result_analysis_workbook", "result_analysis_workbook"):
                with self.subTest(alias=alias):
                    self.assertNotIn(alias, hydration["verified_artifacts"])
                    effective, _, conflicts = reconcile_legacy_artifacts([alias], hydration)
                    self.assertNotIn(alias, effective)
                    self.assertTrue(conflicts)

    def test_analysis_pending_cannot_be_relabelled_validated_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, self.state(root, analysis=False))
            hydration = hydrate_project_context(root, "Q1")
            effective, _, conflicts = reconcile_legacy_artifacts(["validated_results"], hydration)
            self.assertNotIn("validated_results", effective)
            self.assertTrue(conflicts)

    def test_valid_primary_and_required_or_exempt_analysis_remain_available(self):
        for disposition in ("passed", "not_required"):
            with self.subTest(disposition=disposition), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                state = self.state(root)
                item = state["subproblems"]["Q1"]
                if disposition == "not_required":
                    item.update(result_analysis_status=disposition, analysis_execution_status="pending",
                                result_analysis_requirement_reason="Only observed-world claims are needed")
                    (root / item["result_analysis_workbook"]).unlink()
                    for field in ("result_analysis_code", "analysis_code_sha256", "result_analysis_workbook"):
                        item.pop(field, None)
                    item["solver_execution"].pop("analysis", None)
                    for field in ("artifact_hashes", "validated_artifact_hashes"):
                        for layer in ("analysis_code", "result_analysis_workbook"):
                            item[field].pop(layer, None)
                self.write(root, state)
                hydration = hydrate_project_context(root, "Q1")
                self.assertIn("validated_results", hydration["verified_artifacts"])
                effective, _, conflicts = reconcile_legacy_artifacts(
                    ["solution_workbook", "solved_results", "result_quality_report", "validated_results"], hydration)
                self.assertEqual(conflicts, [])
                self.assertIn("solved_results", effective)

    def test_current_accepted_analysis_requires_its_delivered_source_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.state(root)
            item = state["subproblems"]["Q1"]
            item.pop("result_analysis_code")
            item.pop("analysis_code_sha256")
            item["solver_execution"].pop("analysis")
            self.write(root, state)
            hydration = hydrate_project_context(root, "Q1")
            self.assertIn("accepted_solution_workbook", hydration["verified_artifacts"])
            self.assertNotIn("accepted_result_analysis_workbook", hydration["verified_artifacts"])
            self.assertNotIn("validated_results", hydration["verified_artifacts"])
            row = next(e for e in hydration["artifact_evidence"]
                       if e["artifact"] == "accepted_result_analysis_workbook")
            self.assertIn("analysis缺少已交付入口路径", row["reason"])

    def test_not_required_cannot_keep_current_analysis_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.state(root)
            item = state["subproblems"]["Q1"]
            item.update(result_analysis_status="not_required", analysis_execution_status="pending",
                        result_analysis_requirement_reason="Only primary results are needed")
            self.write(root, state)
            hydration = hydrate_project_context(root, "Q1")
            self.assertIn("accepted_solution_workbook", hydration["verified_artifacts"])
            self.assertNotIn("validated_results", hydration["verified_artifacts"])
            row = next(e for e in hydration["artifact_evidence"]
                       if e["artifact"] == "result_analysis_not_required")
            self.assertEqual(row["status"], "not_accepted")
            self.assertIn("current analysis numerical identity", row["reason"])

    def test_relevant_stale_layers_block_results_but_figure_only_stale_does_not(self):
        for layer in ("data", "primary_code", "solution_workbook", "analysis_code", "result_analysis_workbook", "figure_bundle"):
            with self.subTest(layer=layer), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                state = self.state(root)
                state["subproblems"]["Q1"].update(artifacts_stale=True, stale_layers=[layer])
                self.write(root, state)
                hydration = hydrate_project_context(root, "Q1")
                self.assertEqual("validated_results" in hydration["verified_artifacts"], layer == "figure_bundle")

    def test_unscoped_aggregation_requires_every_questions_primary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.state(root)
            state["subproblems"]["Q2"] = {"primary_execution_status": "pending"}
            self.write(root, state)
            self.assertNotIn("validated_results", hydrate_project_context(root)["verified_artifacts"])
            self.assertIn("validated_results", hydrate_project_context(root, "Q1")["verified_artifacts"])

    def test_current_primary_identity_cannot_reuse_an_old_accepted_label(self):
        for drift in ("data", "code", "unknown_stale"):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                state = self.state(root)
                item = state["subproblems"]["Q1"]
                if drift == "data":
                    item.update(data_hash="a" * 64, validated_data_hash="b" * 64)
                elif drift == "code":
                    code = root / "primary.py"
                    code.write_text("# modified after acceptance\n", encoding="utf-8")
                    item.update(code="primary.py", primary_code_sha256="a" * 64)
                else:
                    item.update(artifacts_stale=True, stale_layers=[])
                self.write(root, state)
                hydration = hydrate_project_context(root, "Q1")
                self.assertNotIn("accepted_solution_workbook", hydration["verified_artifacts"])
                self.assertNotIn("validated_results", hydration["verified_artifacts"])

    def test_no_project_name_only_compatibility_is_still_unverified(self):
        effective, rows, conflicts = reconcile_legacy_artifacts(
            ["solution_workbook", "validated_results"], {"loaded": False})
        self.assertEqual(effective, ["solution_workbook", "validated_results"])
        self.assertEqual(conflicts, [])
        self.assertTrue(all(row["status"] == "declared_unverified" for row in rows))


if __name__ == "__main__":
    unittest.main()
