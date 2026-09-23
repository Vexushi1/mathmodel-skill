from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml
import test_user_execution_contract as execution_fixtures

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


CODE = load_module("validate_code_delivery_v700", ROOT / "scripts/validate_code_delivery.py")


class V700TwoStageExecutionTests(unittest.TestCase):
    def add_q2(self, state: dict) -> None:
        state["subproblems"]["Q2"] = {
            "status": "designed", "selected_model": "m2", "capabilities": {},
            "result_quality_status": "pending", "result_analysis_status": "pending",
            "framework_section": "Q2", "result_summary_status": "pending",
        }

    def write_state(self, root: Path, state: dict) -> None:
        (root / "state").mkdir(parents=True, exist_ok=True)
        (root / "state/project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

    def read_state(self, root: Path) -> dict:
        return yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))

    def test_code_delivery_updates_only_target_question(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = execution_fixtures.UserExecutionContractTests()
            code = fixture.make_project(root)
            state = self.read_state(root)
            self.add_q2(state)
            self.write_state(root, state)
            issues, cfg = CODE.validate_script(root, code, "primary")
            self.assertEqual(issues, [])
            CODE.update_state(root, cfg, code)
            updated = self.read_state(root)
            self.assertEqual(updated["subproblems"]["Q1"]["primary_execution_status"], "awaiting_user_execution")
            self.assertNotIn("primary_execution_status", updated["subproblems"]["Q2"])
            self.assertNotIn("data_hash", updated["subproblems"]["Q2"])

    def test_analysis_change_invalidates_only_analysis_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = execution_fixtures.UserExecutionContractTests()
            primary = fixture.make_project(root)
            fixture.accept_primary(root, primary)
            fixture.activate_analysis(root)
            analysis = fixture.make_analysis_code(root)
            issues, cfg = CODE.validate_script(root, analysis, "analysis")
            self.assertEqual(issues, [])
            CODE.update_state(root, cfg, analysis)
            workbook = fixture.make_analysis_workbook(root, analysis)
            state = self.read_state(root)
            self.assertEqual(execution_fixtures.RECEIPT.validate_one(root, workbook, state, True), [])
            self.write_state(root, state)
            fixture.write_code(analysis, fixture.config("analysis", "问题一结果深化分析.xlsx"), marker=1)
            issues, cfg = CODE.validate_script(root, analysis, "analysis")
            self.assertEqual(issues, [])
            CODE.update_state(root, cfg, analysis)
            entry = self.read_state(root)["subproblems"]["Q1"]
            self.assertEqual(entry["result_quality_status"], "passed")
            self.assertEqual(entry["result_analysis_status"], "pending")
            self.assertIn("result_analysis_workbook", entry["stale_layers"])
            self.assertNotIn("solution_workbook", entry["stale_layers"])

    def test_primary_change_invalidates_primary_and_analysis_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = execution_fixtures.UserExecutionContractTests()
            primary = fixture.make_project(root)
            state = self.read_state(root)
            self.add_q2(state)
            self.write_state(root, state)
            fixture.accept_primary(root, primary)
            fixture.activate_analysis(root)
            analysis = fixture.make_analysis_code(root)
            issues, cfg = CODE.validate_script(root, analysis, "analysis")
            self.assertEqual(issues, [])
            CODE.update_state(root, cfg, analysis)
            workbook = fixture.make_analysis_workbook(root, analysis)
            state = self.read_state(root)
            self.assertEqual(execution_fixtures.RECEIPT.validate_one(root, workbook, state, True), [])
            state["project"]["current_phase"] = "solve_validate"
            self.write_state(root, state)
            fixture.write_code(primary, fixture.config("primary", "问题一求解结果.xlsx"), marker=1)
            issues, cfg = CODE.validate_script(root, primary, "primary")
            self.assertEqual(issues, [])
            CODE.update_state(root, cfg, primary)
            updated = self.read_state(root)
            entry = updated["subproblems"]["Q1"]
            self.assertEqual(entry["result_quality_status"], "pending")
            self.assertEqual(entry["result_analysis_status"], "pending")
            self.assertIn("solution_workbook", entry["stale_layers"])
            self.assertIn("result_analysis_workbook", entry["stale_layers"])
            self.assertNotIn("primary_execution_status", updated["subproblems"]["Q2"])

    def test_output_contract_uses_two_stage_python_files(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        per_question = contract["per_question"]
        self.assertEqual(
            per_question["python_scripts"],
            {"primary": "问题{中文序号}求解.py", "result_analysis": "问题{中文序号}结果深化分析.py"},
        )
        self.assertEqual(len(per_question["base_default_files"]), 3)
        self.assertEqual(len(per_question["analysis_required_additional_files"]), 2)
        self.assertIn("问题{中文序号}结果深化分析.py", per_question["analysis_required_additional_files"])
        self.assertNotIn("single_python_update_policy", per_question)

    def test_user_execution_contract_preserves_two_stage_scripts_and_conditional_preprocessing(self):
        contract = yaml.safe_load((ROOT / "core/user_execution_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(
            contract["code_delivery"]["stage_scripts"],
            {
                "primary": "问题X求解/问题X求解.py",
                "analysis": "问题X求解/问题X结果深化分析.py",
            },
        )
        self.assertEqual(
            contract["code_delivery"]["preprocessing_script"],
            "数据预处理/数据预处理.py",
        )
        self.assertEqual(
            contract["code_delivery"]["stage_activation"]["preprocessing"],
            "preprocessing_decision == project_level",
        )
        forbidden = contract["code_delivery"]["standalone_files_forbidden_by_default"]
        self.assertNotIn("问题X结果深化分析.py", forbidden)

    def test_analysis_script_matches_code_quality_contract(self):
        contract = yaml.safe_load((ROOT / "core/code_quality_contract.yaml").read_text(encoding="utf-8"))
        self.assertIn("问题X求解/问题X结果深化分析.py", contract["scope"])
        self.assertIn("数据预处理/数据预处理.py", contract["scope"])

    def test_stage_from_filename_rejects_nonstandard_names(self):
        problem = "问题一"
        with self.assertRaises(ValueError):
            CODE.stage_from_filename(Path("问题一求解/analysis.py"), problem)

    def test_state_records_separate_code_hash_fields(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        fields = schema["properties"]["subproblems"]["additionalProperties"]["properties"]
        self.assertIn("primary_code_sha256", fields)
        self.assertIn("analysis_code_sha256", fields)
        self.assertIn("result_analysis_code", fields)


if __name__ == "__main__":
    unittest.main()
