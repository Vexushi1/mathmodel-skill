from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


CODE = load_module("validate_code_delivery_v700", ROOT / "scripts/validate_code_delivery.py")


class V700TwoStageExecutionTests(unittest.TestCase):
    def config(self, problem: str, stage: str, workbook: str) -> dict:
        return {
            "execution_owner": "user",
            "execution_profile": "full_fidelity",
            "stage": stage,
            "problem_name": problem,
            "data_paths": ["data.csv"],
            "data_sha256": "a" * 64,
            "solver": "test",
            "solver_version": "1",
            "random_seed": 2026,
            "tolerance": 1e-8,
            "iteration_or_time_limit": "full",
            "expected_workbook": workbook,
            "allow_reduced_data": False,
            "allow_coarser_grid": False,
            "allow_shorter_horizon": False,
            "allow_fewer_repetitions": False,
            "allow_relaxed_tolerance": False,
            "allow_silent_solver_fallback": False,
        }

    def write_code(self, path: Path, cfg: dict, marker: int = 0) -> None:
        path.write_text(
            "FULL_FIDELITY_CONFIG = " + repr(cfg)
            + f"\n\ndef main():\n    return {marker}\n\nif __name__ == '__main__':\n    raise SystemExit(main())\n",
            encoding="utf-8",
        )

    def base_state(self) -> dict:
        return {
            "project": {"competition": "test", "problem": "A", "current_phase": "solve_validate"},
            "requirements": {"total": 0, "completed": [], "pending": []},
            "decisions": {},
            "subproblems": {
                "Q1": {
                    "status": "designed",
                    "selected_model": "m1",
                    "capabilities": {},
                    "result_quality_status": "pending",
                    "result_analysis_status": "pending",
                    "framework_section": "Q1",
                    "result_summary_status": "pending",
                },
                "Q2": {
                    "status": "designed",
                    "selected_model": "m2",
                    "capabilities": {},
                    "result_quality_status": "pending",
                    "result_analysis_status": "pending",
                    "framework_section": "Q2",
                    "result_summary_status": "pending",
                },
            },
            "variables": {"locked": [], "source": {}},
            "paper_framework": {
                "path": "模型论文框架.md",
                "version": "1",
                "sync_status": "stale",
                "last_sync_scope": "design",
                "proposition_limit": 4,
                "proposition_count": 0,
                "proposition_status": "not_assessed",
                "propositions": [],
            },
            "artifacts": {"code": [], "results": [], "figures": [], "papers": []},
            "risks": [],
            "next_gate": {"module": "solve_validate", "condition": "code"},
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
            state = self.base_state()
            state["preprocessing"] = {"decision": "not_needed"}
            self.write_state(root, state)
            folder = root / "问题一求解"
            folder.mkdir()
            code = folder / "问题一求解.py"
            self.write_code(code, self.config("问题一", "primary", "问题一求解结果.xlsx"))
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
            state = self.base_state()
            state["preprocessing"] = {"decision": "not_needed"}
            state["subproblems"]["Q1"].update({
                "status": "solved",
                "result_quality_status": "passed",
                "primary_execution_status": "accepted",
                "analysis_execution_status": "accepted",
                "result_analysis_status": "passed",
                "primary_code_sha256": "1" * 64,
                "analysis_code_sha256": "2" * 64,
            })
            self.write_state(root, state)
            folder = root / "问题一求解"
            folder.mkdir()
            analysis = folder / "问题一结果深化分析.py"
            self.write_code(analysis, self.config("问题一", "analysis", "问题一结果深化分析.xlsx"), marker=1)
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
            state = self.base_state()
            state["preprocessing"] = {"decision": "not_needed"}
            state["subproblems"]["Q1"].update({
                "status": "analyzed",
                "result_quality_status": "passed",
                "primary_execution_status": "accepted",
                "analysis_execution_status": "accepted",
                "result_analysis_status": "passed",
                "primary_code_sha256": "1" * 64,
                "analysis_code_sha256": "2" * 64,
            })
            self.write_state(root, state)
            folder = root / "问题一求解"
            folder.mkdir()
            primary = folder / "问题一求解.py"
            self.write_code(primary, self.config("问题一", "primary", "问题一求解结果.xlsx"), marker=1)
            state = self.read_state(root)
            state["project"]["current_phase"] = "solve_validate"
            self.write_state(root, state)
            issues, cfg = CODE.validate_script(root, primary, "primary")
            self.assertEqual(issues, [])
            CODE.update_state(root, cfg, primary)
            entry = self.read_state(root)["subproblems"]["Q1"]
            self.assertEqual(entry["result_quality_status"], "pending")
            self.assertEqual(entry["result_analysis_status"], "pending")
            self.assertIn("solution_workbook", entry["stale_layers"])
            self.assertIn("result_analysis_workbook", entry["stale_layers"])

    def test_output_contract_uses_two_stage_python_files(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        per_question = contract["per_question"]
        self.assertEqual(
            per_question["python_scripts"],
            {"primary": "问题{中文序号}求解.py", "result_analysis": "问题{中文序号}结果深化分析.py"},
        )
        self.assertEqual(len(per_question["exact_default_files"]), 5)
        self.assertIn("问题{中文序号}结果深化分析.py", per_question["exact_default_files"])
        self.assertNotIn("single_python_update_policy", per_question)

    def test_user_execution_contract_exposes_three_stage_scripts(self):
        contract = yaml.safe_load((ROOT / "core/user_execution_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(
            contract["code_delivery"]["stage_scripts"],
            {
                "preprocessing": "数据预处理/数据预处理.py",
                "primary": "问题X求解/问题X求解.py",
                "analysis": "问题X求解/问题X结果深化分析.py",
            },
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
