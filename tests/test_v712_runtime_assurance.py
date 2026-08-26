import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_runtime():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(
        "resolve_runtime", ROOT / "scripts/resolve_runtime.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV712RuntimeAssurance(unittest.TestCase):
    def setUp(self):
        self.runtime = load_runtime()

    def _write_state(self, root: Path, state: dict) -> None:
        path = root / "state"
        path.mkdir(parents=True, exist_ok=True)
        (path / "project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def _base_state(self) -> dict:
        semantic_hash = "a" * 64
        return {
            "project": {
                "competition": "CUMCM",
                "problem": "A",
                "current_phase": "solve_validate",
                "version": "current",
            },
            "preprocessing": {
                "decision": "not_needed",
                "status": "not_applicable",
            },
            "subproblems": {
                "Q1": {
                    "classification": {
                        "objective": "optimization",
                        "structures": ["stochastic"],
                    },
                    "capabilities": {
                        "has_explicit_constraints": True,
                        "requires_feasibility_check": True,
                        "requires_equilibrium_residual": False,
                        "requires_conservation_residual": False,
                        "requires_discretization_check": False,
                        "requires_convergence_diagnostic": True,
                    },
                    "model_challenge_status": "passed",
                    "human_model_approval_status": "approved",
                    "semantic_revision": 3,
                    "semantic_hash": semantic_hash,
                    "approved_semantic_revision": 3,
                    "approved_semantic_hash": semantic_hash,
                    "primary_execution_status": "pending",
                    "analysis_execution_status": "pending",
                    "result_quality_status": "pending",
                    "result_analysis_status": "pending",
                }
            },
        }

    def test_default_runtime_adds_assurance_without_breaking_legacy_plan(self):
        plan = self.runtime.resolve_runtime("problem_analysis")
        current_version = yaml.safe_load(
            (ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8")
        )["skill_version"]
        self.assertEqual(plan["version"], current_version)
        self.assertIn("runtime_plan", plan)
        self.assertIn("assurance", plan)
        self.assertEqual(plan["assurance"]["status"], "pass")
        self.assertEqual(
            plan["runtime_plan"]["selected_intents"], ["problem_analysis"]
        )
        self.assertEqual(
            plan["assurance"]["intent_resolution"]["mode"], "explicit"
        )

    def test_explicit_intent_is_authoritative_over_request_keywords(self):
        plan = self.runtime.resolve_runtime(
            "problem_analysis", request="请给出完整求解"
        )
        intent = plan["assurance"]["intent_resolution"]
        self.assertEqual(intent["selected_intents"], ["problem_analysis"])
        self.assertTrue(intent["inferred_candidates"])
        self.assertEqual(plan["intents"], ["problem_analysis"])

    def test_inferred_intent_prefers_specific_keyword_phrase(self):
        plan = self.runtime.resolve_runtime(
            request="请审题并建模", objective="optimization"
        )
        intent = plan["assurance"]["intent_resolution"]
        self.assertEqual(intent["selected_intents"], ["new_problem_design"])
        self.assertFalse(intent["ambiguity"])
        candidates = {item["intent"]: item for item in intent["inferred_candidates"]}
        self.assertGreater(
            candidates["new_problem_design"]["score"],
            candidates["problem_analysis"]["score"],
        )

    def test_intent_provenance_reports_true_top_score_ambiguity(self):
        router = {
            "routing": {
                "route_a": {"infer_keywords": ["同词"]},
                "route_b": {"infer_keywords": ["同词"]},
            }
        }
        selected, diagnostics = self.runtime.resolve_intent_assurance(
            [], "同词", router
        )
        self.assertEqual(selected, ["route_a", "route_b"])
        self.assertTrue(diagnostics["ambiguity"])
        self.assertEqual(diagnostics["confidence_band"], "low")

    def test_module_contract_dependency_closure_is_additive(self):
        plan = self.runtime.resolve_runtime("figures")
        closure = plan["assurance"]["dependency_closure"]
        self.assertIn("workbook", closure["required_aliases"])
        self.assertIn("core/workbook_schema.yaml", plan["contracts"])
        self.assertIn("core/workbook_schema.yaml", plan["load_order"])
        self.assertIn("core/workbook_schema.yaml", closure["added_paths"])

    def test_project_state_hydrates_classification_approval_and_preprocessing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_state(root, self._base_state())
            plan = self.runtime.resolve_runtime(
                "full_solution", project_root=root, question="Q1"
            )
        self.assertEqual(plan["competition"], "CUMCM")
        self.assertEqual(plan["preprocessing_decision"], "not_needed")
        self.assertEqual(plan["classification"]["objective"], "optimization")
        self.assertIn("packs/task/optimization.md", plan["packs"])
        self.assertFalse(plan["pause_for_model_approval"])
        self.assertEqual(plan["pause_state"], "awaiting_user_execution")
        assurance = plan["assurance"]
        self.assertTrue(assurance["context"]["project_state_loaded"])
        self.assertIn(
            "locked_model_spec",
            assurance["artifact_assurance"]["effective_artifacts"],
        )

    def test_verified_primary_workbook_allows_result_analysis_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workbook = root / "问题一求解结果.xlsx"
            workbook.write_bytes(b"verified-workbook")
            digest = hashlib.sha256(workbook.read_bytes()).hexdigest()
            state = self._base_state()
            q1 = state["subproblems"]["Q1"]
            q1.update(
                {
                    "primary_execution_status": "accepted",
                    "result_quality_status": "passed",
                    "solution_workbook": workbook.name,
                    "artifact_hashes": {"solution_workbook": digest},
                }
            )
            self._write_state(root, state)
            plan = self.runtime.resolve_runtime(
                "result_analysis", project_root=root, question="Q1"
            )
        self.assertIn("modules/03_result_analysis.md", plan["modules"])
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        self.assertIn(
            "accepted_solution_workbook",
            plan["assurance"]["artifact_assurance"]["effective_artifacts"],
        )

    def test_known_hash_mismatch_blocks_legacy_artifact_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workbook = root / "问题一求解结果.xlsx"
            workbook.write_bytes(b"actual")
            state = self._base_state()
            q1 = state["subproblems"]["Q1"]
            q1.update(
                {
                    "primary_execution_status": "accepted",
                    "result_quality_status": "passed",
                    "solution_workbook": workbook.name,
                    "artifact_hashes": {"solution_workbook": "b" * 64},
                }
            )
            self._write_state(root, state)
            plan = self.runtime.resolve_runtime(
                "result_analysis",
                project_root=root,
                question="Q1",
                available_artifacts=["accepted_solution_workbook"],
            )
        assurance = plan["assurance"]
        self.assertEqual(assurance["status"], "review_required")
        self.assertTrue(assurance["artifact_assurance"]["conflicts"])
        self.assertNotIn(
            "accepted_solution_workbook",
            assurance["artifact_assurance"]["effective_artifacts"],
        )
        self.assertIn("modules/03_solve_validate.md", plan["modules"])

    def test_artifact_path_outside_project_root_is_never_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "project"
            root.mkdir()
            outside = base / "outside.xlsx"
            outside.write_bytes(b"outside")
            digest = hashlib.sha256(outside.read_bytes()).hexdigest()
            state = self._base_state()
            q1 = state["subproblems"]["Q1"]
            q1.update(
                {
                    "primary_execution_status": "accepted",
                    "result_quality_status": "passed",
                    "solution_workbook": "../outside.xlsx",
                    "artifact_hashes": {"solution_workbook": digest},
                }
            )
            self._write_state(root, state)
            plan = self.runtime.resolve_runtime(
                "result_analysis", project_root=root, question="Q1"
            )
        evidence = plan["assurance"]["artifact_assurance"]["evidence"]
        row = next(
            item
            for item in evidence
            if item["artifact"] == "accepted_solution_workbook"
            and item["scope"] == "Q1"
        )
        self.assertEqual(row["status"], "outside_project_root")
        self.assertNotIn(
            "accepted_solution_workbook",
            plan["assurance"]["artifact_assurance"]["effective_artifacts"],
        )
        self.assertIn("modules/03_solve_validate.md", plan["modules"])


if __name__ == "__main__":
    unittest.main()
