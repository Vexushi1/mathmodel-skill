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
        self.assertEqual(example["semantic_governance_version"], "1.0.0")

    def test_classification_has_single_capability_source_and_split_status(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        defs = schema["$defs"]
        self.assertEqual(schema["version"], "7.4.1")
        self.assertEqual(set(defs["classification"]["required"]), {"objective", "structures"})
        self.assertEqual(set(defs["dependency_kind"]["enum"]), {"data", "parameter", "model", "result"})
        self.assertEqual(set(defs["preprocessing_decision"]["enum"]), {"not_needed", "question_local", "project_level"})
        subproblems = schema["properties"]["subproblems"]
        sub_required = set(subproblems["additionalProperties"]["required"])
        self.assertEqual(subproblems["minProperties"], 1)
        for name in ("capabilities", "result_quality_status", "result_analysis_status"):
            self.assertIn(name, sub_required)
        fields = subproblems["additionalProperties"]["properties"]
        for name in (
            "code", "result_analysis_code", "primary_code_sha256", "analysis_code_sha256",
            "depends_on", "problem_contract_status", "semantic_closure_status",
            "complexity_sanity_status", "semantic_revision", "semantic_change_categories",
            "semantic_hash", "validated_semantic_hash",
        ):
            self.assertIn(name, fields)
        phases = set(schema["properties"]["project"]["properties"]["current_phase"]["enum"])
        statuses = set(subproblems["additionalProperties"]["properties"]["status"]["enum"])
        self.assertIn("data_preprocessing", phases)
        self.assertIn("result_analysis", phases)
        self.assertIn("analyzed", statuses)
        self.assertIn("result_analysis_workbook", defs["artifact_hashes"]["properties"])
        self.assertIn("preprocessing", schema["properties"])

    def test_workbook_schema_has_quality_gate_and_adaptive_analysis(self):
        schema = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8"))
        self.assertEqual(schema["schema_version"], "2.2.1")
        self.assertIn(">=6.3.2", schema["skill_compatibility"])
        self.assertIn("<8.0.0", schema["skill_compatibility"])
        self.assertEqual(schema["classification_contract"]["capabilities_source"], "subproblem.capabilities")
        runtime = schema["runtime_enforcement"]
        self.assertNotIn("artifact_checker", runtime)
        self.assertEqual(runtime["code_delivery_checker"], "scripts/validate_code_delivery.py")
        self.assertEqual(runtime["returned_workbook_checker"], "scripts/validate_user_execution.py")
        self.assertIn("objective_profiles", schema["solution_workbook"])
        self.assertIn("structure_profiles", schema["solution_workbook"])
        self.assertIn("主结果质量门", schema["solution_workbook"]["common_required_sheets"])
        self.assertIn("运行配置", schema["solution_workbook"]["common_required_sheets"])
        rules = "\n".join(runtime["rules"])
        self.assertIn("质量门允许记录未通过项", rules)
        self.assertIn("只有主结果质量门全部通过", rules)
        self.assertIn("不得进入下游", schema["solution_workbook"]["role"])
        analysis = schema["result_analysis_workbook"]
        self.assertEqual(set(analysis["common_required_sheets"]), {"运行配置", "分析设计", "结论稳定性汇总"})
        self.assertIn("算法一致性", analysis["required_any_sheets"])
        self.assertIn("结构稳健性", analysis["required_any_sheets"])
        self.assertNotIn("适用性说明", analysis["sheet_schemas"])
        self.assertEqual(schema["matlab_handoff"]["field_resolution"]["method"], "exact_header_unique_match")

    def test_output_contract_defines_split_result_policy(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(contract["version"], "7.4.1")
        self.assertEqual(contract["code_quality_contract"], "core/code_quality_contract.yaml")
        self.assertEqual(contract["preprocessing_contract"], "core/global_preprocessing_contract.yaml")
        self.assertEqual(contract["semantic_governance"]["script"], "scripts/validate_semantic_governance.py")
        self.assertEqual(contract["semantic_governance"]["dependency_kinds"], ["data", "parameter", "model", "result"])
        self.assertEqual(contract["project_sync"]["role"], "formal_pre_delivery_gate_after_semantic_governance")
        self.assertEqual(contract["project_sync"]["stage_requirements_semantics"], "exact_scope")
        self.assertEqual(
            contract["project_sync"]["conditional_stage_requirements_semantics"],
            "additive_when_condition_true_without_changing_base_exact_scope",
        )
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
            {
                "raw_data", "preprocessing_decision", "preprocessing_code", "preprocessing_workbook",
                "preprocessing_matlab_script", "model", "solution_workbook", "result_analysis_workbook",
                "matlab_script", "figure_bundle", "framework",
            },
        )
        conditional = contract["project_sync"]["conditional_stage_requirements"]
        self.assertEqual(
            conditional["preprocessing_decision_project_level"]["condition"],
            "preprocessing_decision == project_level",
        )
        self.assertIn("preprocessing_workbook", conditional["preprocessing_decision_project_level"]["results"])
        self.assertIn("preprocessing_matlab_script", conditional["preprocessing_decision_project_level"]["figures"])
        self.assertIn("preprocessing_matlab_script", conditional["preprocessing_decision_project_level"]["latex"])
        per_question = contract["per_question"]
        self.assertEqual(set(per_question["mandatory_workbooks"]), {"solution", "result_analysis"})
        self.assertEqual(per_question["question_directory"], "问题{中文序号}求解/")
        self.assertEqual(len(per_question["exact_default_files"]), 5)
        self.assertEqual(set(per_question["python_scripts"]), {"primary", "result_analysis"})
        self.assertNotIn("single_python_update_policy", per_question)
        self.assertTrue(per_question["no_auxiliary_files_by_default"])
        self.assertEqual(
            contract["global_preprocessing"]["exact_default_files"],
            ["数据预处理.py", "数据预处理结果.xlsx", "data_process.m"],
        )
        self.assertEqual(contract["writing_policy"]["default_mode"], "latex_first")
        self.assertEqual(contract["writing_policy"]["docx_mode"], "explicit_only_independent")
        self.assertFalse(contract["writing_policy"]["docx_is_latex_prerequisite"])


if __name__ == "__main__":
    unittest.main()
