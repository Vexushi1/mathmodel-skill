import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


class TestSchemas(unittest.TestCase):
    def test_project_state_example_validates(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(example)), [])

    def test_classification_has_single_capability_source_and_split_status(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        defs = schema["$defs"]
        self.assertEqual(schema["version"], "6.4.0")
        self.assertEqual(set(defs["classification"]["required"]), {"objective", "structures"})
        subproblems = schema["properties"]["subproblems"]
        sub_required = set(subproblems["additionalProperties"]["required"])
        self.assertEqual(subproblems["minProperties"], 1)
        for name in ("capabilities", "result_quality_status", "result_analysis_status"):
            self.assertIn(name, sub_required)
        phases = set(schema["properties"]["project"]["properties"]["current_phase"]["enum"])
        statuses = set(subproblems["additionalProperties"]["properties"]["status"]["enum"])
        self.assertIn("result_analysis", phases)
        self.assertIn("analyzed", statuses)
        self.assertIn("result_analysis_workbook", defs["artifact_hashes"]["properties"])

    def test_workbook_schema_has_quality_gate_and_adaptive_analysis(self):
        schema = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8"))
        self.assertEqual(schema["schema_version"], "2.2.0")
        self.assertIn(">=6.3.2", schema["skill_compatibility"])
        self.assertEqual(schema["classification_contract"]["capabilities_source"], "subproblem.capabilities")
        self.assertIn("objective_profiles", schema["solution_workbook"])
        self.assertIn("structure_profiles", schema["solution_workbook"])
        self.assertIn("主结果质量门", schema["solution_workbook"]["common_required_sheets"])
        rules = "\n".join(schema["runtime_enforcement"]["rules"])
        self.assertIn("质量门允许记录未通过项", rules)
        self.assertIn("只有主结果质量门全部通过", rules)
        self.assertIn("不得进入下游", schema["solution_workbook"]["role"])
        analysis = schema["result_analysis_workbook"]
        self.assertEqual(set(analysis["common_required_sheets"]), {"分析设计", "结论稳定性汇总"})
        self.assertIn("算法一致性", analysis["required_any_sheets"])
        self.assertIn("结构稳健性", analysis["required_any_sheets"])
        self.assertNotIn("适用性说明", analysis["sheet_schemas"])
        self.assertEqual(schema["matlab_handoff"]["field_resolution"]["method"], "exact_header_unique_match")

    def test_output_contract_defines_split_result_policy(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(contract["version"], "6.4.0")
        self.assertEqual(contract["project_sync"]["role"], "formal_pre_delivery_gate")
        self.assertEqual(contract["project_sync"]["stage_requirements_semantics"], "exact_scope")
        self.assertEqual(contract["project_sync"]["implicit_phase_sync_semantics"], "status_minimum_only")
        self.assertTrue(contract["project_sync"]["formal_scope_requires_explicit_flag"])
        self.assertEqual(
            contract["project_sync"]["formal_state_requirements"],
            {
                "result_quality_status": "passed",
                "result_analysis_status": "passed",
                "downstream_artifacts_stale": False,
            },
        )
        self.assertEqual(set(contract["model_paper_framework"]["modes"]), {"compact", "full"})
        policy = contract["result_policy"]
        self.assertTrue(policy["primary_quality_gate_required"])
        self.assertTrue(policy["failed_quality_evidence_persisted"])
        self.assertTrue(policy["downstream_admission_requires_quality_passed"])
        self.assertEqual(set(policy["result_analysis_outcomes"]), {"passed", "failed", "redo_required"})
        self.assertTrue(policy["fixed_perturbation_forbidden"])
        self.assertEqual(
            set(contract["project_sync"]["artifact_hash_layers"]),
            {"data", "model", "solution_workbook", "result_analysis_workbook", "matlab_script", "figure_bundle", "framework"},
        )
        self.assertEqual(set(contract["per_question"]["mandatory_workbooks"]), {"solution", "result_analysis"})
        self.assertEqual(contract["writing_policy"]["default_mode"], "latex_first")
        self.assertEqual(contract["writing_policy"]["docx_mode"], "explicit_only_independent")
        self.assertFalse(contract["writing_policy"]["docx_is_latex_prerequisite"])


if __name__ == "__main__":
    unittest.main()
