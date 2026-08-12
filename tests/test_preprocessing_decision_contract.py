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
        cls.resolver = load_module("resolver_721", "scripts/resolve_workflow.py")
        cls.code_gate = load_module("code_gate_721", "scripts/validate_code_delivery.py")
        cls.execution_gate = load_module("execution_gate_721", "scripts/validate_user_execution.py")
        cls.sync = load_module("sync_721", "scripts/sync_project.py")

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

    def test_seismic_operations_are_conditional_not_default(self):
        seismic = self.contract["seismic_guidance"]
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
        raw_required = self.sync.stage_requirements("results", self.output, raw_state)
        project_required = self.sync.stage_requirements("results", self.output, project_state)
        self.assertNotIn("preprocessing_workbook", raw_required)
        self.assertIn("preprocessing_workbook", project_required)


if __name__ == "__main__":
    unittest.main()
