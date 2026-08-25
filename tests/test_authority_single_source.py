from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_RESOLVER_POLICY_CONSTANTS = (
    "PRIMARY_CODE_GATES", "ANALYSIS_CODE_GATES", "SEMANTIC_CODE_GATES", "SEMANTIC_SYNC_GATES",
    "SUBMISSION_GATES", "MODEL_APPROVAL_OUTPUTS", "PREPROCESSING_OUTPUTS", "PRIMARY_CODE_OUTPUTS",
    "ANALYSIS_CODE_OUTPUTS", "FINAL_WORKFLOW_OUTPUTS", "DOWNSTREAM_MODULES", "MODEL_APPROVAL_REQUIRED_INTENTS",
)


def load_resolver():
    path = ROOT / "scripts/resolve_workflow.py"
    spec = importlib.util.spec_from_file_location("authority_single_source_resolver", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestAuthoritySingleSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        cls.manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        cls.resolver = load_resolver()

    def test_router_owns_order_and_runtime_boundaries(self):
        self.assertIn("workflow_order", self.router["execution_contract"])
        self.assertIn("runtime_segments", self.router)
        self.assertNotIn("workflow_order", self.manifest)
        self.assertNotIn("workflow_profiles", self.manifest)
        compat = self.manifest["workflow_profile_compatibility"]
        self.assertEqual(compat["authority"], "core/workflow_router.yaml")
        self.assertFalse(compat["runtime_consumed"])

    def test_resolver_contains_no_embedded_policy_collections(self):
        text = (ROOT / "scripts/resolve_workflow.py").read_text(encoding="utf-8")
        for token in FORBIDDEN_RESOLVER_POLICY_CONSTANTS:
            self.assertNotIn(token, text, token)
        self.assertIn("runtime_segment", text)
        self.assertIn("route_boundary_roles", text)

    def test_route_boundary_roles_are_declarative(self):
        expected = {
            "new_problem_design": {"model_approval"},
            "model_selection": {"model_approval"},
            "advanced_method": {"model_approval"},
            "data_preprocessing": {"model_approval", "preprocessing"},
            "full_solution": {"model_approval", "preprocessing", "primary_execution"},
            "full_workflow": {"model_approval", "preprocessing", "primary_execution", "full_workflow_resume"},
            "code_and_solution": {"model_approval", "preprocessing", "primary_execution"},
            "result_analysis": {"model_approval", "analysis_execution"},
            "validation": {"model_approval", "analysis_execution"},
        }
        for route, roles in expected.items():
            self.assertEqual(set(self.router["routing"][route]["boundary_roles"]), roles, route)

    def test_model_approval_and_execution_boundaries_preserve_plan_semantics(self):
        no_approval = self.resolver.resolve_workflow(
            "full_solution", objective="optimization", structures=["stochastic"], preprocessing_decision="not_needed"
        )
        self.assertEqual(no_approval["pause_state"], "awaiting_model_approval")
        self.assertNotIn("modules/03_solve_validate.md", no_approval["modules"])

        design_outputs = set(self.manifest["modules"]["model_design"]["outputs"])
        design_outputs.add("locked_model_spec")
        primary = self.resolver.resolve_workflow(
            "full_solution",
            objective="optimization",
            structures=["stochastic"],
            available_artifacts=sorted(design_outputs),
            preprocessing_decision="not_needed",
        )
        self.assertEqual(primary["pause_state"], "awaiting_user_execution")
        self.assertIn("modules/03_solve_validate.md", primary["modules"])
        self.assertEqual([g["name"] for g in primary["pre_delivery_gates"]], ["semantic_governance", "model_approval", "code_delivery"])

    def test_full_workflow_resumes_analysis_then_submission_from_router_segments(self):
        all_artifacts = set(self.manifest["artifact_catalog"])
        analysis_pending = all_artifacts - {"accepted_result_analysis_workbook", "result_analysis_workbook", "validated_results"}
        analysis_plan = self.resolver.resolve_workflow(
            "full_workflow",
            objective="optimization",
            structures=["stochastic"],
            available_artifacts=sorted(analysis_pending),
            preprocessing_decision="not_needed",
        )
        self.assertEqual(analysis_plan["pause_state"], "awaiting_user_execution")
        self.assertIn("modules/03_result_analysis.md", analysis_plan["modules"])

        final_plan = self.resolver.resolve_workflow(
            "full_workflow",
            objective="optimization",
            structures=["stochastic"],
            available_artifacts=sorted(all_artifacts),
            preprocessing_decision="not_needed",
        )
        self.assertIsNone(final_plan["pause_state"])
        self.assertIn("modules/04_figure_evidence.md", final_plan["modules"])
        self.assertIn("modules/05_writing/latex.md", final_plan["modules"])
        self.assertIn("modules/06_review_delivery.md", final_plan["modules"])
        self.assertEqual([g["name"] for g in final_plan["pre_delivery_gates"]], ["semantic_governance", "project_sync", "submission_package_validation"])


if __name__ == "__main__":
    unittest.main()
