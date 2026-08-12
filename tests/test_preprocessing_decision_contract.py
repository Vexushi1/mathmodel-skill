import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestPreprocessingDecisionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = yaml.safe_load(
            (ROOT / "core/global_preprocessing_contract.yaml").read_text(encoding="utf-8")
        )
        cls.router = yaml.safe_load(
            (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")
        )
        cls.manifest = yaml.safe_load(
            (ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8")
        )
        cls.output = yaml.safe_load(
            (ROOT / "core/output_contract.yaml").read_text(encoding="utf-8")
        )
        cls.state_schema = yaml.safe_load(
            (ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8")
        )
        cls.resolver = load_module("resolver_723", "scripts/resolve_workflow.py")
        cls.code_gate = load_module("code_gate_723", "scripts/validate_code_delivery.py")
        cls.execution_gate = load_module("execution_gate_723", "scripts/validate_user_execution.py")
        cls.sync = load_module("sync_723", "scripts/sync_project.py")

    def test_three_state_decision_is_authoritative(self):
        self.assertEqual(
            self.contract["decision_gate"]["decision_values"],
            ["not_needed", "question_local", "project_level"],
        )
        self.assertEqual(
            self.contract["decision_gate"]["level_values"],
            ["none", "structural", "transformative"],
        )

    def test_shared_data_is_not_sufficient_for_project_level(self):
        text = yaml.safe_dump(self.contract, allow_unicode=True)
        self.assertIn("两个及以上小问共享同一原始数据源", text)
        self.assertIn("never_sufficient_alone", self.contract["activation"])
        insufficient = self.contract["activation"]["never_sufficient_alone"]
        self.assertTrue(any("共享同一原始数据源" in item for item in insufficient))

    def test_generic_judgment_framework_covers_cross_competition_data_risks(self):
        audit = self.contract["judgment_framework"]["audit_dimensions"]
        for key in (
            "completeness",
            "consistency",
            "validity",
            "identity_and_duplicates",
            "sampling_and_coverage",
            "measurement_quality",
            "model_readiness",
            "temporal_causality_and_leakage",
            "target_and_label_integrity",
        ):
            self.assertIn(key, audit)
        principle = self.contract["judgment_framework"]["general_rules"]
        self.assertTrue(any("某一赛题" in item or "固定操作模板" in item for item in principle))

    def test_missing_values_do_not_imply_interpolation(self):
        policy = self.contract["missing_data_policy"]
        self.assertIn("不存在“有缺失就插值”的默认规则", policy["principle"])
        boundaries = policy["method_boundaries"]
        self.assertIn("interpolation", boundaries)
        self.assertIn("类别", boundaries["interpolation"])
        self.assertIn("predictive_imputation", boundaries)
        self.assertIn("人工掩蔽", boundaries["model_based_imputation"])

    def test_predictive_imputation_is_not_the_task_prediction_model(self):
        boundary = self.contract["prediction_boundary"]
        self.assertIn("只有前者可能属于预处理", boundary["principle"])
        self.assertTrue(any("赛题直接要求预测未来值" in item for item in boundary["not_preprocessing_when"]))
        self.assertTrue(any("缺测" in item for item in boundary["preprocessing_prediction_when"]))
        self.assertIn("不得以“数据预处理”的名义提前生成答案", boundary["rule"])

    def test_learned_preprocessing_requires_no_leakage_and_validation(self):
        rules = self.contract["operation_gate"]["rules"]
        self.assertTrue(any("训练/验证边界" in item for item in rules))
        quality = self.contract["workbook"]["quality_gate"]["checks"]
        self.assertTrue(any("人工掩蔽" in item or "留出样本" in item for item in quality))
        self.assertTrue(any("信息泄漏" in item for item in quality))

    def test_full_solution_does_not_unconditionally_load_preprocessing(self):
        route = self.router["routing"]["full_solution"]
        loaded = [*route.get("load", []), *route.get("then", [])]
        self.assertNotIn("modules/03_data_preprocessing.md", loaded)
        self.assertEqual(
            route["conditional_stage"]["when"],
            "preprocessing_decision == project_level",
        )
        self.assertIn("data_preprocessing", self.router["execution_contract"]["conditional_modules"])

    def test_manifest_makes_preprocessing_conditional(self):
        self.assertIn("data_preprocessing", self.manifest["conditional_modules"])
        pre = self.manifest["modules"]["data_preprocessing"]
        self.assertTrue(pre["conditional"])
        self.assertEqual(pre["activation"], "preprocessing_decision == project_level")
        self.assertNotIn(
            "preprocessing_workbook",
            self.manifest["modules"]["solve_validate"]["inputs"],
        )
        self.assertEqual(
            self.manifest["modules"]["solve_validate"]["conditional_inputs"]["preprocessing_workbook"]["when"],
            "preprocessing_decision == project_level",
        )

    def test_output_contract_requires_preprocessing_only_for_project_level(self):
        base_code = self.output["project_sync"]["stage_requirements"]["code"]
        self.assertNotIn("preprocessing_code", base_code)
        self.assertNotIn("preprocessing_workbook", base_code)
        conditional = self.output["project_sync"]["conditional_stage_requirements"]
        self.assertEqual(
            conditional["preprocessing_decision_project_level"]["condition"],
            "preprocessing_decision == project_level",
        )
        self.assertIn(
            "preprocessing_workbook",
            conditional["preprocessing_decision_project_level"]["results"],
        )

    def test_project_level_preprocessing_has_standard_data_process_matlab(self):
        directory = self.contract["project_directory"]
        self.assertEqual(directory["figure_stage_file"], "data_process.m")
        self.assertEqual(
            directory["final_default_files"],
            ["数据预处理.py", "数据预处理结果.xlsx", "data_process.m"],
        )
        visual = self.contract["visual_evidence"]
        self.assertEqual(visual["matlab_script"], "数据预处理/data_process.m")
        self.assertEqual(visual["data_source"], "数据预处理/数据预处理结果.xlsx")
        self.assertTrue(any("MATLAB只读取统一工作簿绘图" in item for item in visual["python_matlab_boundary"]))

    def test_data_process_is_figure_stage_not_solve_gate(self):
        conditional = self.output["project_sync"]["conditional_stage_requirements"]["preprocessing_decision_project_level"]
        self.assertNotIn("preprocessing_matlab_script", conditional["code"])
        self.assertNotIn("preprocessing_matlab_script", conditional["results"])
        self.assertIn("preprocessing_matlab_script", conditional["figures"])
        figure_module = self.manifest["modules"]["figure_evidence"]
        self.assertEqual(
            figure_module["conditional_outputs"]["preprocessing_matlab_script"]["when"],
            "preprocessing_decision == project_level",
        )

    def test_data_process_cannot_recompute_preprocessing(self):
        visual = self.contract["visual_evidence"]
        boundary = "\n".join(visual["python_matlab_boundary"])
        self.assertIn("不重新插值", boundary)
        self.assertIn("不重新", boundary)
        module_text = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        self.assertIn("data_process.m", module_text)
        self.assertIn("重新插值", module_text)
        self.assertIn("只读取 `数据预处理结果.xlsx`", module_text)

    def test_resolver_skips_preprocessing_for_clean_shared_data_decision(self):
        plan = self.resolver.resolve_workflow(
            "full_solution",
            objective="optimization",
            preprocessing_decision="not_needed",
        )
        self.assertNotIn("modules/03_data_preprocessing.md", plan["modules"])
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertIn("python_code", plan["terminal_outputs"])
        self.assertEqual(plan["preprocessing_decision"], "not_needed")

    def test_resolver_pauses_at_project_level_preprocessing(self):
        plan = self.resolver.resolve_workflow(
            "full_solution",
            objective="optimization",
            preprocessing_decision="project_level",
            available_artifacts=[],
        )
        self.assertIn("modules/03_data_preprocessing.md", plan["modules"])
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        self.assertIn("preprocessing_code", plan["terminal_outputs"])
        self.assertIn("awaiting_user_preprocessing", plan["terminal_outputs"])
        self.assertTrue(plan["pause_for_user_execution"])

    def test_resolver_continues_after_project_level_workbook_is_accepted(self):
        plan = self.resolver.resolve_workflow(
            "full_solution",
            objective="optimization",
            preprocessing_decision="project_level",
            available_artifacts=["accepted_preprocessing_workbook"],
        )
        self.assertNotIn("modules/03_data_preprocessing.md", plan["modules"])
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertIn("python_code", plan["terminal_outputs"])

    def test_state_schema_supports_conditional_preprocessing_phase(self):
        phases = self.state_schema["properties"]["project"]["properties"]["current_phase"]["enum"]
        self.assertIn("data_preprocessing", phases)
        decisions = self.state_schema["$defs"]["preprocessing_decision"]["enum"]
        self.assertEqual(decisions, ["not_needed", "question_local", "project_level"])
        self.assertIn("preprocessing", self.state_schema["properties"])

    def test_seismic_operations_are_conditional_domain_example_not_default(self):
        seismic = self.contract["seismic_guidance"]
        self.assertIn("领域专项示例", seismic["role"])
        self.assertIn("不得反向成为其他赛题的默认预处理模板", seismic["role"])
        self.assertIn("先审计后处理", seismic["principle"])
        self.assertIn("默认带通滤波", seismic["forbidden_defaults"])
        self.assertIn("默认插值坏道", seismic["forbidden_defaults"])
        self.assertIn("带通滤波", seismic["optional_operations"])
        self.assertIn("仅在", seismic["optional_operations"]["带通滤波"])

    def test_code_delivery_recognizes_preprocessing_stage(self):
        problem, stage = self.code_gate.script_identity(
            Path("项目") / "数据预处理" / "数据预处理.py"
        )
        self.assertEqual((problem, stage), ("数据预处理", "preprocessing"))

    def test_returned_workbook_recognizes_preprocessing_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            workbook = root / "数据预处理" / "数据预处理结果.xlsx"
            problem, stage, issues = self.execution_gate.workbook_identity(root, workbook)
        self.assertEqual((problem, stage), ("数据预处理", "preprocessing"))
        self.assertEqual(issues, [])

    def test_sync_stage_requirements_follow_decision(self):
        raw_state = {"preprocessing": {"decision": "not_needed"}}
        project_state = {"preprocessing": {"decision": "project_level"}}
        raw_required = self.sync.stage_requirements("figures", self.output, raw_state)
        project_required = self.sync.stage_requirements("figures", self.output, project_state)
        self.assertNotIn("preprocessing_workbook", raw_required)
        self.assertNotIn("preprocessing_matlab_script", raw_required)
        self.assertIn("preprocessing_workbook", project_required)
        self.assertIn("preprocessing_matlab_script", project_required)


if __name__ == "__main__":
    unittest.main()
